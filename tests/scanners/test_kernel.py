from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.nixos.boot.kernel import Kernel
from nix_scribe.scanners.boot.kernel import kernel

MOCK_MODULES = """
# /etc/modules
tun
kvm_intel
"""

MOCK_MODULES_LOAD_D = """
overlay
br_netfilter
"""

MOCK_MODPROBE_D = """
blacklist nouveau
blacklist pcspkr
options kvm_intel nested=1
"""

MOCK_CMDLINE = "quiet splash console=ttyS0,115200"


def test_kernel_scanner_empty(tmp_path):
    context = SystemContext(tmp_path)
    assert kernel.scan(context) is None


def test_kernel_scanner_with_files(tmp_path):
    etc_dir = tmp_path / "etc"
    etc_dir.mkdir(parents=True)

    (etc_dir / "modules").write_text(MOCK_MODULES)

    mod_load_dir = etc_dir / "modules-load.d"
    mod_load_dir.mkdir()
    (mod_load_dir / "docker.conf").write_text(MOCK_MODULES_LOAD_D)

    modprobe_dir = etc_dir / "modprobe.d"
    modprobe_dir.mkdir()
    (modprobe_dir / "blacklist.conf").write_text(MOCK_MODPROBE_D)

    (etc_dir / "cmdline").write_text(MOCK_CMDLINE)

    context = SystemContext(tmp_path)
    mod = kernel.scan(context)

    assert isinstance(mod, Kernel)
    assert mod.kernelModules == ["br_netfilter", "kvm_intel", "overlay", "tun"]
    assert mod.blacklistedKernelModules == ["nouveau", "pcspkr"]
    assert mod.extraModprobeConfig == "options kvm_intel nested=1"
    assert mod.kernelParams == ["quiet", "splash", "console=ttyS0,115200"]

    fragment = mod.to_nix_fragment()
    data = fragment["boot"].value
    assert data["kernelModules"] == ["br_netfilter", "kvm_intel", "overlay", "tun"]
    assert data["blacklistedKernelModules"] == ["nouveau", "pcspkr"]
    assert data["extraModprobeConfig"] == "options kvm_intel nested=1"
    assert data["kernelParams"] == ["quiet", "splash", "console=ttyS0,115200"]
