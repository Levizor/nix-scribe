from __future__ import annotations

import copy
from dataclasses import MISSING, Field, dataclass, field, fields
from typing import TYPE_CHECKING, Any, ClassVar, cast, dataclass_transform

from nix_scribe.lib.asset import Asset
from nix_scribe.lib.nix_fragment import NixValue

if TYPE_CHECKING:
    from nix_scribe.lib.nix_fragment import NixFragment


@dataclass(frozen=True, slots=True)
class OptionMetadata:
    # NixOS option path override. Defaults to field name.
    path: str | None = None
    # Static comment rendered above the option in the generated Nix file.
    comment: str | None = None
    # Package attribute names claimed when this option is active.
    claims: set[str] = field(default_factory=set)
    # Nix function arguments (e.g. 'pkgs') required when this option is active.
    arguments: set[str] = field(default_factory=set)
    # Emits option at top level instead of under the schema prefix.
    root: bool = False
    # Inlines dictionary fields directly under the parent prefix.
    inline: bool = False
    # Whether an explicit default or default_factory was configured.
    explicit_default: bool = False
    # Whether to omit the field when its value matches default.
    omit_default: bool = True


_DEFAULT_OPTION_METADATA = OptionMetadata()


def get_option_metadata(f: Field[Any]) -> OptionMetadata:
    """Retrieves OptionMetadata from a dataclass field, falling back to defaults."""
    return f.metadata.get("nix_option", _DEFAULT_OPTION_METADATA)


def option(
    path: str | None = None,
    *,
    default: Any = MISSING,
    default_factory: Any = MISSING,
    comment: str | None = None,
    claims: set[str] | None = None,
    arguments: set[str] | None = None,
    root: bool = False,
    inline: bool = False,
    omit_default: bool = True,
    **kwargs: Any,
) -> Any:
    """Declares a NixModule field with Nix option metadata."""
    metadata = dict(kwargs.pop("metadata", {}))
    has_explicit_default = default is not MISSING or default_factory is not MISSING
    metadata["nix_option"] = OptionMetadata(
        path=path,
        comment=comment,
        claims=set(claims) if claims else set(),
        arguments=set(arguments) if arguments else set(),
        root=root,
        inline=inline,
        explicit_default=has_explicit_default,
        omit_default=omit_default,
    )

    if default_factory is not MISSING:
        return field(default_factory=default_factory, metadata=metadata, **kwargs)
    if default is not MISSING:
        if isinstance(default, (list, dict, set)):
            if not default:
                return field(
                    default_factory=type(default),
                    metadata=metadata,
                    **kwargs,
                )
            initial_val = default
            return field(
                default_factory=lambda: copy.deepcopy(initial_val),
                metadata=metadata,
                **kwargs,
            )
        return field(default=default, metadata=metadata, **kwargs)
    return field(default=None, metadata=metadata, **kwargs)


def _collect_submodules(val: Any) -> list[NixModule]:
    """Recursively extracts all active child NixModule instances from an option value."""
    if isinstance(val, NixValue):
        return _collect_submodules(val.value)
    if isinstance(val, NixModule):
        return [val]
    if isinstance(val, dict):
        submodules = []
        for v in val.values():
            submodules.extend(_collect_submodules(v))
        return submodules
    if isinstance(val, (list, tuple, set)):
        submodules = []
        for item in val:
            submodules.extend(_collect_submodules(item))
        return submodules
    return []


@dataclass_transform(field_specifiers=(option, field))
class NixModule:
    """Recursive declarative schema mapping host state to Nix module options."""

    _declared_claims: ClassVar[frozenset[str]] = frozenset()
    _declared_arguments: ClassVar[frozenset[str]] = frozenset()
    prefix: ClassVar[str | None] = None

    def __init_subclass__(
        cls,
        *,
        claims: set[str] | frozenset[str] | None = None,
        arguments: set[str] | frozenset[str] | None = None,
        prefix: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init_subclass__(**kwargs)
        if claims is not None:
            cls._declared_claims = frozenset(cls._declared_claims) | frozenset(claims)
        if arguments is not None:
            cls._declared_arguments = frozenset(cls._declared_arguments) | frozenset(
                arguments
            )
        if prefix is not None:
            cls.prefix = prefix
        has_explicit_doc = bool(cls.__dict__.get("__doc__"))
        if "__dataclass_fields__" not in cls.__dict__:
            dataclass(cls)
        if not has_explicit_doc:
            cls.__doc__ = None

    @property
    def _fields(self) -> tuple[Field[Any], ...]:
        """Returns the dataclass fields of this module instance."""
        return fields(cast(Any, self))

    def add_asset(self, asset: Asset) -> None:
        """Registers a file asset with this module."""
        assets: set[Asset] | None = getattr(self, "_registered_assets", None)
        if assets is None:
            assets = set()
            object.__setattr__(self, "_registered_assets", assets)
        assets.add(asset)

    def add_argument(self, *args: str) -> None:
        """Registers Nix function arguments (e.g. 'pkgs', 'lib') required by this module."""
        extra: set[str] | None = getattr(self, "_extra_arguments", None)
        if extra is None:
            extra = set()
            object.__setattr__(self, "_extra_arguments", extra)
        extra.update(args)

    def claim(self, *packages: str) -> None:
        """Registers additional runtime package claims on this module instance."""
        extra: set[str] | None = getattr(self, "_extra_claims", None)
        if extra is None:
            extra = set()
            object.__setattr__(self, "_extra_claims", extra)
        extra.update(packages)

    def resolve_claims(self) -> set[str]:
        """Recursively resolves active package claims from self and active submodules."""
        active_claims: set[str] = set(self._declared_claims)
        extra: set[str] | None = getattr(self, "_extra_claims", None)
        if extra:
            active_claims.update(extra)

        for f in self._fields:
            raw_val = getattr(self, f.name)
            val = raw_val.value if isinstance(raw_val, NixValue) else raw_val
            if not val:
                continue

            meta = get_option_metadata(f)
            if meta.claims:
                active_claims.update(meta.claims)

            for sub in _collect_submodules(val):
                active_claims.update(sub.resolve_claims())

        return active_claims

    def resolve_assets(self) -> set[Asset]:
        """Recursively collects explicitly registered assets from self and active submodules."""
        collected: set[Asset] = set(getattr(self, "_registered_assets", set()))
        for f in self._fields:
            raw_val = getattr(self, f.name)
            val = raw_val.value if isinstance(raw_val, NixValue) else raw_val
            if isinstance(val, Asset):
                collected.add(val)
            for sub in _collect_submodules(val):
                collected.update(sub.resolve_assets())
        return collected

    def to_dict(
        self,
        keep_defaults: bool = False,
    ) -> dict[str, Any]:
        """Serializes active module options into a plain dictionary without NixValue wrappers."""
        from nix_scribe.lib.emitter import emit_dict

        return emit_dict(cast(Any, self), keep_defaults=keep_defaults)

    def to_nix_fragment(
        self,
        name: str = "",
        description: str = "",
        prefix: str | None = None,
        keep_defaults: bool = False,
    ) -> NixFragment:
        """Compiles this NixModule into a NixFragment for layout rendering."""
        from nix_scribe.lib.emitter import emit_nix_fragment

        return emit_nix_fragment(
            cast(Any, self),
            name=name,
            description=description,
            prefix=prefix,
            keep_defaults=keep_defaults,
        )
