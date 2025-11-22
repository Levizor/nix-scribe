import subprocess
from pathlib import Path


class ElevationRequest(Exception):
    def __init__(self, target: str, description: str):
        self.target = target
        self.description = description
        super().__init__(f"Access denied to {target}. {description}")


class SystemContext:
    def __init__(self, use_sudo: bool = False):
        self.use_sudo = use_sudo

    def exists(self, path: str) -> bool:
        try:
            Path(path).stat()
            return True
        except FileNotFoundError:
            return False
        except PermissionError:
            if self.use_sudo:
                try:
                    self.run_command(["sudo", "test", "-e", path])
                    return True
                except RuntimeError:
                    return False
            return False

    def run_command(self, command: list):
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
        path_obj = Path(path)

        try:
            return path_obj.read_text(encoding="utf-8")
        except PermissionError:
            if self.use_sudo:
                return self.run_command(["sudo", "cat", path])
            raise ElevationRequest(path, "Read permission denied.") from PermissionError
