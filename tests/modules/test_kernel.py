from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.modules.boot.kernel import kernel

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
    ir = kernel.scan(context)
    assert ir == {}


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
    ir = kernel.scan(context)

    assert ir["kernelModules"] == ["br_netfilter", "kvm_intel", "overlay", "tun"]
    assert ir["blacklistedKernelModules"] == ["nouveau", "pcspkr"]
    assert ir["extraModprobeConfig"] == "options kvm_intel nested=1"
    assert ir["kernelParams"] == ["quiet", "splash", "console=ttyS0,115200"]


def test_kernel_mapper():
    assert kernel.map
    mock_ir = {
        "kernelModules": ["tun"],
        "blacklistedKernelModules": ["nouveau"],
        "extraModprobeConfig": "options kvm_intel nested=1",
        "kernelParams": ["quiet"],
    }

    block = kernel.map(mock_ir)
    assert isinstance(block, ConfigFragment)
    data = block["boot"]
    assert data["kernelModules"] == ["tun"]
    assert data["blacklistedKernelModules"] == ["nouveau"]
    assert data["extraModprobeConfig"] == "options kvm_intel nested=1"
    assert data["kernelParams"] == ["quiet"]


def test_kernel_mapper_empty():
    assert kernel.map(None) is None
    assert kernel.map({}) is None
