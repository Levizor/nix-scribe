from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.modules.programs.nano import nano


def test_nano_scanner_basic(tmp_path):
    assert nano.scan
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/nano").touch()

    context = SystemContext(tmp_path)
    ir = nano.scan(context)

    assert ir["enable"] is True
    assert "nanorc" not in ir


def test_nano_scanner_not_found(tmp_path):
    assert nano.scan
    context = SystemContext(tmp_path)
    ir = nano.scan(context)

    assert "enable" not in ir


def test_nano_scanner_with_nanorc(tmp_path):
    assert nano.scan
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/nano").touch()

    (tmp_path / "etc").mkdir()
    (tmp_path / "etc/nanorc").write_text("set tabsize 4")

    context = SystemContext(tmp_path)
    ir = nano.scan(context)

    assert ir["enable"] is True
    assert ir["nanorc"] == "set tabsize 4"


def test_nano_mapper_basic():
    assert nano.map
    mapper = nano.map

    assert mapper({"enable": False}) is None

    block = mapper({"enable": True})
    assert (
        isinstance(block, ConfigFragment) and block["programs.nano"]["enable"] is True
    )
    assert "nanorc" not in block["programs.nano"]


def test_nano_mapper_with_custom_nanorc():
    assert nano.map
    mapper = nano.map

    # custom nanorc
    ir = {"enable": True, "nanorc": "set tabsize 4"}
    block = mapper(ir)
    assert isinstance(block, ConfigFragment) and "enable" in block["programs.nano"]
    assert block["programs.nano"]["nanorc"] == "set tabsize 4"

    # default nanorc (or fully commented)
    ir_default = {
        "enable": True,
        "nanorc": """

# comment""",
    }
    block_default = mapper(ir_default)
    assert isinstance(block_default, ConfigFragment)
    assert "enable" in block_default["programs.nano"]
    assert "nanorc" not in block_default["programs.nano"]
