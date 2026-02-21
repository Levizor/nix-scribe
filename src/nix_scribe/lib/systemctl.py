from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Set

if TYPE_CHECKING:
    from nix_scribe.lib.context import SystemContext


class Systemctl:
    def __init__(self, system_context: SystemContext):
        self.context = system_context
        self._existing: Set[str] = set()
        self._enabled: Set[str] = set()
        self._masked: Set[str] = set()
        self._build_state()

    def _build_state(self) -> None:
        paths = [
            "/lib/systemd/system",
            "/usr/lib/systemd/system",
            "/etc/systemd/system",
        ]

        for base in paths:
            base_path = self.context.root_path(base)
            if not base_path.is_dir():
                continue

            for item in base_path.iterdir():
                if item.name.endswith(".service"):
                    self._process_unit(item, base)
                elif item.is_dir() and (
                    item.name.endswith(".wants") or item.name.endswith(".requires")
                ):
                    guest_parent = f"{base}/{item.name}"
                    for link in item.iterdir():
                        if link.name.endswith(".service"):
                            self._process_dependency(link, guest_parent)

    def _is_masked(self, path: Path) -> bool:
        if path.is_symlink():
            try:
                target = os.readlink(path)
                return target == "/dev/null" or target.endswith("/dev/null")
            except OSError:
                pass
        return False

    def _target_exists(self, path: Path, guest_parent: str) -> bool:
        if not path.is_symlink():
            return True
        try:
            target = os.readlink(path)
            if os.path.isabs(target):
                return self.context.path_exists(target)

            guest_path = os.path.normpath(f"{guest_parent}/{target}")
            return self.context.path_exists(guest_path)
        except OSError:
            return False

    def _process_unit(self, path: Path, guest_parent: str) -> None:
        name = path.name
        if self._is_masked(path):
            self._masked.add(name)
            self._existing.discard(name)
        else:
            self._existing.add(name)
            self._masked.discard(name)

            if path.is_symlink():
                try:
                    target = os.readlink(path)
                    target_name = Path(target).name
                    if target_name.endswith(".service") and self._target_exists(
                        path, guest_parent
                    ):
                        self._enabled.add(target_name)
                except OSError:
                    pass

    def _process_dependency(self, path: Path, guest_parent: str) -> None:
        name = path.name
        if self._is_masked(path):
            self._enabled.discard(name)
        elif self._target_exists(path, guest_parent):
            self._enabled.add(name)

    def _normalize_service_name(self, service: str) -> str:
        if not service.endswith(".service"):
            return f"{service}.service"
        return service

    def _get_template_base(self, service: str) -> str:
        if "@" in service:
            return f"{service.split('@')[0]}@.service"
        return service

    def exists(self, service: str) -> bool:
        name = self._normalize_service_name(service)
        base_name = self._get_template_base(name)
        return (
            name in self._existing or base_name in self._existing
        ) and name not in self._masked

    def is_enabled(self, service: str) -> bool:
        name = self._normalize_service_name(service)
        return name in self._enabled and name not in self._masked and self.exists(name)

    def is_disabled(self, service: str) -> bool:
        if not self.exists(service):
            return False
        name = self._normalize_service_name(service)
        return name not in self._enabled
