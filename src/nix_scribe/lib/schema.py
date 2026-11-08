from __future__ import annotations

import copy
from dataclasses import MISSING, Field, dataclass, field, fields
from typing import Any, ClassVar, dataclass_transform

from nix_scribe.arguments import args
from nix_scribe.lib.asset import Asset
from nix_scribe.lib.option_block import NixFragment, NixValue, combined_comments


@dataclass(frozen=True, slots=True)
class OptionMetadata:
    path: str | None = None
    comment: str | None = None
    claims: set[str] = field(default_factory=set)
    arguments: set[str] = field(default_factory=set)
    root: bool = False
    inline: bool = False
    explicit_default: bool = False
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
    """Declares a ModuleSchema field with NixOS option metadata.

    Args:
        path: NixOS option path override. Defaults to field name.
        default: Static default value. When omitted, field defaults to None.
        default_factory: Zero-argument callable producing field default value.
        comment: Static comment rendered above the option in the generated Nix file.
        claims: Package attribute names claimed when this option is active.
        arguments: Nix function arguments (e.g. 'pkgs') required when this option is active.
        root: Emits option at top level instead of under the schema prefix.
        inline: Inlines dictionary fields directly under the parent prefix.
        omit_default: Whether to omit the field when its value matches default.
    """
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


