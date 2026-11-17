import logging

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.parsers.pam import parse_pam
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.security.pam import Pam, PamService

logger = logging.getLogger(__name__)

pam = Scanner("security.pam")

PAM_DIR = "/etc/pam.d"
PAM_CONF = "/etc/pam.conf"


@pam.scanner()
def scan(context: SystemContext) -> Pam | None:
    has_pam_dir = context.path_exists(PAM_DIR)
    has_pam_conf = context.path_exists(PAM_CONF)

    if not has_pam_dir and not has_pam_conf:
        return None

    mod = Pam()
    reader = ConfigReader(context, parse_pam)

    if has_pam_dir:
        filenames = context.list_directory(PAM_DIR)
        for filename in filenames:
            service_path = f"{PAM_DIR}/{filename}"
            if not context.path_exists(service_path):
                continue
            service_config = reader.read_config(service_path)

            if service_config.get("has_ssh_agent_auth"):
                mod.ssh_agent_auth_enable = True
            if service_config.get("has_u2f"):
                mod.u2f_enable = True
            if service_config.get("has_yubico"):
                mod.yubico_enable = True
            if service_config.get("has_mount"):
                mod.mount_enable = True
            if service_config.get("has_howdy"):
                mod.howdy_enable = True

            svc = PamService(
                kwallet_enable=bool(service_config.get("has_kwallet")),
                u2f_enable=bool(service_config.get("has_u2f")),
                gnupg_enable=bool(service_config.get("has_gnupg")),
                howdy_enable=bool(service_config.get("has_howdy")),
                google_authenticator_enable=bool(
                    service_config.get("has_google_authenticator")
                ),
                duo_security_enable=bool(service_config.get("has_duo")),
            )
            if svc.to_dict():
                mod.services[filename] = svc

    if has_pam_conf:
        conf_config = reader.read_config(PAM_CONF)
        if conf_config.get("has_ssh_agent_auth"):
            mod.ssh_agent_auth_enable = True
        if conf_config.get("has_u2f"):
            mod.u2f_enable = True
        if conf_config.get("has_yubico"):
            mod.yubico_enable = True
        if conf_config.get("has_mount"):
            mod.mount_enable = True
        if conf_config.get("has_howdy"):
            mod.howdy_enable = True

    return mod
