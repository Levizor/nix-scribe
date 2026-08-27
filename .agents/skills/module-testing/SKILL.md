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

## Unit Test Template (`tests/modules/test_my_module.py`)

```python
from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.modules.category.my_module import my_module

MOCK_CONFIG = """
# /etc/my_service/config.conf
setting_name = my_value
"""


def test_my_module_scanner_empty(tmp_path):
    context = SystemContext(tmp_path)
    ir = my_module.scan(context)
    assert ir == {}


def test_my_module_scanner_with_files(tmp_path):
    conf_dir = tmp_path / "etc/my_service"
    conf_dir.mkdir(parents=True)
    (conf_dir / "config.conf").write_text(MOCK_CONFIG)

    context = SystemContext(tmp_path)
    ir = my_module.scan(context)

    assert ir["enable"] is True
    assert ir["settingName"] == "my_value"


def test_my_module_mapper():
    assert my_module.map
    mock_ir = {"enable": True, "settingName": "custom_val"}

    block = my_module.map(mock_ir)
    assert isinstance(block, ConfigFragment)
    data = block["services.myService"]
    assert data["enable"] is True
    assert data["settingName"] == "custom_val"


def test_my_module_mapper_empty():
    assert my_module.map(None) is None
    assert my_module.map({}) is None
```

## Running Verification Commands
Before finalizing changes:
```bash
direnv exec . ruff check --fix
direnv exec . ruff format
direnv exec . pytest
```
