from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.modules.security.rtkit import rtkit


def test_rtkit_scanner_service_found(tmp_path):
    assert rtkit.scan
    (tmp_path / "usr/lib/systemd/system").mkdir(parents=True)
    service_file = tmp_path / "usr/lib/systemd/system/rtkit-daemon.service"
    service_file.write_text("""[Service]
ExecStart=/usr/libexec/rtkit-daemon --our-realtime-priority=29 --max-realtime-priority=28
""")

    context = SystemContext(tmp_path)
    ir = rtkit.scan(context)

    assert ir["enable"] is True
    assert ir["args"] == ["--our-realtime-priority=29", "--max-realtime-priority=28"]


def test_rtkit_scanner_not_found(tmp_path):
    assert rtkit.scan
    context = SystemContext(tmp_path)
    ir = rtkit.scan(context)

    assert ir == {}


def test_rtkit_mapper():
    assert rtkit.map
    mapper = rtkit.map

    ir = {"enable": True}
    block = mapper(ir)
    assert block is not None
    assert (
        isinstance(block, SimpleOptionBlock)
        and block.data["security.rtkit"]["enable"] is True
    )
    assert "args" not in block.data["security.rtkit"]

    ir_full = {"enable": True, "args": ["--arg1", "--arg2"]}
    block_full = mapper(ir_full)
    assert isinstance(block_full, SimpleOptionBlock)
    assert block_full is not None
    assert block_full.data["security.rtkit"]["enable"] is True
    assert block_full.data["security.rtkit"]["args"] == ["--arg1", "--arg2"]
