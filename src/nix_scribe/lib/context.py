from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from nix_scribe.lib.systemctl import Systemctl

logger = logging.getLogger(__name__)

COMMON_TARGET_BINARIES_PATHS = [
    "/usr/bin",
    "/bin",
    "/usr/sbin",
    "/sbin",
    "/usr/local/bin",
]


class ElevationRequest(Exception):
    def __init__(self, target: str, description: str):
        self.target = target
        self.description = description
        super().__init__(f"Access denied to {target}. {description}")


class SystemContext:
    def __init__(self, root: Path, use_sudo: bool = False):
        self.root = root
        self.use_sudo = use_sudo
        self.systemctl = Systemctl(self)

    def root_path(self, path: str) -> Path:
        """
        Return a path relative to the input root.
        Required to use on paths when running custom commands.
        """
        return Path(os.path.normpath(f"{self.root}/{path}"))

    def path_exists(self, path: str | Path) -> bool:
        rpath = self.root_path(path) if isinstance(path, str) else path
        try:
            rpath.stat()
            return True
        except FileNotFoundError:
            return False
        except PermissionError:
            if self.use_sudo:
                try:
                    self.run_command(["sudo", "test", "-e", rpath])
                    return True
                except RuntimeError:
                    return False
            return False

    def find_executable_path(self, name: str) -> Optional[str]:
        logger.debug("Find executable")
        if self.root == Path("/"):
            return shutil.which(name)

        for bin_dir in COMMON_TARGET_BINARIES_PATHS:
            path = self.root_path(bin_dir + "/" + name)

            if path.exists():
                return str(path)

    def _root_command_args(self, command: list[str]) -> list[str]:
        if self.root == Path("/"):
            return command

        result = [command[0]]

        for arg in command[1:]:
            if (
                arg.startswith("/")
                and len(arg) > 1
                and not arg.startswith((":/", "//"))
            ):
                result.append(str(self.root_path(arg)))
            else:
                result.append(arg)

        return result

    def run_command(self, command: list):
        command = self._root_command_args(command)
        logger.debug(f"Running command: {command}")
        if command[0] == "sudo":
            try:
                result = subprocess.run(
                    command, check=True, capture_output=True, text=True
                )
                return result.stdout.strip()
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Command failed: {e.stderr}") from e

        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            err = e.stderr.lower()
            if "permission denied" in err or "access denied" in err:
                if self.use_sudo:
                    return self.run_command(["sudo"] + command)
                raise ElevationRequest(
                    " ".join(command), "Command requires root privileges."
                ) from e
            raise RuntimeError(f"Command failed: {e.stderr}") from e

    def verify_sudo(self) -> bool:
        try:
            subprocess.run(["sudo", "-v"], check=True)
            self.use_sudo = True
        except subprocess.CalledProcessError:
            self.use_sudo = False

        return self.use_sudo

    def read_file(self, path: str) -> str:
        rpath = self.root_path(path)

        try:
            return rpath.read_text(encoding="utf-8")
        except PermissionError:
            if self.use_sudo:
                return self.run_command(["sudo", "cat", path])
            raise ElevationRequest(path, "Read permission denied.") from PermissionError

    def read_directory_files(self, path: str) -> list[str]:
        """
        Reads all files inside a specified directory files, return list of strings
        """
        result = []
        rpath = self.root_path(path)

        for file_path in sorted(os.listdir(rpath)):
            result.append(self.read_file(file_path))

        return result

    def copy_file(self, src: str, dst: Path) -> None:
        """
        Copies a file from the target system to a destination path
        """
        rsrc = self.root_path(src)
        logger.debug(f"Copying file from {rsrc} to {dst}")

        try:
            shutil.copy2(rsrc, dst)
        except PermissionError:
            if self.use_sudo:
                self.run_command(["sudo", "cp", "-p", src, str(dst)])
            else:
                raise ElevationRequest(
                    str(rsrc), f"Permission denied while copying to {dst}"
                ) from PermissionError
        except Exception as e:
            logger.error(f"Failed to copy {rsrc} to {dst}: {e}")
            raise
