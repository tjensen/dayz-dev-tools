import dataclasses
import logging

import toml


@dataclasses.dataclass
class ServerConfig:
    server_executable: str
    workshop_directory: str
    bundle_path: str


def load(filename: str) -> ServerConfig:
    try:
        config = toml.load(filename)
    except FileNotFoundError:
        logging.debug(f"Unable to read config file ({filename})", exc_info=True)
        config = {}

    config.setdefault("server", {})
    config["server"].setdefault("executable", r".\DayZServer_x64.exe")
    config["server"].setdefault("bundles", "bundles.py")
    config.setdefault("workshop", {})
    config["workshop"].setdefault(
        "directory", r"C:\Program Files (x86)\Steam\steamapps\common\DayZ\!Workshop")

    return ServerConfig(
        server_executable=config["server"]["executable"],
        workshop_directory=config["workshop"]["directory"],
        bundle_path=config["server"]["bundles"])
