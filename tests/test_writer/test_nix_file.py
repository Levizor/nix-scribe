import pytest

from nix_scribe.lib.nix_writer import raw
from nix_scribe.lib.nixfile import NixFile
from nix_scribe.lib.option_block import ConfigFragment


@pytest.fixture()
def file():
    return NixFile("configuration.nix")


def test_file_writing(file: NixFile):
    file.description = "Generated with nix-scribe test"

    file.imports = [raw("./hardware-configuration.nix")]

    firewall = ConfigFragment(
        name="networking/firewall", description="sets up firewall options"
    )
    firewall["networking.firewall.enable"] = True
    firewall["networking.firewall.settings"] = {
        "something": True,
        "something.nothing": "Hello",
    }

    file.add_fragment(firewall)

    assert (
        file.gettext()
        == """\
# Generated with nix-scribe test
{

  imports = [
    ./hardware-configuration.nix
  ];

  # --- networking/firewall: sets up firewall options ---
  networking.firewall.enable = true;

  networking.firewall.settings.something = true;
  networking.firewall.settings.something.nothing = "Hello";

}"""
    )
    file.add_fragment(
        ConfigFragment(
            name="networkmanager",
            description="NetworkManager configuration",
            data={
                "networking.networkmanager": {
                    "enable": True,
                    "plugins": [raw("pkgs.networkmanager-openvpn")],
                }
            },
            arguments={"pkgs"},
        )
    )

    assert (
        file.gettext()
        == """\
# Generated with nix-scribe test
{pkgs, ...}:
{

  imports = [
    ./hardware-configuration.nix
  ];

  # --- networking/firewall: sets up firewall options ---
  networking.firewall.enable = true;

  networking.firewall.settings.something = true;
  networking.firewall.settings.something.nothing = "Hello";

  # --- networkmanager: NetworkManager configuration ---
  networking.networkmanager.enable = true;
  networking.networkmanager.plugins = [
    pkgs.networkmanager-openvpn
  ];

}"""
    )


def test_config_fragment_claims():
    fragment = ConfigFragment(
        name="git",
        description="Git VCS",
        claims={"git", "git-lfs"},
    )
    assert fragment.claims == {"git", "git-lfs"}

    fragment.claim("git-gui", "tig")
    assert fragment.claims == {"git", "git-lfs", "git-gui", "tig"}

    empty_fragment = ConfigFragment(name="empty")
    assert empty_fragment.claims == set()
