from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from nix_scribe.lib.nix_module import NixModule
from nix_scribe.lib.packages.models import (
    DiscoveredPackage,
    PackageState,
    ResolvedPackage,
)


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
        if isinstance(obj, NixModule):
            return obj.to_dict(keep_defaults=True)
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
    """Serializes module results IR to a JSON-compatible dictionary structure."""
    raw_ir = {
        name: result.scan_data
        for name, result in results.items()
        if hasattr(result, "scan_data") and result.scan_data
    }
    return json.loads(json.dumps(raw_ir, cls=IRJSONEncoder))


def save_ir_to_file(results: dict[str, Any], output_path: Path) -> Path:
    """Saves the system IR to scan-ir.json in output_path."""
    output_path.mkdir(parents=True, exist_ok=True)
    target_file = output_path / "scan-ir.json"
    data = dump_ir_to_dict(results)
    target_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return target_file
