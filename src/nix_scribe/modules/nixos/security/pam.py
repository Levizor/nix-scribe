from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class PamService(NixModule):
    kwallet_enable: bool = option("kwallet.enable", default=False)
    u2f_enable: bool = option("u2f.enable", default=False)
    gnupg_enable: bool = option("gnupg.enable", default=False)
    howdy_enable: bool = option("howdy.enable", default=False)
    google_authenticator_enable: bool = option(
        "googleAuthenticator.enable", default=False
    )
    duo_security_enable: bool = option("duoSecurity.enable", default=False)


class Pam(NixModule, prefix="security.pam"):
    """PAM (Pluggable Authentication Modules) Configuration"""

    ssh_agent_auth_enable: bool = option("sshAgentAuth.enable", default=False)
    u2f_enable: bool = option("u2f.enable", default=False)
    yubico_enable: bool = option("yubico.enable", default=False)
    mount_enable: bool = option("mount.enable", default=False)
    howdy_enable: bool = option("howdy.enable", default=False)
    services: dict[str, PamService] = option(default={})
