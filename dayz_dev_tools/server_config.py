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
                "profile": {"type": "string"},
                "mission": {"type": "string"},
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
        "profile": {"type": "string"},
        "workshop": {"type": "string"},
        "mods": {
            "oneOf": [
                {"type": "string"},
                {
                    "type": "array",
                    "items": {"type": "string"}
                }
            ]
        },
        "server_mods": {
            "oneOf": [
                {"type": "string"},
                {
                    "type": "array",
                    "items": {"type": "string"}
                }
            ]
        },
        "mission": {"type": "string"}
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
    config["server"].setdefault("bundles", "bundles.py")
    config.setdefault("workshop", {})
    config["workshop"].setdefault(
        "directory", r"C:\Program Files (x86)\Steam\steamapps\common\DayZ\!Workshop")
    config.setdefault("bundle", {})

    for name, bundle in config["bundle"].items():
        _validate(bundle, BUNDLE_SCHEMA, prefix=f"bundle.{name}.")
        bundle.setdefault("mods", [])
        bundle.setdefault("server_mods", [])

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
                mods=_parse_mods(bundle["mods"]),
                server_mods=_parse_mods(bundle["server_mods"]),
                mission=bundle.get("mission"))
            for name, bundle in config.get("bundle", {}).items()
        })
