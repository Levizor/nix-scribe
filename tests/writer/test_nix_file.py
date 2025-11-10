import pytest

from src.writer.nixfile import NixFile
from src.writer.option_block import SimpleOptionBlock
from src.writer.value import raw


@pytest.fixture()
def file():
    return NixFile("configuration.nix")

def test_file_writing(file: NixFile):
    file.description = "Generated with nix-scribe test"

    file.imports = [raw("./hardware-configuration.nix")]

    firewall = SimpleOptionBlock(
        name = "networking/firewall",
        description = "sets up firewall options"
    )
    firewall["networking.firewall.enable"] = True
    firewall["networking.firewall.settings"] = {
        "something": True,
        "something.nothing": "Hello"
    }

    file.add_option_block(firewall)

    assert file.gettext() == """\
# Generated with nix-scribe test
{

  imports = [
    ./hardware-configuration.nix
  ];

  # sets up firewall options
  networking.firewall.enable = true;

  networking.firewall.settings = {
    something = true;
    something.nothing = "Hello";
  };

}\
"""
    file.add_option_block(SimpleOptionBlock(
        name = "networkmanager",
        description="NetworkManager configuration",
        data = {
            "networking.networkmanager": {
                "enable": True,
                "plugins": [raw("pkgs.networkmanager-openvpn")]
            }
        },
        arguments=["pkgs"]
    ))

    assert file.gettext() == """\
# Generated with nix-scribe test
{pkgs, ...}:
{

  imports = [
    ./hardware-configuration.nix
  ];

  # sets up firewall options
  networking.firewall.enable = true;

  networking.firewall.settings = {
    something = true;
    something.nothing = "Hello";
  };

  # NetworkManager configuration
  networking.networkmanager = {
    enable = true;
    plugins = [
      pkgs.networkmanager-openvpn
    ];
  };

}"""
