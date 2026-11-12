from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class PamService(NixModule):
    kwallet_enable: bool = option("kwallet.enable")
    u2f_enable: bool = option("u2f.enable")
    gnupg_enable: bool = option("gnupg.enable")
    howdy_enable: bool = option("howdy.enable")
    google_authenticator_enable: bool = option("googleAuthenticator.enable")
    duo_security_enable: bool = option("duoSecurity.enable")


class Pam(NixModule, prefix="security.pam"):
    """PAM (Pluggable Authentication Modules) Configuration"""

    ssh_agent_auth_enable: bool = option("sshAgentAuth.enable")
    u2f_enable: bool = option("u2f.enable")
    yubico_enable: bool = option("yubico.enable")
    mount_enable: bool = option("mount.enable")
    howdy_enable: bool = option("howdy.enable")
    services: dict[str, PamService] = option()