@dataclass_transform(field_specifiers=(option, field))
class ModuleSchema:
    """Recursive declarative schema mapping host state to NixOS module options."""

    claims: ClassVar[set[str]] = set()
    arguments: ClassVar[set[str]] = set()
    prefix: ClassVar[str | None] = None

    def __init_subclass__(
        cls,
        *,
        claims: set[str] | None = None,
        arguments: set[str] | None = None,
        prefix: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init_subclass__(**kwargs)
        if claims is not None:
            cls.claims = set(cls.claims) | set(claims)
        if arguments is not None:
            cls.arguments = set(cls.arguments) | set(arguments)
        if prefix is not None:
            cls.prefix = prefix
        if "__dataclass_fields__" not in cls.__dict__:
            dataclass(cls)

    def add_asset(self, asset: Asset) -> None:
        """Registers a file asset with this schema."""
        assets: set[Asset] | None = getattr(self, "_registered_assets", None)
        if assets is None:
            assets = set()
            object.__setattr__(self, "_registered_assets", assets)
        assets.add(asset)

    def add_argument(self, *args: str) -> None:
        """Registers Nix function arguments (e.g. 'pkgs', 'lib') required by this schema."""
        extra: set[str] | None = getattr(self, "_extra_arguments", None)
        if extra is None:
            extra = set()
            object.__setattr__(self, "_extra_arguments", extra)
        extra.update(args)

    def claim(self, *packages: str) -> None:
        """Registers additional runtime package claims on this schema instance."""
        extra: set[str] | None = getattr(self, "_extra_claims", None)
        if extra is None:
            extra = set()
            object.__setattr__(self, "_extra_claims", extra)
        extra.update(packages)

    @staticmethod
    def _should_omit(f: Field[Any], val: Any, omit_defaults: bool = True) -> bool:
        """Determines whether a schema field should be omitted from output.

        None and empty collections are always omitted unless explicitly requested.
        When omit_defaults is True, fields matching their declared default are omitted.
        """
        if val is None:
            return True

        meta = get_option_metadata(f)
        if not meta.omit_default:
            return False

        if not omit_defaults:
            return False

        if isinstance(val, (list, dict, set)) and len(val) == 0:
            return True

        if meta.explicit_default:
            default_val = (
                f.default
                if f.default is not MISSING
                else (
                    f.default_factory() if f.default_factory is not MISSING else MISSING
                )
            )
            if (
                default_val is not MISSING
                and (isinstance(val, bool) == isinstance(default_val, bool))
                and val == default_val
            ):
                return True
            return False

        if f.default is not MISSING:
            if isinstance(f.default, bool):
                if val is False:
                    return True
                return False
            if (
                isinstance(val, bool) == isinstance(f.default, bool)
            ) and val == f.default:
                return True

        return False

    def _collect_subschemas(self, val: Any) -> list[ModuleSchema]:
        """Recursively extracts all active child ModuleSchema instances from an option value."""
        if isinstance(val, NixValue):
            return self._collect_subschemas(val.value)
        if isinstance(val, ModuleSchema):
            return [val]
        if isinstance(val, dict):
            subschemas: list[ModuleSchema] = []
            for v in val.values():
                subschemas.extend(self._collect_subschemas(v))
            return subschemas
        if isinstance(val, (list, tuple, set)):
            subschemas = []
            for item in val:
                subschemas.extend(self._collect_subschemas(item))
            return subschemas
        return []

    def resolve_claims(self, omit_defaults: bool | None = None) -> set[str]:
        """Recursively resolves active package claims from self and active sub-schemas."""
        effective_omit = (
            not getattr(args, "keep_defaults", False)
            if omit_defaults is None
            else omit_defaults
        )
        active_claims: set[str] = set(self.claims)
        extra: set[str] | None = getattr(self, "_extra_claims", None)
        if extra:
            active_claims.update(extra)

        for f in fields(self):
            raw_val = getattr(self, f.name)
            val = raw_val.value if isinstance(raw_val, NixValue) else raw_val
            if self._should_omit(f, val, omit_defaults=effective_omit):
                continue

            meta = get_option_metadata(f)
            if meta.claims:
                active_claims.update(meta.claims)

            for sub in self._collect_subschemas(val):
                active_claims.update(sub.resolve_claims(omit_defaults=effective_omit))

        return active_claims

    def resolve_arguments(self, omit_defaults: bool | None = None) -> set[str]:
        """Recursively resolves required Nix function arguments from self and active sub-schemas."""
        effective_omit = (
            not getattr(args, "keep_defaults", False)
            if omit_defaults is None
            else omit_defaults
        )
        active_args: set[str] = set(self.arguments)
        extra: set[str] | None = getattr(self, "_extra_arguments", None)
        if extra:
            active_args.update(extra)

        for f in fields(self):
            raw_val = getattr(self, f.name)
            val = raw_val.value if isinstance(raw_val, NixValue) else raw_val
            if self._should_omit(f, val, omit_defaults=effective_omit):
                continue

            meta = get_option_metadata(f)
            if meta.arguments:
                active_args.update(meta.arguments)

            for sub in self._collect_subschemas(val):
                active_args.update(sub.resolve_arguments(omit_defaults=effective_omit))

        return active_args

    def resolve_assets(self, omit_defaults: bool | None = None) -> set[Asset]:
        """Recursively collects explicitly registered assets from self and active sub-schemas."""
        effective_omit = (
            not getattr(args, "keep_defaults", False)
            if omit_defaults is None
            else omit_defaults
        )
        collected: set[Asset] = set(getattr(self, "_registered_assets", set()))
        for f in fields(self):
            raw_val = getattr(self, f.name)
            val = raw_val.value if isinstance(raw_val, NixValue) else raw_val
            if self._should_omit(f, val, omit_defaults=effective_omit):
                continue
            for sub in self._collect_subschemas(val):
                collected.update(sub.resolve_assets(omit_defaults=effective_omit))
        return collected

    def _serialize_value(
        self,
        val: Any,
        preserve_comments: bool,
        omit_defaults: bool = True,
        root_opts: dict[str, Any] | None = None,
    ) -> Any:
        """Serializes a schema option value recursively, handling NixValue wrappers and collections."""
        if isinstance(val, NixValue):
            inner = self._serialize_value(
                val.value,
                preserve_comments,
                omit_defaults,
                root_opts=root_opts,
            )
            if inner is None or (isinstance(inner, dict) and not inner):
                return None
            if preserve_comments and val.comment:
                return NixValue(value=inner, comment=val.comment)
            return inner

        if isinstance(val, ModuleSchema):
            scoped, child_root = val._serialize_fields(
                preserve_comments=preserve_comments, omit_defaults=omit_defaults
            )
            if root_opts is not None:
                root_opts.update(child_root)
            return scoped if scoped else None

        if isinstance(val, dict):
            out: dict[str, Any] = {}
            for k, v in val.items():
                serialized_v = self._serialize_value(
                    v,
                    preserve_comments,
                    omit_defaults,
                    root_opts=root_opts,
                )
                if serialized_v is not None:
                    out[k] = serialized_v
            return out

        if isinstance(val, (list, tuple, set)):
            out_list: list[Any] = []
            for item in val:
                serialized_item = self._serialize_value(
                    item,
                    preserve_comments,
                    omit_defaults,
                    root_opts=root_opts,
                )
                if serialized_item is not None:
                    out_list.append(serialized_item)
            return out_list

        return val

    def _serialize_fields(
        self,
        preserve_comments: bool = True,
        omit_defaults: bool | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Serializes fields of this schema into scoped options and cross-cutting root options."""
        effective_omit = (
            not getattr(args, "keep_defaults", False)
            if omit_defaults is None
            else omit_defaults
        )
        scoped: dict[str, Any] = {}
        root_opts: dict[str, Any] = {}

        for f in fields(self):
            raw_val = getattr(self, f.name)
            dyn_comment = raw_val.comment if isinstance(raw_val, NixValue) else None
            val = raw_val.value if isinstance(raw_val, NixValue) else raw_val

            if self._should_omit(f, val, omit_defaults=effective_omit):
                continue

            if isinstance(val, ModuleSchema):
                child_scoped, child_root = val._serialize_fields(
                    preserve_comments=preserve_comments,
                    omit_defaults=effective_omit,
                )
                root_opts.update(child_root)
                if not child_scoped:
                    continue
                serialized_val: Any = child_scoped
            else:
                serialized_val = self._serialize_value(
                    val,
                    preserve_comments,
                    omit_defaults=effective_omit,
                    root_opts=root_opts,
                )
                if serialized_val is None or (
                    isinstance(serialized_val, (dict, list)) and not serialized_val
                ):
                    continue

            meta = get_option_metadata(f)
            merged_comment = combined_comments(meta.comment, dyn_comment)
            if preserve_comments and merged_comment:
                serialized_val = NixValue(value=serialized_val, comment=merged_comment)

            nix_path: str = meta.path if meta.path is not None else f.name
            is_root: bool = meta.root
            is_inline: bool = meta.inline or nix_path == ""

            target = root_opts if is_root else scoped
            if is_inline:
                raw_dict = (
                    serialized_val.value
                    if isinstance(serialized_val, NixValue)
                    else serialized_val
                )
                if isinstance(raw_dict, dict):
                    target.update(raw_dict)
            else:
                target[nix_path] = serialized_val

        return scoped, root_opts

    def to_dict(self, omit_defaults: bool | None = None) -> dict[str, Any]:
        """Serializes active schema options into a plain dictionary without NixValue wrappers."""
        scoped, root_opts = self._serialize_fields(
            preserve_comments=False, omit_defaults=omit_defaults
        )
        if root_opts:
            return {**scoped, **root_opts}
        return scoped

    def to_nix_fragment(
        self,
        name: str = "",
        description: str = "",
        prefix: str | None = None,
        omit_defaults: bool | None = None,
    ) -> NixFragment:
        """Compiles this ModuleSchema into a NixFragment for rendering."""
        scoped, root_opts = self._serialize_fields(
            preserve_comments=True, omit_defaults=omit_defaults
        )
        effective_prefix = self.prefix if self.prefix is not None else (prefix or "")

        data: dict[str, Any] = {}
        if scoped:
            if effective_prefix:
                data[effective_prefix] = scoped
            else:
                data.update(scoped)

        if root_opts:
            data.update(root_opts)

        fragment_name = name or (
            effective_prefix.split(".")[-1]
            if effective_prefix
            else self.__class__.__name__
        )

        options: dict[str, NixValue] = {
            k: v if isinstance(v, NixValue) else NixValue(value=v)
            for k, v in data.items()
        }

        return NixFragment(
            name=fragment_name,
            description=description,
            options=options,
            arguments=self.resolve_arguments(omit_defaults=omit_defaults),
        )
