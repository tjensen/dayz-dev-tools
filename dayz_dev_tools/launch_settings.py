import functools
import importlib.machinery
import logging
import types
import typing

from dayz_dev_tools import server_config


class LaunchSettings:
    _executable: str
    _config: str
    _profile: typing.Optional[str] = None
    _workshop_path: str
    _bundle_module: typing.Optional[types.ModuleType] = None
    _mods: typing.List[str]
    _server_mods: typing.List[str]
    _mission: typing.Optional[str] = None
    _bundles: typing.Dict[str, server_config.BundleConfig]

    def __init__(self, config: server_config.ServerConfig) -> None:
        self._executable = config.server_executable
        self._config = config.server_config
        self._profile = config.server_profile
        self._workshop_path = config.workshop_directory
        self._mods = []
        self._server_mods = []
        self._bundles = config.bundles

        try:
            loader = importlib.machinery.SourceFileLoader("bundles", config.bundle_path)
            self._bundle_module = loader.load_module()
        except FileNotFoundError:
            logging.debug(f"Unable to load bundles at: {config.bundle_path}", exc_info=True)

    def executable(self) -> str:
        return self._executable

    def set_executable(self, path: str) -> None:
        self._executable = path

    def config(self) -> str:
        return self._config

    def set_config(self, path: str) -> None:
        self._config = path

    def profile(self) -> typing.Optional[str]:
        return self._profile

    def set_profile(self, path: str) -> None:
        self._profile = path

    def workshop_directory(self) -> str:
        return self._workshop_path

    def set_workshop_directory(self, path: str) -> None:
        self._workshop_path = path

    def mods(self) -> typing.List[str]:
        return self._mods

    def add_mod(self, name: str) -> None:
        self._mods.append(name)

    def server_mods(self) -> typing.List[str]:
        return self._server_mods

    def add_server_mod(self, name: str) -> None:
        self._server_mods.append(name)

    def mission(self) -> typing.Optional[str]:
        return self._mission

    def set_mission(self, name: str) -> None:
        self._mission = name

    def load_bundle(self, name: str) -> None:
        bundle_fn = None

        if name in self._bundles:
            bundle_fn = functools.partial(_config_bundle, self._bundles[name])
        elif self._bundle_module is not None and hasattr(self._bundle_module, name):
            bundle_fn = getattr(self._bundle_module, name)

        if bundle_fn is None:
            raise Exception(f"No such bundle: {name}")

        bundle_fn(self)


def _config_bundle(bundle: server_config.BundleConfig, settings: LaunchSettings) -> None:
    if bundle.executable is not None:
        settings.set_executable(bundle.executable)

    if bundle.config is not None:
        settings.set_config(bundle.config)

    if bundle.profile is not None:
        settings.set_profile(bundle.profile)

    if bundle.workshop is not None:
        settings.set_workshop_directory(bundle.workshop)

    for mod in bundle.mods:
        settings.add_mod(mod)

    for mod in bundle.server_mods:
        settings.add_server_mod(mod)

    if bundle.mission is not None:
        settings.set_mission(bundle.mission)
