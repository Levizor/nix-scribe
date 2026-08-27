import logging
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.parsers.pam import parse_pam
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.lib.registry import Module

logger = logging.getLogger(__name__)

pam = Module("security.pam")

PAM_DIR = "/etc/pam.d"
PAM_CONF = "/etc/pam.conf"


@pam.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    has_pam_dir = context.path_exists(PAM_DIR)
    has_pam_conf = context.path_exists(PAM_CONF)

    if not has_pam_dir and not has_pam_conf:
        return {}

    ir: dict[str, Any] = {
        "sshAgentAuth": False,
        "u2f": False,
        "yubico": False,
        "mount": False,
        "howdy": False,
        "services": {},
    }

    reader = ConfigReader(context, parse_pam)

    if has_pam_dir:
        filenames = context.list_directory(PAM_DIR)
        for filename in filenames:
            service_path = f"{PAM_DIR}/{filename}"
            if not context.path_exists(service_path):
                continue
            service_config = reader.read_config(service_path)

            if service_config.get("has_ssh_agent_auth"):
                ir["sshAgentAuth"] = True
            if service_config.get("has_u2f"):
                ir["u2f"] = True
            if service_config.get("has_yubico"):
                ir["yubico"] = True
            if service_config.get("has_mount"):
                ir["mount"] = True
            if service_config.get("has_howdy"):
                ir["howdy"] = True

            service_info: dict[str, Any] = {}
            if service_config.get("has_kwallet"):
                service_info["kwallet"] = {"enable": True}
            if service_config.get("has_u2f"):
                service_info["u2f"] = {"enable": True}
            if service_config.get("has_gnupg"):
                service_info["gnupg"] = {"enable": True}
            if service_config.get("has_howdy"):
                service_info["howdy"] = {"enable": True}
            if service_config.get("has_google_authenticator"):
                service_info["googleAuthenticator"] = {"enable": True}
            if service_config.get("has_duo"):
                service_info["duoSecurity"] = {"enable": True}

            if service_info:
                ir["services"][filename] = service_info

    if has_pam_conf:
        conf_config = reader.read_config(PAM_CONF)
        if conf_config.get("has_ssh_agent_auth"):
            ir["sshAgentAuth"] = True
        if conf_config.get("has_u2f"):
            ir["u2f"] = True
        if conf_config.get("has_yubico"):
            ir["yubico"] = True
        if conf_config.get("has_mount"):
            ir["mount"] = True
        if conf_config.get("has_howdy"):
            ir["howdy"] = True

    return ir


@pam.mapper()
def map(ir: dict[str, Any]) -> ConfigFragment | None:
    if not ir:
        return None

    pam_config: dict[str, Any] = {}

    if ir.get("sshAgentAuth"):
        pam_config["sshAgentAuth.enable"] = True

    if ir.get("u2f"):
        pam_config["u2f.enable"] = True

    if ir.get("yubico"):
        pam_config["yubico.enable"] = True

    if ir.get("mount"):
        pam_config["mount.enable"] = True

    if ir.get("howdy"):
        pam_config["howdy.enable"] = True

    services = ir.get("services", {})
    if services:
        mapped_services = {}
        for sname, sinfo in services.items():
            if sinfo:
                mapped_services[sname] = sinfo
        if mapped_services:
            pam_config["services"] = mapped_services

    if not pam_config:
        return None

    return ConfigFragment(
        name="pam",
        description="PAM (Pluggable Authentication Modules) Configuration",
        data={"security.pam": pam_config},
    )
