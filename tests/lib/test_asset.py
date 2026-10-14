from pathlib import Path
from unittest.mock import MagicMock

import pytest

from nix_scribe.lib.asset import Asset
from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.modularization import ModularizationLevel
from nix_scribe.lib.nixfile import NixFile
from nix_scribe.lib.option_block import ConfigFragment


def test_asset_init_from_file():
    asset = Asset("/etc/sample.conf", "sample.conf")
    assert asset.source_path == "/etc/sample.conf"
    assert asset.target_filename == "sample.conf"
    assert asset.content is None
    assert str(asset) == "./sample.conf"
    assert "source=/etc/sample.conf" in repr(asset)


def test_asset_init_from_content():
    asset = Asset(target_filename="packages.log", content="report content")
    assert asset.source_path is None
    assert asset.target_filename == "packages.log"
    assert asset.content == "report content"
    assert str(asset) == "./packages.log"
    assert "content_len=14" in repr(asset)


def test_asset_factory_methods():
    file_asset = Asset.from_file("/var/log/test.log", "test.log")
    assert file_asset.source_path == "/var/log/test.log"
    assert file_asset.target_filename == "test.log"
    assert file_asset.content is None

    content_asset = Asset.from_content("report.txt", "summary data")
    assert content_asset.source_path is None
    assert content_asset.target_filename == "report.txt"
    assert content_asset.content == "summary data"


def test_asset_validation():
    with pytest.raises(ValueError, match="target_filename must not be empty"):
        Asset(target_filename="")

    with pytest.raises(ValueError, match="either source_path or content"):
        Asset(target_filename="test.txt")


def test_asset_filename_sanitization():
    asset = Asset.from_content("invalid name/with spaces:and*chars?.txt", "data")
    assert "/" not in asset.target_filename
    assert " " not in asset.target_filename
    assert "*" not in asset.target_filename


def test_asset_equality_and_hash():
    a1 = Asset.from_content("report.txt", "data")
    a2 = Asset.from_content("report.txt", "data")
    a3 = Asset.from_content("report.txt", "different data")
    f1 = Asset.from_file("/src", "report.txt")

    assert a1 == a2
    assert hash(a1) == hash(a2)
    assert a1 != a3
    assert a1 != f1
    assert a1 != "not an asset"


def test_save_content_asset_to_nixfile(tmp_path: Path):
    root = NixFile("configuration")
    fragment = ConfigFragment("system-packages")
    asset = Asset.from_content("packages.log", "package report data")
    fragment.add_asset(asset)
    root.add_fragment(fragment)

    mock_context = MagicMock(spec=SystemContext)
    root.save(tmp_path, ModularizationLevel.SINGLE_FILE, mock_context)

    log_path = tmp_path / "packages.log"
    assert log_path.exists()
    assert log_path.read_text(encoding="utf-8") == "package report data"
    mock_context.copy_file.assert_not_called()
