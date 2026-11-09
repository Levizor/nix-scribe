from __future__ import annotations

from dataclasses import MISSING, Field
from typing import Any

from nix_scribe.lib.nix_module import (
    NixModule,
    get_option_metadata,
)
from nix_scribe.lib.option_block import NixFragment, NixValue, combined_comments


def should_omit(f: Field[Any], val: Any, keep_defaults: bool = False) -> bool:
    """Determines whether a module field should be omitted from output.

    None and empty collections are always omitted unless explicitly requested.
    When keep_defaults is False, fields matching their declared default are omitted.
    """
    if val is None:
        return True

    meta = get_option_metadata(f)
    if not meta.omit_default:
        return False

    if keep_defaults:
        return False

    if isinstance(val, (list, dict, set)) and len(val) == 0:
        return True

    default_val = (
        f.default
        if f.default is not MISSING
        else (f.default_factory() if f.default_factory is not MISSING else MISSING)
    )
    if default_val is not MISSING:
        # Guard against Python treating bool as an int subclass where 0 == False and 1 == True
        if (
            isinstance(val, bool) == isinstance(default_val, bool)
        ) and val == default_val:
            return True

    return False


def _serialize_value(
    val: Any,
    preserve_comments: bool,
    keep_defaults: bool = False,
    root_opts: dict[str, Any] | None = None,
    collected_args: set[str] | None = None,
) -> Any:
    """Serializes a module option value recursively, handling NixValue wrappers and collections."""
    if isinstance(val, NixValue):
        inner = _serialize_value(
            val.value,
            preserve_comments,
            keep_defaults,
            root_opts=root_opts,
            collected_args=collected_args,
        )
        if inner is None or (isinstance(inner, dict) and not inner):
            return None
        if preserve_comments and val.comment:
            return NixValue(value=inner, comment=val.comment)
        return inner

    if isinstance(val, NixModule):
        scoped, child_root, child_args = _serialize_fields(
            val,
            preserve_comments=preserve_comments,
            keep_defaults=keep_defaults,
        )
        if root_opts is not None:
            root_opts.update(child_root)
        if collected_args is not None:
            collected_args.update(child_args)
        return scoped if scoped else None

    if isinstance(val, dict):
        return {
            k: s
            for k, v in val.items()
            if (
                s := _serialize_value(
                    v,
                    preserve_comments,
                    keep_defaults,
                    root_opts=root_opts,
                    collected_args=collected_args,
                )
            )
            is not None
        }

    if isinstance(val, (list, tuple, set)):
        return [
            s
            for item in val
            if (
                s := _serialize_value(
                    item,
                    preserve_comments,
                    keep_defaults,
                    root_opts=root_opts,
                    collected_args=collected_args,
                )
            )
            is not None
        ]

    return val


def _serialize_fields(
    module: NixModule,
    preserve_comments: bool = True,
    keep_defaults: bool = False,
) -> tuple[dict[str, Any], dict[str, Any], set[str]]:
    """Serializes fields of a module into scoped options, root options, and active arguments."""
    scoped: dict[str, Any] = {}
    root_opts: dict[str, Any] = {}
    active_args: set[str] = set(module._declared_arguments) | set(
        getattr(module, "_extra_arguments", ())
    )

    for f in module._fields:
        raw_val = getattr(module, f.name)
        dyn_comment, val = (
            (raw_val.comment, raw_val.value)
            if isinstance(raw_val, NixValue)
            else (None, raw_val)
        )

        if should_omit(f, val, keep_defaults=keep_defaults):
            continue

        serialized_val = _serialize_value(
            val,
            preserve_comments=preserve_comments,
            keep_defaults=keep_defaults,
            root_opts=root_opts,
            collected_args=active_args,
        )
        if serialized_val is None or (
            isinstance(serialized_val, (dict, list)) and not serialized_val
        ):
            continue

        meta = get_option_metadata(f)
        if meta.arguments:
            active_args.update(meta.arguments)

        merged_comment = combined_comments(meta.comment, dyn_comment)
        if preserve_comments and merged_comment:
            serialized_val = NixValue(value=serialized_val, comment=merged_comment)

        nix_path: str = meta.path if meta.path is not None else f.name
        is_inline: bool = meta.inline or nix_path == ""

        target = root_opts if meta.root else scoped
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

    return scoped, root_opts, active_args


def emit_dict(module: NixModule, keep_defaults: bool = False) -> dict[str, Any]:
    """Serializes active module options into a plain dictionary without NixValue wrappers."""
    scoped, root_opts, _ = _serialize_fields(
        module, preserve_comments=False, keep_defaults=keep_defaults
    )
    if root_opts:
        return {**scoped, **root_opts}
    return scoped


def emit_nix_fragment(
    module: NixModule,
    name: str = "",
    description: str = "",
    prefix: str | None = None,
    keep_defaults: bool = False,
) -> NixFragment:
    """Compiles a NixModule into a NixFragment for layout rendering."""
    scoped, root_opts, active_args = _serialize_fields(
        module, preserve_comments=True, keep_defaults=keep_defaults
    )
    effective_prefix = module.prefix if module.prefix is not None else (prefix or "")

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
        else module.__class__.__name__
    )

    doc_description = (
        (module.__doc__ or "").strip().split("\n")[0] if module.__doc__ else ""
    )
    fragment_description = description or doc_description

    options: dict[str, NixValue] = {
        k: v if isinstance(v, NixValue) else NixValue(value=v) for k, v in data.items()
    }

    return NixFragment(
        name=fragment_name,
        description=fragment_description,
        options=options,
        arguments=active_args,
    )
