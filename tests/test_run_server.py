import os
import unittest
from unittest import mock

from dayz_dev_tools import launch_settings
from dayz_dev_tools import run_server
from dayz_dev_tools import server_config

from tests import helpers


main = helpers.call_main(run_server)


class TestMain(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.server_config = server_config.ServerConfig(
            server_executable="SERVER-EXECUTABLE",
            server_config="SERVER-CONFIG",
            workshop_directory="WORKSHOP-DIRECTORY",
            bundle_path="BUNDLE-PATH")

        load_patcher = mock.patch(
            "dayz_dev_tools.server_config.load", return_value=self.server_config)
        self.mock_server_config_load = load_patcher.start()
        self.addCleanup(load_patcher.stop)

        settings_patcher = mock.patch(
            "dayz_dev_tools.launch_settings.LaunchSettings", autospec=True)
        self.mock_launch_settings_class = settings_patcher.start()
        self.addCleanup(settings_patcher.stop)

        run_server_patcher = mock.patch("dayz_dev_tools.run_server.run_server")
        self.mock_run_server = run_server_patcher.start()
        self.addCleanup(run_server_patcher.stop)

    def test_parses_arguments_and_runs_server(self) -> None:
        mock_launch_settings = self.mock_launch_settings_class.return_value

        main([
            "ignored",
            "--config", "CONFIG-FILE"
        ])

        self.mock_server_config_load.assert_called_once_with("CONFIG-FILE")

        self.mock_launch_settings_class.assert_called_once_with(self.server_config)

        self.mock_run_server.assert_called_once_with(mock_launch_settings)

    def test_loads_default_config_filename_when_not_provided(self) -> None:
        mock_launch_settings = self.mock_launch_settings_class.return_value

        main([
            "ignored"
        ])

        self.mock_server_config_load.assert_called_once_with("server.toml")

        self.mock_launch_settings_class.assert_called_once_with(self.server_config)

        self.mock_run_server.assert_called_once_with(mock_launch_settings)

    def test_loads_bundles_when_specified_in_arguments(self) -> None:
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

        self.server_config = server_config.ServerConfig(
            server_executable="server.exe",
            server_config="config.cfg",
            workshop_directory="workshopdir",
            bundle_path="dont-care")

        popen_patcher = mock.patch("subprocess.Popen", autospec=True)
        self.mock_popen = popen_patcher.start()
        self.addCleanup(popen_patcher.stop)

    def test_runs_executable_with_provided_launch_settings(self) -> None:
        settings = launch_settings.LaunchSettings(self.server_config)

        run_server.run_server(settings)

        self.mock_popen.assert_called_once_with(["server.exe", "-config=config.cfg"])

    def test_runs_executable_with_profiles_parameter_when_profile_is_not_none(self) -> None:
        self.server_config.server_profile = "PROFILE"
        settings = launch_settings.LaunchSettings(self.server_config)

        run_server.run_server(settings)

        self.mock_popen.assert_called_once_with([
            "server.exe", "-config=config.cfg", "-profiles=PROFILE"
        ])

    def test_runs_with_mod_parameter_when_mods_are_added(self) -> None:
        settings = launch_settings.LaunchSettings(self.server_config)
        settings.add_mod("some-mod")
        settings.add_mod(r"P:\path\to\mod")
        settings.add_mod("@Workshop Mod")

        run_server.run_server(settings)

        expected_workshop_mod_path = os.path.join("workshopdir", "@Workshop Mod")

        self.mock_popen.assert_called_once_with([
            "server.exe",
            "-config=config.cfg",
            f"-mod=some-mod;P:\\path\\to\\mod;{expected_workshop_mod_path}"
        ])

    def test_runs_with_servermod_parameter_when_server_mods_are_added(self) -> None:
        settings = launch_settings.LaunchSettings(self.server_config)
        settings.add_server_mod("some-mod")
        settings.add_server_mod(r"P:\path\to\mod")
        settings.add_server_mod("@Workshop Mod")

        run_server.run_server(settings)

        expected_workshop_mod_path = os.path.join("workshopdir", "@Workshop Mod")

        self.mock_popen.assert_called_once_with([
            "server.exe",
            "-config=config.cfg",
            f"-servermod=some-mod;P:\\path\\to\\mod;{expected_workshop_mod_path}"
        ])
