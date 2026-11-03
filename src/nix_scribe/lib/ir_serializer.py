from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from nix_scribe.lib.packages.models import (
    DiscoveredPackage,
    PackageState,
    ResolvedPackage,
)

SENSITIVE_KEYS = {
    "hashedpassword",
    "password",
    "secret",
    "private_key",
    "privatekey",
}


def sanitize_ir(data: Any) -> Any:
    """Recursively redacts sensitive values such as password hashes."""
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if str(k).lower() in SENSITIVE_KEYS and v is not None:
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_ir(v)
        return sanitized
    elif isinstance(data, (list, tuple)):
        return [sanitize_ir(item) for item in data]
    return data


class IRJSONEncoder(json.JSONEncoder):
    """JSON encoder capable of serializing custom nix-scribe IR structures and Python primitives."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, PackageState):
            return {
                "resolved": [
                    {
                        "name": p.name,
                        "original_name": p.original_name,
                        "repository": p.repository,
                        "reason": p.reason.value,
                    }
                    for p in obj.resolved
                ],
                "unmapped": [
                    {
                        "name": p.name,
                        "repository": p.repository,
                        "reason": p.reason.value,
                    }
                    for p in obj.unmapped
                ],
                "claimed": sorted(obj.claimed),
            }
        if isinstance(obj, ResolvedPackage):
            return {
                "name": obj.name,
                "original_name": obj.original_name,
                "repository": obj.repository,
                "reason": obj.reason.value,
            }
        if isinstance(obj, DiscoveredPackage):
            return {
                "name": obj.name,
                "repository": obj.repository,
                "reason": obj.reason.value,
            }
        if is_dataclass(obj) and not isinstance(obj, type):
            return asdict(obj)
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, (set, frozenset)):
            return sorted(list(obj), key=lambda x: str(x))
        if isinstance(obj, bytes):
            try:
                return obj.decode("utf-8")
            except UnicodeDecodeError:
                return obj.hex()
        return super().default(obj)


def dump_ir_to_dict(results: dict[str, Any]) -> dict[str, Any]:
    """Serializes module results IR to a sanitized dictionary structure."""
    raw_ir = {
        name: result.scan_data
        for name, result in results.items()
        if hasattr(result, "scan_data") and result.scan_data
    }
    json_str = json.dumps(raw_ir, cls=IRJSONEncoder, indent=2)
    return sanitize_ir(json.loads(json_str))


def save_ir_to_file(results: dict[str, Any], output_path: Path) -> Path:
    """Saves the sanitized system IR to scan-ir.json in output_path."""
    output_path.mkdir(parents=True, exist_ok=True)
    target_file = output_path / "scan-ir.json"
    sanitized = dump_ir_to_dict(results)
    target_file.write_text(json.dumps(sanitized, indent=2) + "\n", encoding="utf-8")
    return target_file
