from nix_scribe.lib.parsers.pacman_log import (
    extract_explicit_packages_from_log,
    parse_pacman_cmdline,
    parse_pacman_log_cmdlines,
)

SAMPLE_PACMAN_LOG = """[2026-10-25T00:03:49+0000] [ALPM] installed filesystem (2025.10.12-1)
[2026-10-25T00:03:55+0000] [ALPM] installed base (3-3)
[2026-10-25T00:03:55+0000] [ALPM] transaction completed
[2026-10-31T19:59:16+0000] [PACMAN] Running 'pacman -Sy --noconfirm curl fastfetch'
[2026-10-31T19:59:16+0000] [PACMAN] synchronizing package lists
[2026-10-31T19:59:18+0000] [ALPM] transaction started
[2026-10-31T19:59:18+0000] [ALPM] reinstalled curl (8.23.0-1)
[2026-10-31T19:59:18+0000] [ALPM] installed yyjson (0.13.0-1)
[2026-10-31T19:59:18+0000] [ALPM] installed fastfetch (2.70.0-1)
[2026-10-31T19:59:18+0000] [ALPM] transaction completed
"""


def test_parse_pacman_log_cmdlines():
    cmdlines = parse_pacman_log_cmdlines(SAMPLE_PACMAN_LOG)
    assert len(cmdlines) == 1
    assert cmdlines[0] == (
        "2026-10-31T19:59:16+0000",
        "pacman -Sy --noconfirm curl fastfetch",
    )


def test_parse_pacman_cmdline_install():
    action, pkgs = parse_pacman_cmdline("pacman -Sy --noconfirm curl fastfetch")
    assert action == "install"
    assert pkgs == {"curl", "fastfetch"}


def test_parse_pacman_cmdline_with_wrappers_and_repo_prefix():
    action, pkgs = parse_pacman_cmdline("sudo pacman -S extra/vim core/systemd")
    assert action == "install"
    assert pkgs == {"vim", "systemd"}


def test_parse_pacman_cmdline_aur_helpers():
    action, pkgs = parse_pacman_cmdline("yay -S ripgrep bat")
    assert action == "install"
    assert pkgs == {"ripgrep", "bat"}

    action, pkgs = parse_pacman_cmdline("paru -S --needed fd")
    assert action == "install"
    assert pkgs == {"fd"}


def test_parse_pacman_cmdline_remove():
    action, pkgs = parse_pacman_cmdline("pacman -Rns curl fastfetch")
    assert action == "remove"
    assert pkgs == {"curl", "fastfetch"}

    action, pkgs = parse_pacman_cmdline("pacman -Rs htop")
    assert action == "remove"
    assert pkgs == {"htop"}


def test_parse_pacman_cmdline_upgrade_package_file():
    action, pkgs = parse_pacman_cmdline(
        "pacman -U /tmp/htop-3.3.0-1-x86_64.pkg.tar.zst"
    )
    assert action == "install"
    assert pkgs == {"htop"}


def test_parse_pacman_cmdline_database_asdeps_asexplicit():
    action, pkgs = parse_pacman_cmdline("pacman -D --asdeps ripgrep")
    assert action == "asdeps"
    assert pkgs == {"ripgrep"}

    action, pkgs = parse_pacman_cmdline("pacman -D --asexplicit ripgrep")
    assert action == "install"
    assert pkgs == {"ripgrep"}


def test_parse_pacman_cmdline_sync_asdeps():
    action, pkgs = parse_pacman_cmdline("pacman -S --asdeps libsecret")
    assert action == "asdeps"
    assert pkgs == {"libsecret"}


def test_parse_pacman_cmdline_options_with_args():
    action, pkgs = parse_pacman_cmdline(
        "pacman -S --config /etc/pacman.conf --cachedir /var/cache --overwrite '*' bash"
    )
    assert action == "install"
    assert pkgs == {"bash"}


def test_parse_pacman_cmdline_bootstrap():
    action, pkgs = parse_pacman_cmdline("pacman -r /mnt -Sy base linux")
    assert action == "bootstrap"
    assert pkgs == {"base", "linux"}

    action, pkgs = parse_pacman_cmdline("pacman --sysroot /mnt -Sy base linux")
    assert action == "bootstrap"
    assert pkgs == {"base", "linux"}

    action, pkgs = parse_pacman_cmdline("pacstrap -K /mnt base linux-firmware")
    assert action == "bootstrap"
    assert pkgs == {"base", "linux-firmware"}


def test_parse_pacman_cmdline_query():
    action, pkgs = parse_pacman_cmdline("pacman -Qdt")
    assert action is None
    assert pkgs == set()


def test_extract_explicit_packages_from_log():
    log_content = """[2026-10-25T10:00:00+0000] [PACMAN] Running 'pacman -S pkg1 pkg2 pkg3'
[2026-10-26T10:00:00+0000] [PACMAN] Running 'pacman -R pkg1'
[2026-10-27T10:00:00+0000] [PACMAN] Running 'pacman -D --asdeps pkg2'
[2026-10-28T10:00:00+0000] [PACMAN] Running 'pacman -S pkg4'
"""
    explicit = extract_explicit_packages_from_log(log_content)
    assert explicit == {"pkg3", "pkg4"}
