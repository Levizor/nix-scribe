import pytest

from nix_scribe.lib.registry import Module, ModuleRegistry


@pytest.fixture(autouse=True)
def reset_registry():
    ModuleRegistry().reset()
    yield
    ModuleRegistry().reset()


def test_singleton_instance():
    r1 = ModuleRegistry()
    r2 = ModuleRegistry()
    assert r1 is r2


def test_module_registration():
    registry = ModuleRegistry()
    mod = Module("test.dummy.mod")
    assert registry.get_all()["test.dummy.mod"] == mod


def test_parse_patterns():
    registry = ModuleRegistry()
    assert registry._parse_patterns(["boot.*", "security.pam,networking"]) == [
        "boot.*",
        "security.pam",
        "networking",
    ]
    assert registry._parse_patterns(None) == []


def test_module_filter_object():
    from nix_scribe.lib.registry import ModuleFilter

    spec = ModuleFilter.from_raw(
        enable=["boot.kernel"], disable=["networking.*"], only=["boot.*"]
    )
    assert spec.enable == ("boot.kernel",)
    assert spec.disable == ("networking.*",)
    assert spec.only == ("boot.*",)

    assert spec.is_active("boot.kernel", is_default_blacklisted=True) is True
    assert spec.is_active("networking", is_default_blacklisted=False) is False
    assert spec.is_active("programs.bash", is_default_blacklisted=False) is False


def test_is_match():
    registry = ModuleRegistry()
    assert registry.is_match("boot.loader.grub", ["boot.*"]) is True
    assert registry.is_match("boot.loader.grub", ["boot.loader.grub"]) is True
    assert registry.is_match("security.pam", ["boot.*"]) is False


def test_filter_modules_default_and_disable():
    registry = ModuleRegistry()
    mock_modules = {
        "boot.loader.grub": Module("boot.loader.grub"),
        "security.pam": Module("security.pam"),
        "experimental.feature": Module("experimental.feature"),
    }

    registry.default_blacklist = {"experimental.*"}

    filtered = registry.filter(modules=mock_modules)
    assert "boot.loader.grub" in filtered
    assert "security.pam" in filtered
    assert "experimental.feature" not in filtered

    filtered_enable = registry.filter(
        modules=mock_modules, enable=["experimental.feature"]
    )
    assert "experimental.feature" in filtered_enable

    filtered_disable = registry.filter(
        modules=mock_modules, disable=["boot.loader.grub"]
    )
    assert "boot.loader.grub" not in filtered_disable
    assert "security.pam" in filtered_disable

    filtered_only = registry.filter(modules=mock_modules, only=["security.*"])
    assert list(filtered_only.keys()) == ["security.pam"]


def test_validate_patterns_invalid_module():
    from nix_scribe.lib.registry import InvalidModuleError

    registry = ModuleRegistry()
    mock_modules = {"boot.loader.grub": Module("boot.loader.grub")}

    with pytest.raises(InvalidModuleError) as exc_info:
        registry.filter(modules=mock_modules, disable=["non_existent_module"])

    assert "non_existent_module" in str(exc_info.value)


def test_print_modules_table(capsys):
    from nix_scribe.lib.registry import print_modules_table

    print_modules_table()
    captured = capsys.readouterr()
    assert "Discovered Modules" in captured.out or "Module Name" in captured.out


def test_print_modules_tree(capsys):
    from nix_scribe.lib.registry import print_modules_tree

    print_modules_tree()
    captured = capsys.readouterr()
    assert "nix-scribe Modules" in captured.out or "Modules Tree" in captured.out
