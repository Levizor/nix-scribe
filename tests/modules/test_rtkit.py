from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.security.rtkit import RtkitMapper, RtkitScanner


def test_rtkit_scanner_service_found(tmp_path):
    (tmp_path / "usr/lib/systemd/system").mkdir(parents=True)
    service_file = tmp_path / "usr/lib/systemd/system/rtkit-daemon.service"
    service_file.write_text("""[Service]
ExecStart=/usr/libexec/rtkit-daemon --our-realtime-priority=29 --max-realtime-priority=28
""")

    context = SystemContext(tmp_path)
    scanner = RtkitScanner()
    ir = scanner.scan(context)

    assert ir["enable"] is True
    assert ir["args"] == ["--our-realtime-priority=29", "--max-realtime-priority=28"]


def test_rtkit_scanner_not_found(tmp_path):
    context = SystemContext(tmp_path)
    scanner = RtkitScanner()
    ir = scanner.scan(context)

    assert ir == {}


def test_rtkit_mapper():
    mapper = RtkitMapper()

    ir = {"enable": True}
    block = mapper.map(ir)
    assert block is not None
    assert block.data["security.rtkit"]["enable"] is True
    assert "args" not in block.data["security.rtkit"]

    ir_full = {"enable": True, "args": ["--arg1", "--arg2"]}
    block_full = mapper.map(ir_full)
    assert block_full is not None
    assert block_full.data["security.rtkit"]["enable"] is True
    assert block_full.data["security.rtkit"]["args"] == ["--arg1", "--arg2"]
