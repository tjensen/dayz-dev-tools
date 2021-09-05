import functools
import importlib.machinery
import logging
import types
import typing

from dayz_dev_tools import server_config


class LaunchSettings:
    """Settings that determine what command line parameters to pass when running DayZ Server."""
    _executable: str
    _config: str
    _profile: typing.Optional[str] = None
    _workshop_path: str
    _bundle_module: typing.Optional[types.ModuleType] = None
    _mods: typing.List[str]
    _server_mods: typing.List[str]
    _mission: typing.Optional[str]
    _parameters: typing.List[str]
    _bundles: typing.Dict[str, server_config.BundleConfig]

    def __init__(self, config: server_config.ServerConfig) -> None:
        """Create a :class:`LaunchSettings` from a
        :class:`~dayz_dev_tools.server_config.ServerConfig`.

        :Parameters:
          - `config`: A :class:`~dayz_dev_tools.server_config.ServerConfig` instance returned by
            :meth:`dayz_dev_tools.server_config.load`.
        """
        self._executable = config.executable
        self._config = config.config
        self._profile = config.profile_directory
        self._workshop_path = config.workshop_directory
        self._mods = []
        self._server_mods = []
        self._mission = config.mission_directory
        self._parameters = config.parameters
        self._bundles = config.bundles

        try:
            loader = importlib.machinery.SourceFileLoader(
                "__dayz_server_bundles__", config.bundle_path)
            self._bundle_module = loader.load_module()
        except FileNotFoundError as error:
            logging.debug(f"Unable to load bundles at {config.bundle_path}: {error}")

    def executable(self) -> str:
        """Get the DayZ Server executable filename, usually ``.\\DayZServer_x64.exe``.

        :Returns:
          The DayZ Server executable filename.
        """
        return self._executable

    def set_executable(self, path: str) -> None:
        """Set the DayZ Server executable filename.

        :Parameters:
          - `path`: The DayZ Server executable filename.
        """
        self._executable = path

    def config(self) -> str:
        """Get the DayZ Server config filename, usually ``serverDZ.cfg``.

        :Returns:
          The DayZ Server config filename.
        """
        return self._config

    def set_config(self, path: str) -> None:
        """Set the DayZ Server config filename.

        :Parameters:
          - `path`: The DayZ Server config filename.
        """
        self._config = path

    def profile_directory(self) -> typing.Optional[str]:
        """Get the DayZ Server profile directory name.

        :Returns:
          The DayZ Server profile directory name, or ``None`` if it hasn't been set.

        .. note:: When the profile directory is unspecified, DayZ Server will usually use
           ``%LOCALAPPDATA%\\DayZ`` as the profile directory.
        """
        return self._profile

    def set_profile_directory(self, path: str) -> None:
        """Set the DayZ Server profile directory name.

        :Parameters:
          - `path`: The DayZ Server profile directory name.
        """
        self._profile = path

    def workshop_directory(self) -> str:
        """Get the DayZ (client) workshop directory name. This should normally be set to
        ``<DayZ Installation Directory>\\!Workshop``.

        :Returns:
          The DayZ workshop directory name.
        """
        return self._workshop_path

    def set_workshop_directory(self, path: str) -> None:
        """Set the DayZ (client) workshop directory name.

        :Parameters:
          - `path`: The DayZ workshop directory name.
        """
        self._workshop_path = path

    def mods(self) -> typing.List[str]:
        """Get the list of mods to load.

        :Returns:
          The list of mods to load.
        """
        return self._mods

    def add_mod(self, name: str) -> None:
        """Add a mod to be loaded.

        :Parameters:
          - `name`: The name of the mod to load. If the name starts with ``@``, it will be loaded
            from the DayZ workshop directory (see :meth:`LaunchSettings.workshop_directory`), else
            the name is expected to be the name of the directory containing the mod.
        """
        if name not in self._mods:
            self._mods.append(name)

    def server_mods(self) -> typing.List[str]:
        """Get the list of *server* mods to load.

        :Returns:
          The list of server mods to load.
        """
        return self._server_mods

    def add_server_mod(self, name: str) -> None:
        """Add a *server* mod to be loaded.

        :Parameters:
          - `name`: The name of the server mod to load. If the name starts with ``@``, it will be
            loaded from the DayZ workshop directory (see :meth:`LaunchSettings.workshop_directory`),
            else the name is expected to be the name of the directory containing the server mod.
        """
        if name not in self._server_mods:
            self._server_mods.append(name)

    def mission_directory(self) -> typing.Optional[str]:
        """Get the DayZ Server mission directory.

        :Returns:
          The DayZ Server mission directory, or ``None`` if the mission directory hasn't been set.

        .. note:: The mission directory is often configured in the DayZ Server config file (e.g.
           ``serverDZ.cfg``). See also :meth:`LaunchSettings.config`.
        """
        return self._mission

    def set_mission_directory(self, name: str) -> None:
        """Set the DayZ Server mission directory.

        :Parameters:
          - `name`: The DayZ Server mission directory name.
        """
        self._mission = name

    def parameters(self) -> typing.List[str]:
        """Get extra command line parameters to pass to DayZ Server.

        :Returns:
          The list of extra command line parameters to pass to DayZ Server.
        """
        return self._parameters

    def add_parameter(self, param: str) -> None:
        """Add extra parameter to pass on the DayZ Server command line.

        :Parameters:
          - `param`: The parameter to pass on the DayZ Server command line.
        """
        self._parameters.append(param)

    def load_bundle(self, name: str) -> None:
        """Load a bundle to configure DayZ Server launch settings.

        :Parameters:
          - `name`: The name of the bundle to load.

        This method will first try to find the bundle in the settings TOML file (e.g.
        ``server.toml``). If the bundle name does not exist there, then it will then try to find
        the bundle in the bundles Python module (e.g. ``bundles.py``).
        """
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

    if bundle.profile_directory is not None:
        settings.set_profile_directory(bundle.profile_directory)

    if bundle.workshop_directory is not None:
        settings.set_workshop_directory(bundle.workshop_directory)

    for mod in bundle.mods:
        settings.add_mod(mod)

    for mod in bundle.server_mods:
        settings.add_server_mod(mod)

    if bundle.mission_directory is not None:
        settings.set_mission_directory(bundle.mission_directory)

    for param in bundle.parameters:
        settings.add_parameter(param)
