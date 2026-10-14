import tempfile
from pathlib import Path

from nix_scribe.lib.asset import Asset
from nix_scribe.lib.modularization import ModularizationLevel
from nix_scribe.lib.nixfile import NixFile
from nix_scribe.lib.option_block import ConfigFragment


def setup_test_hierarchy():
    root = NixFile("configuration")
    net = NixFile("networking")

    firewall = NixFile("firewall")
    fw_block = ConfigFragment("firewall")
    fw_asset = Asset("firewall.conf", "# firewall configuration\n")
    fw_block["config"] = fw_asset
    firewall.add_fragment(fw_block)

    nm = NixFile("networkmanager")
    nm_block = ConfigFragment("networkmanager")
    nm_block["enable"] = True
    nm.add_fragment(nm_block)

    return root, net, firewall, nm


def test_save_single_file():
    root, net, firewall, nm = setup_test_hierarchy()

    root.add_fragment(firewall.fragments[0])
    root.add_fragment(nm.fragments[0])

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        root.save(tmp_path, ModularizationLevel.SINGLE_FILE)

        assert (tmp_path / "configuration.nix").exists()
        assert (tmp_path / "firewall.conf").exists()
        assert (tmp_path / "firewall.conf").read_text() == "# firewall configuration\n"


def test_save_high_level():
    root, net, firewall, nm = setup_test_hierarchy()

    net.add_fragment(firewall.fragments[0])
    net.add_fragment(nm.fragments[0])
    root.add_import(net)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        root.save(tmp_path, ModularizationLevel.HIGH_LEVEL)

        assert (tmp_path / "configuration.nix").exists()
        assert (tmp_path / "networking.nix").exists()
        assert (tmp_path / "firewall.conf").exists()
        assert (tmp_path / "firewall.conf").read_text() == "# firewall configuration\n"


def test_save_component_level():
    root, net, firewall, nm = setup_test_hierarchy()

    net.add_import(firewall)
    net.add_import(nm)
    root.add_import(net)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        root.save(tmp_path, ModularizationLevel.COMPONENT_LEVEL)

        assert (tmp_path / "configuration.nix").exists()
        assert (tmp_path / "networking" / "default.nix").exists()
        assert (tmp_path / "networking" / "firewall.nix").exists()
        assert (tmp_path / "networking" / "networkmanager.nix").exists()
        assert (tmp_path / "networking" / "firewall.conf").exists()
        assert (
            tmp_path / "networking" / "firewall.conf"
        ).read_text() == "# firewall configuration\n"


def test_save_content_asset_modularized():
    root = NixFile("configuration")
    module = NixFile("packages")
    frag = ConfigFragment("system-packages")
    asset = Asset("packages.log", "audit report")
    frag.add_asset(asset)
    module.add_fragment(frag)
    root.add_import(module)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        root.save(tmp_path, ModularizationLevel.COMPONENT_LEVEL)

        assert (tmp_path / "configuration.nix").exists()
        assert (tmp_path / "packages.nix").exists()
        assert (tmp_path / "packages.log").exists()
        assert (tmp_path / "packages.log").read_text() == "audit report"
