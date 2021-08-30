import dataclasses
import logging
import typing

import toml


@dataclasses.dataclass
class ServerConfig:
    server_executable: str
    server_config: str
    bundle_path: str
    workshop_directory: str
    server_profile: typing.Optional[str] = None


def load(filename: str) -> ServerConfig:
    try:
        config = toml.load(filename)
    except FileNotFoundError:
        logging.debug(f"Unable to read config file ({filename})", exc_info=True)
        config = {}

    config.setdefault("server", {})
    config["server"].setdefault("executable", r".\DayZServer_x64.exe")
    config["server"].setdefault("config", "serverDZ.cfg")
    config["server"].setdefault("bundles", "bundles.py")
    config.setdefault("workshop", {})
    config["workshop"].setdefault(
        "directory", r"C:\Program Files (x86)\Steam\steamapps\common\DayZ\!Workshop")

    return ServerConfig(
        server_executable=config["server"]["executable"],
        server_config=config["server"]["config"],
        server_profile=config["server"].get("profile"),
        workshop_directory=config["workshop"]["directory"],
        bundle_path=config["server"]["bundles"])
