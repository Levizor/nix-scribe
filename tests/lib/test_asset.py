from pathlib import Path

import pytest

from nix_scribe.lib.asset import Asset
from nix_scribe.lib.modularization import ModularizationLevel
from nix_scribe.lib.nixfile import NixFile
from nix_scribe.lib.option_block import ConfigFragment


def test_asset_text():
    asset = Asset("packages.log", "report content")
    assert asset.target_filename == "packages.log"
    assert asset.content == "report content"
    assert str(asset) == "./packages.log"
    assert "content_len=14" in repr(asset)


def test_asset_bytes():
    asset = Asset("icon.bin", b"\x00\x01\x02\x03")
    assert asset.target_filename == "icon.bin"
    assert asset.content == b"\x00\x01\x02\x03"
    assert str(asset) == "./icon.bin"
    assert "content_len=4" in repr(asset)


def test_asset_validation():
    with pytest.raises(ValueError, match="target_filename must not be empty"):
        Asset("", "content")


def test_asset_filename_sanitization():
    asset = Asset("invalid name/with spaces:and*chars?.txt", "data")
    assert "/" not in asset.target_filename
    assert " " not in asset.target_filename
    assert "*" not in asset.target_filename


def test_asset_equality_and_hash():
    a1 = Asset("report.txt", "data")
    a2 = Asset("report.txt", "data")
    a3 = Asset("report.txt", "different data")
    a4 = Asset("other.txt", "data")

    assert a1 == a2
    assert hash(a1) == hash(a2)
    assert a1 != a3
    assert a1 != a4
    assert a1 != "not an asset"


def test_save_asset_text(tmp_path: Path):
    root = NixFile("configuration")
    fragment = ConfigFragment("system-packages")
    asset = Asset("packages.log", "package report data")
    fragment.add_asset(asset)
    root.add_fragment(fragment)

    root.save(tmp_path, ModularizationLevel.SINGLE_FILE)

    log_path = tmp_path / "packages.log"
    assert log_path.exists()
    assert log_path.read_text(encoding="utf-8") == "package report data"


def test_save_asset_bytes(tmp_path: Path):
    root = NixFile("configuration")
    fragment = ConfigFragment("system-packages")
    asset = Asset("data.bin", b"\xca\xfe\xba\xbe")
    fragment.add_asset(asset)
    root.add_fragment(fragment)

    root.save(tmp_path, ModularizationLevel.SINGLE_FILE)

    bin_path = tmp_path / "data.bin"
    assert bin_path.exists()
    assert bin_path.read_bytes() == b"\xca\xfe\xba\xbe"
