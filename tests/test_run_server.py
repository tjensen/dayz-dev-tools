import logging
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
            bundle_path="BUNDLE-PATH",
            bundles={})

        basic_config_patcher = mock.patch("logging.basicConfig")
        self.mock_basic_config = basic_config_patcher.start()
        self.addCleanup(basic_config_patcher.stop)

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

    def test_load_default_config_and_runs_server(self) -> None:
        mock_launch_settings = self.mock_launch_settings_class.return_value

        main([
            "ignored"
        ])

        self.mock_basic_config.assert_called_once_with(
            format="%(asctime)s %(levelname)s:%(module)s:%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S%z",
            level=logging.INFO)

        self.mock_server_config_load.assert_called_once_with("server.toml")

        self.mock_launch_settings_class.assert_called_once_with(self.server_config)

        self.mock_run_server.assert_called_once_with(mock_launch_settings, wait=True)

    def test_loads_config_filename_from_arguments_when_provided(self) -> None:
        main([
            "ignored",
            "--config", "CONFIG-FILE"
        ])

        self.mock_server_config_load.assert_called_once_with("CONFIG-FILE")

    def test_runs_server_without_waiting_when_specified_in_arguments(self) -> None:
        mock_launch_settings = self.mock_launch_settings_class.return_value

        main([
            "ignored",
            "--no-wait"
        ])

        self.mock_run_server.assert_called_once_with(mock_launch_settings, wait=False)

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
            bundle_path="dont-care",
            bundles={})

        popen_patcher = mock.patch("subprocess.Popen", autospec=True)
        self.mock_popen = popen_patcher.start()
        self.addCleanup(popen_patcher.stop)

        self.mock_popen.return_value.pid = 42

        copy_keys_patcher = mock.patch("dayz_dev_tools.keys.copy_keys")
        self.mock_copy_keys = copy_keys_patcher.start()
        self.addCleanup(copy_keys_patcher.stop)

        newest_patcher = mock.patch("dayz_dev_tools.script_logs.newest")
        self.mock_newest = newest_patcher.start()
        self.addCleanup(newest_patcher.stop)

        sleep_patcher = mock.patch("time.sleep")
        self.mock_sleep = sleep_patcher.start()
        self.addCleanup(sleep_patcher.stop)

    def test_runs_executable_with_provided_launch_settings(self) -> None:
        settings = launch_settings.LaunchSettings(self.server_config)

        run_server.run_server(settings, wait=False)

        self.mock_popen.assert_called_once_with(["server.exe", "-config=config.cfg"])

        self.mock_newest.assert_not_called()

    def test_runs_executable_with_profiles_parameter_when_profile_is_not_none(self) -> None:
        self.server_config.server_profile = "PROFILE"
        settings = launch_settings.LaunchSettings(self.server_config)

        run_server.run_server(settings, wait=False)

        self.mock_popen.assert_called_once_with([
            "server.exe", "-config=config.cfg", "-profiles=PROFILE"
        ])

    def test_runs_executable_with_mission_parameter_when_mission_is_not_none(self) -> None:
        self.server_config.mission = "MISSION"
        settings = launch_settings.LaunchSettings(self.server_config)

        run_server.run_server(settings, wait=False)

        self.mock_popen.assert_called_once_with([
            "server.exe", "-config=config.cfg", "-mission=MISSION"
        ])

    def test_copies_keys_and_runs_with_mod_parameter_when_mods_are_added(self) -> None:
        settings = launch_settings.LaunchSettings(self.server_config)
        settings.add_mod("some-mod")
        settings.add_mod(r"P:\path\to\mod")
        settings.add_mod("@Workshop Mod")

        run_server.run_server(settings, wait=False)

        expected_workshop_mod_path = os.path.join("workshopdir", "@Workshop Mod")

        self.mock_copy_keys.assert_has_calls([
            mock.call(os.path.join("some-mod", "keys"), "keys"),
            mock.call(os.path.join(r"P:\path\to\mod", "keys"), "keys"),
            mock.call(os.path.join(expected_workshop_mod_path, "keys"), "keys")
        ])

        self.mock_popen.assert_called_once_with([
            "server.exe",
            "-config=config.cfg",
            f"-mod=some-mod;P:\\path\\to\\mod;{expected_workshop_mod_path}"
        ])

    def test_copies_keys_and_runs_with_servermod_parameter_when_server_mods_are_added(self) -> None:
        settings = launch_settings.LaunchSettings(self.server_config)
        settings.add_server_mod("some-mod")
        settings.add_server_mod(r"P:\path\to\mod")
        settings.add_server_mod("@Workshop Mod")

        run_server.run_server(settings, wait=False)

        expected_workshop_mod_path = os.path.join("workshopdir", "@Workshop Mod")

        self.mock_copy_keys.assert_has_calls([
            mock.call(os.path.join("some-mod", "keys"), "keys"),
            mock.call(os.path.join(r"P:\path\to\mod", "keys"), "keys"),
            mock.call(os.path.join(expected_workshop_mod_path, "keys"), "keys")
        ])

        self.mock_popen.assert_called_once_with([
            "server.exe",
            "-config=config.cfg",
            f"-servermod=some-mod;P:\\path\\to\\mod;{expected_workshop_mod_path}"
        ])

    def test_waits_for_new_script_log_and_streams_it_when_wait_is_true(self) -> None:
        self.mock_newest.side_effect = [
            "script_previous.log",
            "script_previous.log",
            "script_previous.log",
            "script_new.log"
        ]

        self.server_config.server_profile = "profile/dir"
        settings = launch_settings.LaunchSettings(self.server_config)

        run_server.run_server(settings, wait=True)

        assert self.mock_newest.call_count == 4
        self.mock_newest.assert_called_with("profile/dir")

        assert self.mock_sleep.call_count == 2
        self.mock_sleep.assert_called_with(1)
