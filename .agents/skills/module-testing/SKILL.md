---
name: module-testing
description: Guide and patterns for writing unit tests for nix-scribe parsers and modules using pytest tmp_path fixtures.
---

# Module & Parser Testing Guide

All `nix-scribe` tests must be filesystem-backed using `pytest`'s `tmp_path` fixture.

## Testing Rules & Standards
1. **Use `tmp_path` Fixture**: Always build the target mock directory layout inside `tmp_path`.
2. **No Complex Mocking**: Do **not** mock filesystem functions (`os.path.exists`, `open`, `Path.read_text`).
3. **Allowed Mocks**: Only mock non-filesystem interactions (e.g. `context.systemctl.is_enabled`).
4. **Fast Execution**: Unit tests must run in <0.5 seconds total.

## Unit Test Template (`tests/scanners/test_my_service.py`)

```python
from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.nix_fragment import NixFragment
from nix_scribe.scanners.services.my_service import my_service

MOCK_CONFIG = """
# /etc/my_service/config.conf
setting_name = my_value
"""


def test_my_service_scanner_empty(tmp_path):
    context = SystemContext(tmp_path)
    assert my_service.scan(context) is None


def test_my_service_scanner_with_files(tmp_path):
    conf_dir = tmp_path / "etc/my_service"
    conf_dir.mkdir(parents=True)
    (conf_dir / "config.conf").write_text(MOCK_CONFIG)

    context = SystemContext(tmp_path)
    mod = my_service.scan(context)

    assert mod is not None
    assert mod.enable is True
    assert mod.settingName == "my_value"
    assert mod.resolve_claims() == {"my-service"}

    block = mod.to_nix_fragment()
    assert isinstance(block, NixFragment)
    data = block["services.myService"]
    assert data["enable"] is True
    assert data["settingName"] == "my_value"
```

## Running Verification Commands
Before finalizing changes:
```bash
direnv exec . ruff check --fix
direnv exec . ruff format
direnv exec . pytest
```
