from __future__ import annotations

import importlib
import importlib.util
import inspect
import types
import typing
from collections.abc import Sequence
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Union, get_args, get_origin

from nix_scribe.lib.nix_module import NixModule, get_option_metadata


@dataclass(frozen=True)
class ContractSpec:
    """Static metadata extracted from a NixModule contract class."""

    module_class: type[NixModule]
    prefix: str | None
    option_paths: list[str]
    package_claims: set[str]


def _unwrap_optional(ann: Any) -> Any:
    """Unwraps Optional[T] / T | None to T when possible."""
    origin = get_origin(ann)
    if origin is Union or origin is types.UnionType:
        non_none = [arg for arg in get_args(ann) if arg is not type(None)]
        if len(non_none) == 1:
            return non_none[0]
    return ann


def _get_resolved_annotations(cls: type[Any]) -> dict[str, Any]:
    """Resolves type annotations for a class, falling back to raw annotations on failure."""
    try:
        return typing.get_type_hints(cls)
    except Exception:
        return inspect.get_annotations(cls, eval_str=False)


def _collect_contract_details(
    mod_cls: type[NixModule],
    current_prefix: str,
    option_paths: list[str],
    package_claims: set[str],
) -> None:
    package_claims.update(mod_cls._declared_claims)
    annotations = _get_resolved_annotations(mod_cls)

    for f in fields(typing.cast(Any, mod_cls)):
        meta = get_option_metadata(f)
        if meta.claims:
            package_claims.update(meta.claims)

        nix_path = meta.path if meta.path is not None else f.name
        if meta.root:
            full_path = nix_path
        elif meta.inline or nix_path == "":
            full_path = current_prefix
        elif current_prefix:
            full_path = f"{current_prefix}.{nix_path}"
        else:
            full_path = nix_path

        ann = _unwrap_optional(annotations.get(f.name))
        origin = get_origin(ann)
        args = get_args(ann)

        if isinstance(ann, type) and issubclass(ann, NixModule):
            _collect_contract_details(ann, full_path, option_paths, package_claims)
        elif (
            origin is dict
            and len(args) == 2
            and isinstance(sub_cls := _unwrap_optional(args[1]), type)
            and issubclass(sub_cls, NixModule)
        ):
            wildcard_prefix = f"{full_path}.<name>" if full_path else "<name>"
            _collect_contract_details(
                sub_cls, wildcard_prefix, option_paths, package_claims
            )
        elif (
            origin in (list, set, tuple)
            and args
            and isinstance(sub_cls := _unwrap_optional(args[0]), type)
            and issubclass(sub_cls, NixModule)
        ):
            wildcard_prefix = f"{full_path}.*" if full_path else "*"
            _collect_contract_details(
                sub_cls, wildcard_prefix, option_paths, package_claims
            )
        elif full_path:
            option_paths.append(full_path)


def inspect_contract(cls: type[NixModule]) -> ContractSpec:
    """Extracts declared NixOS option paths and package claims from a NixModule class."""
    option_paths: list[str] = []
    package_claims: set[str] = set()
    prefix = cls.prefix or ""
    _collect_contract_details(cls, prefix, option_paths, package_claims)
    return ContractSpec(
        module_class=cls,
        prefix=cls.prefix,
        option_paths=option_paths,
        package_claims=package_claims,
    )


def discover_contracts(
    package_name: str = "nix_scribe.modules.nixos",
    *,
    paths: Sequence[Path | str] | None = None,
) -> list[type[NixModule]]:
    """Discovers root NixModule contract classes in the given package or specific files."""
    spec = importlib.util.find_spec(package_name)
    if not spec or not spec.submodule_search_locations:
        raise ImportError(f"Could not find package {package_name}")
    package_path = Path(spec.submodule_search_locations[0]).resolve()

    if paths is not None:
        target_files = [Path(p).resolve() for p in paths]
    else:
        target_files = sorted(package_path.rglob("*.py"))

    discovered: dict[str, type[NixModule]] = {}
    for py_file in target_files:
        if (
            py_file.name == "__init__.py"
            or "__pycache__" in py_file.parts
            or not py_file.is_file()
        ):
            continue
        rel_parts = py_file.relative_to(package_path).with_suffix("").parts
        module_name = f"{package_name}.{'.'.join(rel_parts)}"
        mod = importlib.import_module(module_name)
        for obj in vars(mod).values():
            if (
                isinstance(obj, type)
                and issubclass(obj, NixModule)
                and obj is not NixModule
                and obj.prefix is not None
                and obj.__module__ == mod.__name__
            ):
                discovered[f"{obj.__module__}.{obj.__name__}"] = obj

    return [discovered[k] for k in sorted(discovered)]
