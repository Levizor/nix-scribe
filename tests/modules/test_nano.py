from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.programs.nano import NanoMapper, NanoScanner


def test_nano_scanner_basic(tmp_path):
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/nano").touch()

    context = SystemContext(tmp_path)
    scanner = NanoScanner()
    ir = scanner.scan(context)

    assert ir["enable"] is True
    assert "nanorc" not in ir


def test_nano_scanner_not_found(tmp_path):
    context = SystemContext(tmp_path)
    scanner = NanoScanner()
    ir = scanner.scan(context)

    assert "enable" not in ir


def test_nano_scanner_with_nanorc(tmp_path):
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/nano").touch()

    (tmp_path / "etc").mkdir()
    (tmp_path / "etc/nanorc").write_text("set tabsize 4")

    context = SystemContext(tmp_path)
    scanner = NanoScanner()
    ir = scanner.scan(context)

    assert ir["enable"] is True
    assert ir["nanorc"] == "set tabsize 4"


def test_nano_mapper_basic():
    mapper = NanoMapper()

    assert mapper.map({"enable": False}) is None

    block = mapper.map({"enable": True})
    assert block.data["programs.nano.enable"] is True
    assert "programs.nano.nanorc" not in block.data


def test_nano_mapper_with_custom_nanorc():
    mapper = NanoMapper()

    # custom nanorc
    ir = {"enable": True, "nanorc": "set tabsize 4"}
    block = mapper.map(ir)
    assert "programs.nano.enable" in block.data
    assert block.data["programs.nano.nanorc"] == "set tabsize 4"

    # default nanorc (or fully commented)
    ir_default = {
        "enable": True,
        "nanorc": """

# comment""",
    }
    block_default = mapper.map(ir_default)
    assert "programs.nano.enable" in block_default.data
    assert "programs.nano.nanorc" not in block_default.data
