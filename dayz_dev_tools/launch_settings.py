import importlib.machinery
import logging
import types
import typing


class LaunchSettings():
    _executable: str
    _workshop_path: str
    _bundle: typing.Optional[types.ModuleType] = None
    _mods: typing.List[str]
    _server_mods: typing.List[str]
    _mission: typing.Optional[str] = None

    def __init__(self, executable: str, workshop_path: str, bundle_path: str) -> None:
        self._executable = executable
        self._workshop_path = workshop_path
        self._mods = []
        self._server_mods = []

        try:
            loader = importlib.machinery.SourceFileLoader("bundles", bundle_path)
            self._bundle = loader.load_module()
        except FileNotFoundError:
            logging.debug(f"Unable to load bundles at: {bundle_path}", exc_info=True)

    def executable(self) -> str:
        return self._executable

    def set_executable(self, path: str) -> None:
        self._executable = path

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
        if self._bundle is None or not hasattr(self._bundle, name):
            raise Exception(f"No such bundle: {name}")

        getattr(self._bundle, name)(self)
