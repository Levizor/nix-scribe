from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.nixos.virtualisation.virtualisation import Virtualisation
from nix_scribe.scanners.virtualisation.virtualisation import virtualisation


def test_virtualisation_scanner(tmp_path):
    context = SystemContext(tmp_path)
    mod = virtualisation.scan(context)

    assert isinstance(mod, Virtualisation)
    assert mod.virtualisation is not None
    assert mod.virtualisation.cores == 4
    assert mod.virtualisation.memorySize == 8128
    assert mod.virtualisation.diskSize == 10240

    fragment = mod.to_nix_fragment()
    data = fragment["virtualisation.vmVariant"].value["virtualisation"]
    assert data["cores"] == 4
    assert data["memorySize"] == 8128
    assert data["diskSize"] == 10240
    assert "-cpu host" in data["qemu.options"]
