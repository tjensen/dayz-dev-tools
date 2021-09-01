import dataclasses
import logging
import typing

import toml


@dataclasses.dataclass
class BundleConfig:
    executable: typing.Optional[str] = None
    config: typing.Optional[str] = None
    profile: typing.Optional[str] = None
    workshop: typing.Optional[str] = None
    mods: typing.List[str] = dataclasses.field(default_factory=list)
    server_mods: typing.List[str] = dataclasses.field(default_factory=list)
    mission: typing.Optional[str] = None


@dataclasses.dataclass
class ServerConfig:
    server_executable: str
    server_config: str
    bundle_path: str
    workshop_directory: str
    bundles: typing.Dict[str, BundleConfig]
    server_profile: typing.Optional[str] = None
    mission: typing.Optional[str] = None


def _parse_mods(mods: typing.Union[str, typing.List[str]]) -> typing.List[str]:
    if isinstance(mods, str):
        return mods.split(";")

    return mods


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
        mission=config["server"].get("mission"),
        workshop_directory=config["workshop"]["directory"],
        bundle_path=config["server"]["bundles"],
        bundles={
            name: BundleConfig(
                executable=bundle.get("executable"),
                config=bundle.get("config"),
                profile=bundle.get("profile"),
                workshop=bundle.get("workshop"),
                mods=_parse_mods(bundle.get("mods", [])),
                server_mods=_parse_mods(bundle.get("server_mods", [])),
                mission=bundle.get("mission"))
            for name, bundle in config.get("bundle", {}).items()
        })
