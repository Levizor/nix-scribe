from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.nixos.security.rtkit import Rtkit
from nix_scribe.scanners.security.rtkit import rtkit


def test_rtkit_scanner_service_found(tmp_path):
    assert rtkit.scan
    (tmp_path / "usr/lib/systemd/system").mkdir(parents=True)
    service_file = tmp_path / "usr/lib/systemd/system/rtkit-daemon.service"
    service_file.write_text("""[Service]
ExecStart=/usr/libexec/rtkit-daemon --our-realtime-priority=29 --max-realtime-priority=28
""")

    context = SystemContext(tmp_path)
    mod = rtkit.scan(context)

    assert isinstance(mod, Rtkit)
    assert mod.enable is True
    assert mod.args == ["--our-realtime-priority=29", "--max-realtime-priority=28"]
    assert mod.resolve_claims() == {"rtkit"}

    fragment = mod.to_nix_fragment()
    data = fragment["security.rtkit"].value
    assert data["enable"] is True
    assert data["args"] == ["--our-realtime-priority=29", "--max-realtime-priority=28"]


def test_rtkit_scanner_not_found(tmp_path):
    assert rtkit.scan
    context = SystemContext(tmp_path)
    assert rtkit.scan(context) is None
