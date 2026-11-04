from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nix_scribe.lib.context import SystemContext

logger = logging.getLogger(__name__)


class Systemctl:
    def __init__(self, system_context: SystemContext):
        self.context = system_context
        self._existing: set[str] = set()
        self._enabled: set[str] = set()
        self._masked: set[str] = set()
        self._build_state()

    def _build_state(self) -> None:
        paths = [
            "/lib/systemd/system",
            "/usr/lib/systemd/system",
            "/etc/systemd/system",
        ]

        for base in paths:
            if not self.context.path_exists(base):
                continue

            logger.debug("Scanning systemd units in %s", base)
            for item in self.context.list_directory(base):
                guest_path = f"{base}/{item}"
                if item.endswith(".service"):
                    self._process_unit(guest_path, base)
                elif item.endswith(".wants") or item.endswith(".requires"):
                    for link in self.context.list_directory(guest_path):
                        if link.endswith(".service"):
                            self._process_dependency(f"{guest_path}/{link}", guest_path)

        logger.debug(
            "Built systemctl state: %d units discovered, %d enabled, %d masked",
            len(self._existing),
            len(self._enabled),
            len(self._masked),
        )

    def _is_masked(self, path: str) -> bool:
        if self.context.is_symlink(path):
            try:
                target = self.context.readlink(path)
                return target == "/dev/null" or target.endswith("/dev/null")
            except Exception:
                pass
        return False

    def _target_exists(self, path: str, guest_parent: str) -> bool:
        if not self.context.is_symlink(path):
            return True
        try:
            target = self.context.readlink(path)
            if os.path.isabs(target):
                return self.context.path_exists(target)

            guest_path = os.path.normpath(f"{guest_parent}/{target}")
            return self.context.path_exists(guest_path)
        except Exception:
            return False

    def _process_unit(self, path: str, guest_parent: str) -> None:
        name = os.path.basename(path)
        if self._is_masked(path):
            self._masked.add(name)
            self._existing.discard(name)
            logger.debug("Systemd unit %s is masked", name)
        else:
            self._existing.add(name)
            self._masked.discard(name)

            if self.context.is_symlink(path):
                try:
                    target = self.context.readlink(path)
                    target_name = os.path.basename(target)
                    if target_name.endswith(".service") and self._target_exists(
                        path, guest_parent
                    ):
                        self._enabled.add(target_name)
                        logger.debug(
                            "Systemd unit %s enabled via symlink in %s",
                            target_name,
                            guest_parent,
                        )
                except Exception:
                    pass

    def _process_dependency(self, path: str, guest_parent: str) -> None:
        name = os.path.basename(path)
        if self._is_masked(path):
            self._enabled.discard(name)
        elif self._target_exists(path, guest_parent):
            self._enabled.add(name)
            logger.debug(
                "Systemd unit %s enabled via dependency %s", name, guest_parent
            )

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
        res = (
            name in self._existing or base_name in self._existing
        ) and name not in self._masked
        logger.debug("systemctl.exists(%s) -> %s", service, res)
        return res

    def is_enabled(self, service: str) -> bool:
        name = self._normalize_service_name(service)
        res = name in self._enabled and name not in self._masked and self.exists(name)
        logger.debug("systemctl.is_enabled(%s) -> %s", service, res)
        return res

    def is_disabled(self, service: str) -> bool:
        if not self.exists(service):
            return False
        name = self._normalize_service_name(service)
        res = name not in self._enabled
        logger.debug("systemctl.is_disabled(%s) -> %s", service, res)
        return res
