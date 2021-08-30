import os
import unittest
from unittest import mock

from dayz_dev_tools import launch_settings
from dayz_dev_tools import run_server

from tests import helpers


main = helpers.call_main(run_server)


class TestMain(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        toml_patcher = mock.patch("toml.load", autospec=True)
        self.mock_toml_load = toml_patcher.start()
        self.addCleanup(toml_patcher.stop)

        settings_patcher = mock.patch(
            "dayz_dev_tools.launch_settings.LaunchSettings", autospec=True)
        self.mock_launch_settings_class = settings_patcher.start()
        self.addCleanup(settings_patcher.stop)

        run_server_patcher = mock.patch("dayz_dev_tools.run_server.run_server")
        self.mock_run_server = run_server_patcher.start()
        self.addCleanup(run_server_patcher.stop)

    def test_parses_arguments_and_runs_server(self) -> None:
        self.mock_toml_load.return_value = {
            "server": {
                "executable": "/path/to/server.exe",
                "bundles": "/path/to/custom-bundles.py"
            },
            "workshop": {
                "directory": "/path/to/workshop/dir"
            }
        }

        mock_launch_settings = self.mock_launch_settings_class.return_value

        main([
            "ignored"
        ])

        self.mock_toml_load.assert_called_once_with("server.toml")

        self.mock_launch_settings_class.assert_called_once_with(
            "/path/to/server.exe", "/path/to/workshop/dir", "/path/to/custom-bundles.py")

        self.mock_run_server.assert_called_once_with(mock_launch_settings)

    def test_uses_default_default_paths_when_not_specified_in_environment(self) -> None:
        self.mock_toml_load.side_effect = FileNotFoundError

        main([
            "ignored"
        ])

        self.mock_launch_settings_class.assert_called_once_with(
            r".\DayZServer_x64.exe",
            r"C:\Program Files (x86)\Steam\steamapps\common\DayZ\!Workshop",
            "bundles.py")

    def test_loads_bundles_when_specified_in_arguments(self) -> None:
        self.mock_toml_load.return_value = {}

        mock_launch_settings = self.mock_launch_settings_class.return_value

        main([
            "ignored",
            "bundle1",
            "bundle2",
            "bundle3"
        ])

        assert mock_launch_settings.load_bundle.call_count == 3

        mock_launch_settings.load_bundle.assert_has_calls([
            mock.call("bundle1"),
            mock.call("bundle2"),
            mock.call("bundle3")
        ])


class TestRunServer(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        popen_patcher = mock.patch("subprocess.Popen", autospec=True)
        self.mock_popen = popen_patcher.start()
        self.addCleanup(popen_patcher.stop)

    def test_runs_executable_with_provided_launch_settings(self) -> None:
        settings = launch_settings.LaunchSettings("server.exe", "workshopdir", "dont-care")

        run_server.run_server(settings)

        self.mock_popen.assert_called_once_with(["server.exe"])

    def test_runs_with_mod_parameter_when_mods_are_added(self) -> None:
        settings = launch_settings.LaunchSettings("server.exe", "workshopdir", "dont-care")
        settings.add_mod("some-mod")
        settings.add_mod(r"P:\path\to\mod")
        settings.add_mod("@Workshop Mod")

        run_server.run_server(settings)

        expected_workshop_mod_path = os.path.join("workshopdir", "@Workshop Mod")

        self.mock_popen.assert_called_once_with([
            "server.exe",
            f"-mod=some-mod;P:\\path\\to\\mod;{expected_workshop_mod_path}"
        ])

    def test_runs_with_servermod_parameter_when_server_mods_are_added(self) -> None:
        settings = launch_settings.LaunchSettings("server.exe", "workshopdir", "dont-care")
        settings.add_server_mod("some-mod")
        settings.add_server_mod(r"P:\path\to\mod")
        settings.add_server_mod("@Workshop Mod")

        run_server.run_server(settings)

        expected_workshop_mod_path = os.path.join("workshopdir", "@Workshop Mod")

        self.mock_popen.assert_called_once_with([
            "server.exe",
            f"-servermod=some-mod;P:\\path\\to\\mod;{expected_workshop_mod_path}"
        ])
