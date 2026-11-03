from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from nix_scribe.lib.ir_serializer import (
    IRJSONEncoder,
    dump_ir_to_dict,
    sanitize_ir,
    save_ir_to_file,
)
from nix_scribe.lib.packages.models import (
    DiscoveredPackage,
    InstallReason,
    PackageState,
    ResolvedPackage,
)
from nix_scribe.nixscribe import ModuleResult


class DummyEnum(Enum):
    ALPHA = "alpha"
    BETA = "beta"


@dataclass
class DummyData:
    user: str
    active: bool


def test_sanitize_ir():
    data = {
        "user": "root",
        "hashedPassword": "$6$salt$encryptedpasswordhash",
        "nested": {
            "password": "secretpassword",
            "private_key": "-----BEGIN PRIVATE KEY-----...",
            "normal_field": 123,
        },
        "items": [
            {"secret": "token123"},
            {"safe": "value"},
        ],
    }

    sanitized = sanitize_ir(data)

    assert sanitized["user"] == "root"
    assert sanitized["hashedPassword"] == "[REDACTED]"
    assert sanitized["nested"]["password"] == "[REDACTED]"
    assert sanitized["nested"]["private_key"] == "[REDACTED]"
    assert sanitized["nested"]["normal_field"] == 123
    assert sanitized["items"][0]["secret"] == "[REDACTED]"
    assert sanitized["items"][1]["safe"] == "value"


def test_ir_json_encoder():
    import json

    disc = DiscoveredPackage("ripgrep", "arch", InstallReason.EXPLICIT)
    res = ResolvedPackage("ripgrep", disc)
    state = PackageState(packages=[res], unmapped=[disc])
    state.claim("ripgrep", by="programs.ripgrep")

    payload = {
        "package_state": state,
        "resolved_pkg": res,
        "discovered_pkg": disc,
        "dataclass": DummyData("alice", True),
        "enum": DummyEnum.ALPHA,
        "path": Path("/etc/nixos"),
        "set": {"banana", "apple"},
        "bytes_utf8": b"hello world",
        "bytes_binary": b"\x80\xff\xfe",
    }

    serialized = json.dumps(payload, cls=IRJSONEncoder)
    deserialized = json.loads(serialized)

    assert deserialized["package_state"]["resolved"][0]["name"] == "ripgrep"
    assert deserialized["package_state"]["resolved"][0]["repository"] == "arch"
    assert deserialized["package_state"]["claimed"] == ["ripgrep"]
    assert deserialized["package_state"]["unmapped"][0]["name"] == "ripgrep"
    assert deserialized["resolved_pkg"]["name"] == "ripgrep"
    assert deserialized["discovered_pkg"]["name"] == "ripgrep"
    assert deserialized["dataclass"] == {"user": "alice", "active": True}
    assert deserialized["enum"] == "alpha"
    assert deserialized["path"] == "/etc/nixos"
    assert deserialized["set"] == ["apple", "banana"]
    assert deserialized["bytes_utf8"] == "hello world"
    assert deserialized["bytes_binary"] == "80fffe"


def test_dump_ir_to_dict_and_save_to_file(tmp_path):
    from nix_scribe.lib.registry import Module

    mod1 = Module("boot.loader.systemd-boot")
    mod2 = Module("users.users")
    mod3 = Module("empty.module")

    res1 = ModuleResult(module=mod1, scan_data={"enable": True, "timeout": 5})
    res2 = ModuleResult(
        module=mod2,
        scan_data={
            "users": {
                "root": {
                    "hashedPassword": "$6$dummyhash",
                    "shell": "/bin/bash",
                }
            }
        },
    )
    res3 = ModuleResult(module=mod3, scan_data={})

    results = {
        "boot.loader.systemd-boot": res1,
        "users.users": res2,
        "empty.module": res3,
    }

    dumped = dump_ir_to_dict(results)
    assert "boot.loader.systemd-boot" in dumped
    assert "users.users" in dumped
    assert "empty.module" not in dumped
    assert dumped["boot.loader.systemd-boot"] == {"enable": True, "timeout": 5}
    assert dumped["users.users"]["users"]["root"]["hashedPassword"] == "[REDACTED]"
    assert dumped["users.users"]["users"]["root"]["shell"] == "/bin/bash"

    output_dir = tmp_path / "out"
    saved_file = save_ir_to_file(results, output_dir)

    assert saved_file == output_dir / "scan-ir.json"
    assert saved_file.exists()

    import json

    file_content = json.loads(saved_file.read_text(encoding="utf-8"))
    assert file_content == dumped
