import json
import shutil
import unittest.mock

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.modules.security.sudo import SudoMapper, SudoScanner

MOCK_TEXT_OUTPUT = """Defaults env_reset
Defaults:root, %wheel env_keep+=TERMINFO_DIRS
root ALL=(ALL:ALL) SETENV: ALL
%wheel ALL=(ALL) NOPASSWD: ALL
"""

MOCK_JSON_OUTPUT = {
    "Defaults": [{"Options": [{"env_keep": ["TERMINFO"]}]}],
    "User_Specs": [
        {
            "User_List": [{"usergroup": "wheel"}],
            "Cmnd_Specs": [{"Options": [{"authenticate": False}]}],
        }
    ],
}


def test_scanner_hybrid_approach(tmp_path, monkeypatch):
    (tmp_path / "etc").mkdir()
    (tmp_path / "etc/sudoers").touch()
    (tmp_path / "bin").mkdir()
    (tmp_path / "bin/sudo").touch()

    context = SystemContext(tmp_path)

    monkeypatch.setattr(
        shutil, "which", lambda x: f"/usr/bin/{x}" if x == "cvtsudoers" else None
    )

    monkeypatch.setattr(
        context,
        "run_command",
        unittest.mock.MagicMock(
            side_effect=[
                MOCK_TEXT_OUTPUT,
                json.dumps(MOCK_JSON_OUTPUT),
                "4755 root",
            ]
        ),
    )

    scanner = SudoScanner()
    ir = scanner.scan(context)

    assert ir["enable"] is True
    assert ir["wheelNeedsPassword"] is False
    assert ir["keepTerminfo"] is True


def test_mapper_filtering():
    mock_ir = {
        "enable": True,
        "wheelNeedsPassword": False,
        "execWheelOnly": False,
        "keepTerminfo": True,
    }

    mapper = SudoMapper()
    block = mapper.map(mock_ir)

    assert isinstance(block, SimpleOptionBlock)
    data = block.data["security.sudo"]

    assert data["wheelNeedsPassword"] is False
