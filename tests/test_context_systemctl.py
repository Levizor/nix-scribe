from __future__ import annotations

from pathlib import Path

import pytest

from nix_scribe.lib.context import SystemContext

GENERIC_SYSTEM_ROOT = Path(__file__).parent / "systems/generic"


@pytest.fixture
def system_context():
    return SystemContext(GENERIC_SYSTEM_ROOT)


def test_systemctl_is_enabled_via_alias(system_context):
    """Test service enabled via a base-directory symlink alias."""
    assert system_context.systemctl.is_enabled("sddm") is True
    assert system_context.systemctl.is_enabled("sddm.service") is True


def test_systemctl_is_enabled_via_wants(system_context):
    """Test service enabled via a target .wants directory."""
    assert system_context.systemctl.is_enabled("nginx") is True


def test_systemctl_template_service(system_context):
    """Test an instantiated template service."""
    assert system_context.systemctl.exists("getty@tty1") is True
    assert system_context.systemctl.is_enabled("getty@tty1.service") is True


def test_systemctl_masked_service(system_context):
    """Test that a masked service is treated as non-existent and disabled."""
    assert system_context.systemctl.exists("bluetooth") is False
    assert system_context.systemctl.is_enabled("bluetooth") is False


def test_systemctl_is_disabled(system_context):
    """Test a service that exists on disk but has no enablement symlinks."""
    assert system_context.systemctl.exists("gdm") is True
    assert system_context.systemctl.is_enabled("gdm") is False
    assert system_context.systemctl.is_disabled("gdm") is True


def test_systemctl_nonexistent(system_context):
    """Test a service that does not exist anywhere."""
    assert system_context.systemctl.exists("nonexistent-service") is False
    assert system_context.systemctl.is_enabled("nonexistent-service") is False
    assert system_context.systemctl.is_disabled("nonexistent-service") is False
