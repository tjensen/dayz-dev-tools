import dataclasses
import logging
import typing

import jsonschema
import toml


CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "server": {
            "type": "object",
            "properties": {
                "executable": {"type": "string"},
                "config": {"type": "string"},
                "profile_directory": {"type": "string"},
                "mission_directory": {"type": "string"},
                "parameters": {"type": "array", "items": {"type": "string"}},
                "bundles": {"type": "string"}
            }
        },
        "workshop": {
            "type": "object",
            "properties": {
                "directory": {"type": "string"}
            }
        }
    }
}

BUNDLE_SCHEMA = {
    "type": "object",
    "properties": {
        "executable": {"type": "string"},
        "config": {"type": "string"},
        "profile_directory": {"type": "string"},
        "workshop_directory": {"type": "string"},
        "mission_directory": {"type": "string"},
        "mods": {
            "oneOf": [
                {"type": "string"},
                {"type": "array", "items": {"type": "string"}}
            ]
        },
        "server_mods": {
            "oneOf": [
                {"type": "string"},
                {"type": "array", "items": {"type": "string"}}
            ]
        },
        "parameters": {"type": "array", "items": {"type": "string"}},
    }
}


def _validate(
    instance: typing.MutableMapping[str, typing.Any],
    schema: typing.Any,
    *, prefix: str = ""
) -> typing.MutableMapping[str, typing.Any]:
    try:
        jsonschema.validate(instance, schema)

        return instance
    except jsonschema.ValidationError as error:
        path = ".".join(error.absolute_path)
        raise Exception(f"Configuration error at {prefix}{path}: {error.message}") from error


@dataclasses.dataclass
class BundleConfig:
    """Configuration file bundle settings."""
    #: DayZ Server executable filename override (optional)
    executable: typing.Optional[str] = None
    #: DayZ Server config filename override (optional)
    config: typing.Optional[str] = None
    #: DayZ Server profile directory name override (optional)
    profile_directory: typing.Optional[str] = None
    #: DayZ workshop directory name override (optional)
    workshop_directory: typing.Optional[str] = None
    #: DayZ mod list to add
    mods: typing.List[str] = dataclasses.field(default_factory=list)
    #: DayZ server mod list to add
    server_mods: typing.List[str] = dataclasses.field(default_factory=list)
    #: DayZ Server mission directory name override (optional)
    mission_directory: typing.Optional[str] = None
    #: Extra server command line parameters to add
    parameters: typing.List[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class ServerConfig:
    """Configuration file settings."""
    #: DayZ Server executable filename
    executable: str
    #: DayZ Server config filename
    config: str
    #: Filename of the bundles Python module
    bundle_path: str
    #: DayZ workshop directory name
    workshop_directory: str
    #: Configuration file bundles, by name (see :class:`dayz_dev_tools.server_config.BundleConfig`)
    bundles: typing.Dict[str, BundleConfig]
    #: DayZ Server profile directory name (optional)
    profile_directory: typing.Optional[str] = None
    #: DayZ Server mission directory name (optional)
    mission_directory: typing.Optional[str] = None
    #: Extra server command line parameters to add
    parameters: typing.List[str] = dataclasses.field(default_factory=list)


def _parse_mods(mods: typing.Union[str, typing.List[str]]) -> typing.List[str]:
    if isinstance(mods, str):
        return mods.split(";")

    return mods


def load(filename: str) -> ServerConfig:
    """Read a TOML-syntax DayZ Server configuration file.

    :Parameters:
      - `filename`: The name of the configuration file to read (e.g. ``server.toml``)

    :Returns:
      A :class:`~dayz_dev_tools.server_config.ServerConfig`.
    """
    try:
        config = _validate(toml.load(filename), CONFIG_SCHEMA)
    except toml.TomlDecodeError as error:
        raise Exception(
            # TODO: Figure out why mypy thinks TomlDecodeError doesn't have lineno, colno, and msg
            f"Configuration error in {filename}:{error.lineno}:{error.colno}"  # type: ignore
            f": {error.msg}") \
            from error
    except FileNotFoundError as error:
        logging.debug(f"Unable to read config file ({filename}): {error}")
        config = {}

    config.setdefault("server", {})
    config["server"].setdefault("executable", r".\DayZServer_x64.exe")
    config["server"].setdefault("config", "serverDZ.cfg")
    config["server"].setdefault("parameters", [])
    config["server"].setdefault("bundles", "bundles.py")
    config.setdefault("workshop", {})
    config["workshop"].setdefault(
        "directory", r"C:\Program Files (x86)\Steam\steamapps\common\DayZ\!Workshop")
    config.setdefault("bundle", {})

    for name, bundle in config["bundle"].items():
        _validate(bundle, BUNDLE_SCHEMA, prefix=f"bundle.{name}.")
        bundle.setdefault("mods", [])
        bundle.setdefault("server_mods", [])
        bundle.setdefault("parameters", [])

    return ServerConfig(
        executable=config["server"]["executable"],
        config=config["server"]["config"],
        profile_directory=config["server"].get("profile_directory"),
        mission_directory=config["server"].get("mission_directory"),
        workshop_directory=config["workshop"]["directory"],
        bundle_path=config["server"]["bundles"],
        parameters=config["server"]["parameters"],
        bundles={
            name: BundleConfig(
                executable=bundle.get("executable"),
                config=bundle.get("config"),
                profile_directory=bundle.get("profile_directory"),
                workshop_directory=bundle.get("workshop_directory"),
                mods=_parse_mods(bundle["mods"]),
                server_mods=_parse_mods(bundle["server_mods"]),
                mission_directory=bundle.get("mission_directory"),
                parameters=bundle["parameters"])
            for name, bundle in config.get("bundle", {}).items()
        })
