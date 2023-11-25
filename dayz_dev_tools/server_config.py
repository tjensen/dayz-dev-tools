import dataclasses
import logging
import os
import platform
import typing

import pydantic
import tomli


if platform.system() == "Windows":
    DEFAULT_EXECUTABLE = os.path.join(".", "DayZServer_x64.exe")
    DEFAULT_WORKSHOP_DIRECTORY = "C:\\" + os.path.join(
        "Program Files (x86)", "Steam", "steamapps", "common", "DayZ", "!Workshop")
else:
    DEFAULT_EXECUTABLE = os.path.join(".", "DayZServer")
    DEFAULT_WORKSHOP_DIRECTORY = os.path.join(
        os.environ["HOME"], ".steam", "steamapps", "common", "DayZ", "!Workshop")


class _ServerConfig(pydantic.BaseModel):
    executable: str = DEFAULT_EXECUTABLE
    config: str = "serverDZ.cfg"
    directory: typing.Optional[str] = None
    profile_directory: typing.Optional[str] = None
    mission_directory: typing.Optional[str] = None
    parameters: typing.List[str] = pydantic.Field(default_factory=list)
    bundles: str = "bundles.py"


class _WorkshopConfig(pydantic.BaseModel):
    directory: str = DEFAULT_WORKSHOP_DIRECTORY


class _Bundle(pydantic.BaseModel):
    executable: typing.Optional[str] = None
    config: typing.Optional[str] = None
    directory: typing.Optional[str] = None
    profile_directory: typing.Optional[str] = None
    workshop_directory: typing.Optional[str] = None
    mission_directory: typing.Optional[str] = None
    mods: typing.Union[str, typing.List[str]] = pydantic.Field(default_factory=list)
    server_mods: typing.Union[str, typing.List[str]] = pydantic.Field(default_factory=list)
    parameters: typing.List[str] = pydantic.Field(default_factory=list)


class _Config(pydantic.BaseModel):
    server: _ServerConfig = pydantic.Field(default_factory=_ServerConfig)
    workshop: _WorkshopConfig = pydantic.Field(default_factory=_WorkshopConfig)
    bundle: typing.Dict[str, _Bundle] = pydantic.Field(default_factory=dict)


@dataclasses.dataclass
class BundleConfig:
    """Configuration file bundle settings."""
    #: DayZ Server executable filename override (optional)
    executable: typing.Optional[str] = None
    #: DayZ Server config filename override (optional)
    config: typing.Optional[str] = None
    #: Directory to switch to before running DayZ Server (optional)
    directory: typing.Optional[str] = None
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
    #: Directory to switch to before running DayZ Server (optional)
    directory: typing.Optional[str] = None
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
        with open(filename, "rb") as toml_file:
            config = _Config.model_validate(tomli.load(toml_file))
    except tomli.TOMLDecodeError as error:
        raise Exception(f"Configuration error in {filename}: {error}") from error
    except pydantic.ValidationError as error:
        loc = ".".join(str(ll) for ll in error.errors()[0]['loc'])
        inp = error.errors()[0]['input']
        msg = error.errors()[0]['msg']
        raise Exception(f"Configuration error at {loc}: {inp}: {msg}") from error
    except FileNotFoundError as error:
        logging.debug(f"Unable to read config file ({filename}): {error}")
        config = _Config()

    return ServerConfig(
        executable=config.server.executable,
        config=config.server.config,
        directory=config.server.directory,
        profile_directory=config.server.profile_directory,
        mission_directory=config.server.mission_directory,
        workshop_directory=config.workshop.directory,
        bundle_path=config.server.bundles,
        parameters=config.server.parameters,
        bundles={
            name: BundleConfig(
                executable=bundle.executable,
                config=bundle.config,
                directory=bundle.directory,
                profile_directory=bundle.profile_directory,
                workshop_directory=bundle.workshop_directory,
                mods=_parse_mods(bundle.mods),
                server_mods=_parse_mods(bundle.server_mods),
                mission_directory=bundle.mission_directory,
                parameters=bundle.parameters)
            for name, bundle in config.bundle.items()
        })
