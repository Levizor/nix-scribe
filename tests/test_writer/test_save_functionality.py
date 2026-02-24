import tempfile
import unittest.mock
from pathlib import Path

from nix_scribe.lib.asset import Asset
from nix_scribe.lib.modularization import ModularizationLevel
from nix_scribe.lib.nixfile import NixFile
from nix_scribe.lib.option_block import SimpleOptionBlock


def setup_test_hierarchy():
    root = NixFile("configuration")
    net = NixFile("networking")

    firewall = NixFile("firewall")
    fw_block = SimpleOptionBlock("firewall")
    fw_asset = Asset("/etc/firewall.conf", "firewall.conf")
    fw_block["config"] = fw_asset
    firewall.add_option_block(fw_block)

    nm = NixFile("networkmanager")
    nm_block = SimpleOptionBlock("networkmanager")
    nm_block["enable"] = True
    nm.add_option_block(nm_block)

    return root, net, firewall, nm


def mock_copy_file(src, dst):
    Path(dst).touch()


def test_save_single_file():
    mock_context = unittest.mock.MagicMock()
    mock_context.copy_file.side_effect = mock_copy_file
    root, net, firewall, nm = setup_test_hierarchy()

    root.add_option_block(firewall.options[0])
    root.add_option_block(nm.options[0])

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        root.save(tmp_path, ModularizationLevel.SINGLE_FILE, mock_context)

        assert (tmp_path / "configuration.nix").exists()
        assert (tmp_path / "firewall.conf").exists()


def test_save_high_level():
    mock_context = unittest.mock.MagicMock()
    mock_context.copy_file.side_effect = mock_copy_file
    root, net, firewall, nm = setup_test_hierarchy()

    net.add_option_block(firewall.options[0])
    net.add_option_block(nm.options[0])
    root.add_import(net)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        root.save(tmp_path, ModularizationLevel.HIGH_LEVEL, mock_context)

        assert (tmp_path / "configuration.nix").exists()
        assert (tmp_path / "networking.nix").exists()
        assert (tmp_path / "firewall.conf").exists()


def test_save_component_level():
    mock_context = unittest.mock.MagicMock()
    mock_context.copy_file.side_effect = mock_copy_file
    root, net, firewall, nm = setup_test_hierarchy()

    net.add_import(firewall)
    net.add_import(nm)
    root.add_import(net)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        root.save(tmp_path, ModularizationLevel.COMPONENT_LEVEL, mock_context)

        assert (tmp_path / "configuration.nix").exists()
        assert (tmp_path / "networking" / "default.nix").exists()
        assert (tmp_path / "networking" / "firewall.nix").exists()
        assert (tmp_path / "networking" / "networkmanager.nix").exists()
        assert (tmp_path / "networking" / "firewall.conf").exists()
