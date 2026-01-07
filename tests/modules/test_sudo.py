import json
import unittest.mock

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


@unittest.mock.patch("shutil.which")
def test_scanner_hybrid_approach(mock_which):
    def which_side_effect(arg):
        if arg == "cvtsudoers":
            return "/usr/bin/cvtsudoers"
        if arg == "sudo":
            return "/usr/bin/sudo"
        return None

    mock_which.side_effect = which_side_effect

    mock_context = unittest.mock.MagicMock()
    # 1. Text output, 2. JSON output, 3. Stat output
    mock_context.run_command.side_effect = [
        MOCK_TEXT_OUTPUT,
        json.dumps(MOCK_JSON_OUTPUT),
        "4755 root",  # Standard permissions (execWheelOnly=False)
    ]

    scanner = SudoScanner()
    ir = scanner.scan(mock_context)

    assert ir["enable"] is True
    assert ir["wheelNeedsPassword"] is False
    assert ir["keepTerminfo"] is True
    # assert len(ir["extraConfigLines"]) == 4


def test_mapper_filtering():
    mock_ir = {
        "enable": True,
        "wheelNeedsPassword": False,
        "execWheelOnly": False,
        "keepTerminfo": True,
        # "extraConfigLines": [
        #     "Defaults env_reset",
        #     "Defaults:root, %wheel env_keep+=TERMINFO_DIRS",  # Should filter
        #     "root ALL=(ALL:ALL) SETENV: ALL",  # Should filter
        #     "%wheel ALL=(ALL) NOPASSWD: ALL",  # Should filter
        #     "custom_user ALL=(ALL) ALL",  # Should keep
        # ],
    }

    mapper = SudoMapper()
    block = mapper.map(mock_ir)

    assert isinstance(block, SimpleOptionBlock)
    data = block.data["security.sudo"]

    assert data["wheelNeedsPassword"] is False

    # extra_config = data.get("extraConfig", "")
    # assert "Defaults env_reset" in extra_config
    # assert "custom_user" in extra_config
    #
    # # Assertions for filtered lines
    # assert "TERMINFO" not in extra_config
    # assert "root ALL" not in extra_config
    # assert "%wheel" not in extra_config
