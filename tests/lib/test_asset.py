from pathlib import Path
from unittest.mock import MagicMock

import pytest

from nix_scribe.lib.asset import Asset, ContentAsset, FileAsset
from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.modularization import ModularizationLevel
from nix_scribe.lib.nixfile import NixFile
from nix_scribe.lib.option_block import ConfigFragment


def test_file_asset():
    asset = FileAsset("/etc/sample.conf", "sample.conf")
    assert isinstance(asset, Asset)
    assert asset.source_path == "/etc/sample.conf"
    assert asset.target_filename == "sample.conf"
    assert str(asset) == "./sample.conf"
    assert "source=/etc/sample.conf" in repr(asset)


def test_content_asset_text():
    asset = ContentAsset("packages.log", "report content")
    assert isinstance(asset, Asset)
    assert asset.target_filename == "packages.log"
    assert asset.content == "report content"
    assert str(asset) == "./packages.log"
    assert "content_len=14" in repr(asset)


def test_content_asset_bytes():
    asset = ContentAsset("icon.bin", b"\x00\x01\x02\x03")
    assert isinstance(asset, Asset)
    assert asset.target_filename == "icon.bin"
    assert asset.content == b"\x00\x01\x02\x03"
    assert str(asset) == "./icon.bin"
    assert "content_len=4" in repr(asset)


def test_asset_factory_methods():
    file_asset = Asset.from_file("/var/log/test.log", "test.log")
    assert isinstance(file_asset, FileAsset)
    assert file_asset.source_path == "/var/log/test.log"
    assert file_asset.target_filename == "test.log"

    content_asset = Asset.from_content("report.txt", "summary data")
    assert isinstance(content_asset, ContentAsset)
    assert content_asset.target_filename == "report.txt"
    assert content_asset.content == "summary data"


def test_asset_validation():
    with pytest.raises(ValueError, match="target_filename must not be empty"):
        ContentAsset("", "content")

    with pytest.raises(ValueError, match="target_filename must not be empty"):
        FileAsset("/src", "")

    with pytest.raises(ValueError, match="source_path must not be empty"):
        FileAsset("", "target.txt")


def test_asset_filename_sanitization():
    asset = Asset.from_content("invalid name/with spaces:and*chars?.txt", "data")
    assert "/" not in asset.target_filename
    assert " " not in asset.target_filename
    assert "*" not in asset.target_filename


def test_asset_equality_and_hash():
    c1 = Asset.from_content("report.txt", "data")
    c2 = ContentAsset("report.txt", "data")
    c3 = ContentAsset("report.txt", "different data")
    f1 = Asset.from_file("/src", "report.txt")
    f2 = FileAsset("/src", "report.txt")

    assert c1 == c2
    assert hash(c1) == hash(c2)
    assert c1 != c3
    assert c1 != f1
    assert f1 == f2
    assert hash(f1) == hash(f2)
    assert c1 != "not an asset"


def test_save_content_asset_text(tmp_path: Path):
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


def test_save_content_asset_bytes(tmp_path: Path):
    root = NixFile("configuration")
    fragment = ConfigFragment("system-packages")
    asset = Asset.from_content("data.bin", b"\xca\xfe\xba\xbe")
    fragment.add_asset(asset)
    root.add_fragment(fragment)

    mock_context = MagicMock(spec=SystemContext)
    root.save(tmp_path, ModularizationLevel.SINGLE_FILE, mock_context)

    bin_path = tmp_path / "data.bin"
    assert bin_path.exists()
    assert bin_path.read_bytes() == b"\xca\xfe\xba\xbe"
    mock_context.copy_file.assert_not_called()


def test_save_file_asset(tmp_path: Path):
    root = NixFile("configuration")
    fragment = ConfigFragment("grub")
    asset = Asset.from_file("/boot/grub/splash.png", "splash.png")
    fragment.add_asset(asset)
    root.add_fragment(fragment)

    mock_context = MagicMock(spec=SystemContext)
    root.save(tmp_path, ModularizationLevel.SINGLE_FILE, mock_context)

    mock_context.copy_file.assert_called_once_with(
        "/boot/grub/splash.png", tmp_path / "splash.png"
    )
