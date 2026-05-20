from dataclasses import dataclass
from typing import Any

from .asset import Asset
from .nix_writer import raw


def combined_comments(*args: str | None) -> str | None:
    """Combines multiple comments, ignoring Nones and removing duplicates."""
    valid_comments = [c for c in args if c]

    if not valid_comments:
        return None

    unique_comments = list(dict.fromkeys(valid_comments))

    return " | ".join(unique_comments)


def flatten_nix_options(
    data: dict[str, Any], parent_key: str = ""
) -> dict[str, tuple[Any, str | None]]:
    """
    Recursively converts nested dictionaries and NixValue types into a flat dictionary with dot-notation keys
    and tuples containing the value and the comment to it.
    Example: "programs.firefox": {"enable": True}" into "programs.firefox.enable": True.
    """
    flattened: dict[str, Any] = {}

    for key, value in data.items():
        new_key = f"{parent_key}.{key}" if parent_key else key
        comment = None

        # unpack NixValue
        if isinstance(value, NixValue):
            comment = value.comment
            value = value.value

        if isinstance(value, dict) and value:
            sub_flattened = flatten_nix_options(value, new_key)

            # attach comment to the top option
            if comment and sub_flattened:
                first_key = next(iter(sub_flattened))
                sub_val, sub_comment = sub_flattened[first_key]
                sub_flattened[first_key] = (
                    sub_val,
                    combined_comments(comment, sub_comment),
                )

            flattened.update(sub_flattened)
        else:
            flattened[new_key] = (value, comment)

    return flattened


@dataclass
class NixValue:
    value: Any
    comment: str | None = None

    def __getattr__(self, name) -> Any:
        return getattr(self.value, name)

    def __getitem__(self, key: Any) -> Any:
        return self.value.__getitem__(key)

    def __setitem__(self, key: Any, value: Any) -> Any:
        return self.value.__setitem__(key, value)

    def __contains__(self, item: Any) -> bool:
        return self.value.__contains__(item)

    def __eq__(self, value: object, /) -> bool:
        return self.value.__eq__(value)

    def __bool__(self) -> bool:
        return bool(self.value)


class ConfigFragment:
    def __init__(
        self,
        name: str,
        description: str = "",
        data: dict[str, Any] | None = None,
        arguments: set[str] | None = None,
        assets: set[Asset] | None = None,
    ):
        self.name = name
        self.description = description
        self.options: dict[str, NixValue] = {}
        self.arguments = arguments if arguments else set()
        self.assets = assets if assets else set()

        if data:
            for k, v in data.items():
                self.add_option(k, v)

    def add_option(self, key: str, value: Any, comment: str | None = None) -> None:
        self._inspect_value(value)
        if isinstance(value, NixValue):
            self.options[key] = value
        else:
            self.options[key] = NixValue(value=value, comment=comment)

    def _inspect_value(self, value: Any) -> None:
        """
        Recursively finds and registers assets and arguments in the value being set
        """
        if isinstance(value, Asset):
            self.assets.add(value)
        elif isinstance(value, raw):
            text = str(value)
            if "pkgs" in text:
                self.arguments.add("pkgs")
            if "lib" in text:
                self.arguments.add("lib")
            if "config" in text:
                self.arguments.add("config")
        elif isinstance(value, dict):
            for v in value.values():
                self._inspect_value(v)
        elif isinstance(value, list):
            for v in value:
                self._inspect_value(v)

    def __setitem__(self, key: str | tuple[str, str], value: Any) -> None:
        """
        Standard assignment: fragment["key"] = value
        With comment: fragment["key", "comment"] = value
        """
        if isinstance(key, tuple):
            if len(key) != 2:
                raise ValueError(f"Invalid key tuple {key}. Expected: (key, comment)")
            actual_key, comment = key
            self.add_option(key=actual_key, value=value, comment=comment)
        else:
            self.add_option(key, value)

    def __getitem__(self, key: str) -> Any:
        return self.options.__getitem__(key)


class DocumentNode:
    pass


@dataclass
class CommentNode(DocumentNode):
    text: str


@dataclass
class EmptyLineNode(DocumentNode):
    pass


@dataclass
class OptionNode(DocumentNode):
    key: str
    value: Any
    inline_comment: str | None = None


class OptionCollisionError(Exception):
    def __init__(self, key: str, existing: Any, rejected: Any) -> None:
        self.key = key
        self.existing = existing
        self.rejected = rejected
        super().__init__(
            f"Collision on '{key}'. Existing: '{existing}'. Rejected: '{rejected}'"
        )


class NixOptionDocument:
    def __init__(self) -> None:
        self._layout: list[DocumentNode] = []
        self._index: dict[str, OptionNode] = {}

    def add_header(self, text: str) -> None:
        self._layout.append(CommentNode(text))

    def add_option(self, base_key: str, nix_value: NixValue) -> None:
        flat_options = flatten_nix_options({base_key: nix_value})

        for key, (value, comment) in flat_options.items():
            if key not in self._index:
                new_node = OptionNode(key, value, comment)
                self._layout.append(new_node)
                self._index[key] = new_node
            else:
                existing_node = self._index[key]

                # merge lists
                if isinstance(existing_node.value, list) and isinstance(value, list):
                    existing_node.value.extend(value)
                    # remove duplicates
                    existing_node.value = list(dict.fromkeys(existing_node.value))

                # throw collisions
                elif existing_node.value != value:
                    raise OptionCollisionError(key, existing_node.value, value)

                # merge comments
                existing_node.inline_comment = combined_comments(
                    existing_node.inline_comment, comment
                )

        self._layout.append(EmptyLineNode())

    def flag_collision(self, key: str, rejected_value: Any, fragment_name: str) -> None:
        """Injects a collision warning for a specific index node"""
        node = self._index[key]
        warning = (
            f"FIXME: Conflict! '{fragment_name}' attempted to set '{rejected_value}'"
        )
        if node.inline_comment:
            node.inline_comment = f"{warning} | {node.inline_comment}"

    def __len__(self):
        return len(self._layout)

    def __iter__(self):
        return self._layout.__iter__()
