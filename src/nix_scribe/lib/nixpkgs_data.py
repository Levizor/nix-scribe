from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path
from typing import Any

import brotli

DEFAULT_CHANNEL = "nixos-unstable"
DEFAULT_CACHE_TTL_SECONDS = 86400

OPTIONS_URL_TEMPLATE = "https://channels.nixos.org/{channel}/options.json.br"
PACKAGES_URL_TEMPLATE = "https://channels.nixos.org/{channel}/packages.json.br"


def get_cache_dir(channel: str = DEFAULT_CHANNEL) -> Path:
    """Returns the cache directory for downloaded nixpkgs artifacts."""
    env_dir = os.environ.get("NIX_SCRIBE_CACHE_DIR")
    if env_dir:
        base = Path(env_dir)
    else:
        xdg_cache = os.environ.get("XDG_CACHE_HOME")
        base = (Path(xdg_cache) if xdg_cache else Path.home() / ".cache") / "nix-scribe"
    return base / "nixpkgs" / channel


def _fetch_brotli_json(
    url: str,
    cache_path: Path,
    *,
    ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Downloads and caches a Brotli-compressed JSON artifact, returning parsed data."""
    if not force_refresh and cache_path.exists():
        age = time.time() - cache_path.stat().st_mtime
        if age < ttl_seconds:
            return json.loads(cache_path.read_text(encoding="utf-8"))

    req = urllib.request.Request(url, headers={"User-Agent": "nix-scribe"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        compressed = resp.read()

    raw_json = brotli.decompress(compressed)
    data = json.loads(raw_json)

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = cache_path.with_suffix(".json.tmp")
    tmp_path.write_bytes(raw_json)
    os.replace(tmp_path, cache_path)

    return data


class NixpkgsOptionsIndex:
    """Lookup index over NixOS options.json."""

    def __init__(self, options: dict[str, dict[str, Any]]) -> None:
        self._options = options

    @classmethod
    def from_channel(
        cls,
        channel: str = DEFAULT_CHANNEL,
        *,
        ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
        force_refresh: bool = False,
    ) -> NixpkgsOptionsIndex:
        url = OPTIONS_URL_TEMPLATE.format(channel=channel)
        cache_path = get_cache_dir(channel) / "options.json"
        data = _fetch_brotli_json(
            url,
            cache_path,
            ttl_seconds=ttl_seconds,
            force_refresh=force_refresh,
        )
        return cls(data)

    def has_option(self, path: str) -> bool:
        """Checks whether a NixOS option path exists in options.json."""
        if path in self._options:
            return True

        parts = path.split(".")
        for i in range(len(parts) - 1, 0, -1):
            prefix = ".".join(parts[:i])
            entry = self._options.get(prefix)
            if entry and entry.get("type") == "submodule":
                suffix = ".".join(parts[i:])
                if self.has_option(suffix):
                    return True

        return False

    def get(self, path: str) -> dict[str, Any] | None:
        """Returns raw option metadata if present."""
        return self._options.get(path)

    def __len__(self) -> int:
        return len(self._options)


class NixpkgsPackagesIndex:
    """Lookup index over Nixpkgs packages.json."""

    def __init__(self, packages: dict[str, Any] | set[str]) -> None:
        self._packages = set(packages)

    @classmethod
    def from_channel(
        cls,
        channel: str = DEFAULT_CHANNEL,
        *,
        ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
        force_refresh: bool = False,
    ) -> NixpkgsPackagesIndex:
        url = PACKAGES_URL_TEMPLATE.format(channel=channel)
        cache_path = get_cache_dir(channel) / "packages.json"
        data = _fetch_brotli_json(
            url,
            cache_path,
            ttl_seconds=ttl_seconds,
            force_refresh=force_refresh,
        )
        return cls(data.get("packages", {}))

    def has_package(self, attr_path: str) -> bool:
        """Checks whether a package attribute path exists in packages.json."""
        return attr_path in self._packages

    def __len__(self) -> int:
        return len(self._packages)
