import os
import stat
import subprocess
import sys
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
            executable="SERVER-EXECUTABLE",
            config="SERVER-CONFIG",
            workshop_directory="WORKSHOP-DIRECTORY",
            bundle_path="BUNDLE-PATH",
            bundles={})

        logging_patcher = mock.patch("dayz_dev_tools.logging_configuration.configure_logging")
        self.mock_configure_logging = logging_patcher.start()
        self.addCleanup(logging_patcher.stop)

        load_patcher = mock.patch(
            "dayz_dev_tools.server_config.load", return_value=self.server_config)
        self.mock_server_config_load = load_patcher.start()
        self.addCleanup(load_patcher.stop)

        settings_patcher = mock.patch(
            "dayz_dev_tools.launch_settings.LaunchSettings", autospec=True)
        self.mock_launch_settings_class = settings_patcher.start()
        self.addCleanup(settings_patcher.stop)

        chdir_patcher = mock.patch("dayz_dev_tools.misc.chdir")
        self.mock_chdir = chdir_patcher.start()
        self.addCleanup(chdir_patcher.stop)

        run_server_patcher = mock.patch("dayz_dev_tools.run_server.run_server")
        self.mock_run_server = run_server_patcher.start()
        self.addCleanup(run_server_patcher.stop)

    def test_loads_default_config_and_runs_server(self) -> None:
        mock_launch_settings = self.mock_launch_settings_class.return_value

        main(
            [
                "ignored"
            ],
            {}
        )

        self.mock_configure_logging.assert_called_once_with(debug=False)

        self.mock_server_config_load.assert_called_once_with("server.toml")

        self.mock_launch_settings_class.assert_called_once_with(self.server_config)

        self.mock_chdir.assert_called_once_with(mock_launch_settings.directory.return_value)

        self.mock_run_server.assert_called_once_with(
            mock_launch_settings, localappdata=None, wait=True)

    def test_passes_localappdata_when_set_in_environment(self) -> None:
        mock_launch_settings = self.mock_launch_settings_class.return_value

        main(
            [
                "ignored"
            ],
            {
                "LOCALAPPDATA": "local/app/data",
            }
        )

        self.mock_run_server.assert_called_once_with(
            mock_launch_settings, localappdata="local/app/data", wait=True)

    def test_loads_config_filename_from_arguments_when_provided(self) -> None:
        main(
            [
                "ignored",
                "--config", "CONFIG-FILE"
            ],
            {}
        )

        self.mock_server_config_load.assert_called_once_with("CONFIG-FILE")

    def test_runs_server_without_waiting_when_specified_in_arguments(self) -> None:
        mock_launch_settings = self.mock_launch_settings_class.return_value

        main(
            [
                "ignored",
                "--no-wait"
            ],
            {}
        )

        self.mock_run_server.assert_called_once_with(
            mock_launch_settings, localappdata=None, wait=False)

    def test_sets_log_level_to_debug_when_debug_option_is_specified(self) -> None:
        main(
            [
                "ignored",
                "--debug"
            ],
            {}
        )

        self.mock_configure_logging.assert_called_once_with(debug=True)

    def test_loads_bundles_when_specified_in_arguments(self) -> None:
        mock_launch_settings = self.mock_launch_settings_class.return_value

        main(
            [
                "ignored",
                "bundle1",
                "bundle2",
                "bundle3"
            ],
            {}
        )

        assert mock_launch_settings.load_bundle.call_count == 3

        mock_launch_settings.load_bundle.assert_has_calls([
            mock.call("bundle1"),
            mock.call("bundle2"),
            mock.call("bundle3")
        ])

    def test_raises_systemexit_on_error(self) -> None:
        self.mock_run_server.side_effect = Exception("run_server error")

        with self.assertRaises(SystemExit) as error:
            main(
                [
                    "ignored"
                ],
                {}
            )

        assert error.exception.code == 1


class TestRunServer(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.server_config = server_config.ServerConfig(
            executable="server.exe",
            config="config.cfg",
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

        wait_for_new_patcher = mock.patch("dayz_dev_tools.script_logs.wait_for_new")
        self.mock_wait_for_new = wait_for_new_patcher.start()
        self.addCleanup(wait_for_new_patcher.stop)

        open_patcher = mock.patch("builtins.open", mock.mock_open())
        self.mock_open = open_patcher.start()
        self.addCleanup(open_patcher.stop)

        stream_patcher = mock.patch("dayz_dev_tools.script_logs.stream")
        self.mock_stream = stream_patcher.start()
        self.addCleanup(stream_patcher.stop)

        stat_patcher = mock.patch("os.stat")
        self.mock_stat = stat_patcher.start()
        self.addCleanup(stat_patcher.stop)

    def test_runs_executable_with_provided_launch_settings(self) -> None:
        settings = launch_settings.LaunchSettings(self.server_config)

        run_server.run_server(settings, localappdata="localappdata", wait=False)

        self.mock_popen.assert_called_once_with(
            ["server.exe", "-config=config.cfg", "-log"],
            stdout=subprocess.DEVNULL)

        self.mock_newest.assert_not_called()

        self.mock_popen.return_value.wait.assert_not_called()

    def test_runs_executable_with_profiles_parameter_when_profile_is_not_none(self) -> None:
        self.server_config.profile_directory = "PROFILE"
        settings = launch_settings.LaunchSettings(self.server_config)

        run_server.run_server(settings, localappdata="localappdata", wait=False)

        self.mock_popen.assert_called_once_with(
            [
                "server.exe", "-config=config.cfg", "-log", "-profiles=PROFILE"
            ],
            stdout=subprocess.DEVNULL)

    def test_runs_executable_with_mission_parameter_when_mission_is_not_none(self) -> None:
        self.server_config.mission_directory = "MISSION"
        settings = launch_settings.LaunchSettings(self.server_config)

        run_server.run_server(settings, localappdata="localappdata", wait=False)

        self.mock_popen.assert_called_once_with(
            [
                "server.exe", "-config=config.cfg", "-log", "-mission=MISSION"
            ],
            stdout=subprocess.DEVNULL)

    def test_copies_keys_and_runs_with_mod_parameter_when_mods_are_added(self) -> None:
        self.mock_stat.return_value = mock.Mock(st_mode=stat.S_IFDIR)

        settings = launch_settings.LaunchSettings(self.server_config)
        settings.add_mod("some-mod")
        settings.add_mod(r"P:\path\to\mod")
        settings.add_mod("@Workshop Mod")

        run_server.run_server(settings, localappdata="localappdata", wait=False)

        expected_workshop_mod_path = os.path.join("workshopdir", "@Workshop Mod")

        self.mock_stat.assert_has_calls([
            mock.call("some-mod"),
            mock.call(r"P:\path\to\mod"),
            mock.call(expected_workshop_mod_path)
        ])

        self.mock_copy_keys.assert_has_calls([
            mock.call("some-mod", "keys"),
            mock.call(r"P:\path\to\mod", "keys"),
            mock.call(expected_workshop_mod_path, "keys")
        ])

        self.mock_popen.assert_called_once_with(
            [
                "server.exe",
                "-config=config.cfg",
                "-log",
                f"-mod=some-mod;P:\\path\\to\\mod;{expected_workshop_mod_path}"
            ],
            stdout=subprocess.DEVNULL)

    def test_copies_keys_and_runs_with_servermod_parameter_when_server_mods_are_added(self) -> None:
        self.mock_stat.return_value = mock.Mock(st_mode=stat.S_IFDIR)

        settings = launch_settings.LaunchSettings(self.server_config)
        settings.add_server_mod("some-mod")
        settings.add_server_mod(r"P:\path\to\mod")
        settings.add_server_mod("@Workshop Mod")

        run_server.run_server(settings, localappdata="localappdata", wait=False)

        expected_workshop_mod_path = os.path.join("workshopdir", "@Workshop Mod")

        self.mock_stat.assert_has_calls([
            mock.call("some-mod"),
            mock.call(r"P:\path\to\mod"),
            mock.call(expected_workshop_mod_path)
        ])

        self.mock_copy_keys.assert_has_calls([
            mock.call("some-mod", "keys"),
            mock.call(r"P:\path\to\mod", "keys"),
            mock.call(expected_workshop_mod_path, "keys")
        ])

        self.mock_popen.assert_called_once_with(
            [
                "server.exe",
                "-config=config.cfg",
                "-log",
                f"-servermod=some-mod;P:\\path\\to\\mod;{expected_workshop_mod_path}"
            ],
            stdout=subprocess.DEVNULL)

    def test_raises_if_mod_directory_is_not_a_directory(self) -> None:
        self.mock_stat.return_value = mock.Mock(st_mode=stat.S_IFCHR)

        settings = launch_settings.LaunchSettings(self.server_config)
        settings.add_mod("some-mod")

        with self.assertRaises(NotADirectoryError):
            run_server.run_server(settings, localappdata="localappdata", wait=False)

    def test_raises_if_workshop_mod_is_not_a_directory(self) -> None:
        self.mock_stat.return_value = mock.Mock(st_mode=stat.S_IFCHR)

        settings = launch_settings.LaunchSettings(self.server_config)
        settings.add_mod("@Workshop Mod")

        with self.assertRaises(NotADirectoryError):
            run_server.run_server(settings, localappdata="localappdata", wait=False)

    def test_raises_if_server_mod_directory_is_not_a_directory(self) -> None:
        self.mock_stat.return_value = mock.Mock(st_mode=stat.S_IFCHR)

        settings = launch_settings.LaunchSettings(self.server_config)
        settings.add_server_mod("some-mod")

        with self.assertRaises(NotADirectoryError):
            run_server.run_server(settings, localappdata="localappdata", wait=False)

    def test_raises_if_workshop_server_mod_is_not_a_directory(self) -> None:
        self.mock_stat.return_value = mock.Mock(st_mode=stat.S_IFCHR)

        settings = launch_settings.LaunchSettings(self.server_config)
        settings.add_server_mod("@Workshop Mod")

        with self.assertRaises(NotADirectoryError):
            run_server.run_server(settings, localappdata="localappdata", wait=False)

    def test_passes_extra_parameters_when_added_to_launch_settings(self) -> None:
        settings = launch_settings.LaunchSettings(self.server_config)
        settings.add_parameter("-opt1")
        settings.add_parameter("-opt2=value")

        run_server.run_server(settings, localappdata="localappdata", wait=False)

        self.mock_popen.assert_called_once_with(
            [
                "server.exe",
                "-config=config.cfg",
                "-log",
                "-opt1",
                "-opt2=value"
            ],
            stdout=subprocess.DEVNULL)

    def test_waits_for_new_script_log_and_streams_it_when_wait_is_true(self) -> None:
        self.mock_newest.return_value = "script_previous.log"
        self.mock_wait_for_new.return_value = "script_new.log"

        self.server_config.profile_directory = "profile/dir"
        settings = launch_settings.LaunchSettings(self.server_config)

        run_server.run_server(settings, localappdata="localappdata", wait=True)

        self.mock_newest.assert_called_once_with("profile/dir")

        self.mock_wait_for_new.assert_called_once_with(
            "profile/dir", "script_previous.log", timeout=1)

        self.mock_open.assert_called_once_with("script_new.log", "r", errors="surrogateescape")

        self.mock_stream.assert_called_once_with(sys.stdout, self.mock_open.return_value, mock.ANY)

        self.mock_popen.return_value.__enter__.return_value.wait.assert_called_with()
        assert self.mock_popen.return_value.__enter__.return_value.wait.call_count == 2

        self.mock_popen.return_value.__enter__.return_value.poll.side_effect = [None, None, 123]

        assert self.mock_stream.call_args[0][2]()
        assert self.mock_stream.call_args[0][2]()
        assert not self.mock_stream.call_args[0][2]()

    def test_continues_waiting_for_script_log_until_new_script_log_is_created(self) -> None:
        self.mock_newest.return_value = "script_previous.log"
        self.mock_wait_for_new.side_effect = [None, None, None, "script_new.log"]

        self.server_config.profile_directory = "profile/dir"
        settings = launch_settings.LaunchSettings(self.server_config)

        run_server.run_server(settings, localappdata="localappdata", wait=True)

        assert self.mock_wait_for_new.call_count == 4

    def test_streams_script_log_from_profile_in_localappdata_if_profile_is_none(self) -> None:
        self.mock_newest.return_value = "script_previous.log"
        self.mock_wait_for_new.return_value = "script_new.log"

        settings = launch_settings.LaunchSettings(self.server_config)

        run_server.run_server(settings, localappdata="localappdata", wait=True)

        expected_dir = os.path.join("localappdata", "DayZ")

        self.mock_newest.assert_called_once_with(expected_dir)

        self.mock_wait_for_new.assert_called_once_with(
            expected_dir, "script_previous.log", timeout=1)

    def test_streams_script_log_from_current_dir_if_profile_is_none_and_localappdata_is_unset(
            self) -> None:
        self.mock_newest.return_value = "script_previous.log"
        self.mock_wait_for_new.return_value = "script_new.log"

        settings = launch_settings.LaunchSettings(self.server_config)

        run_server.run_server(settings, localappdata=None, wait=True)

        self.mock_newest.assert_called_once_with(".")

        self.mock_wait_for_new.assert_called_once_with(".", "script_previous.log", timeout=1)

    def test_gracefully_terminates_server_when_ctrl_c_is_pressed(self) -> None:
        self.mock_newest.return_value = None
        self.mock_wait_for_new.side_effect = KeyboardInterrupt

        settings = launch_settings.LaunchSettings(self.server_config)

        run_server.run_server(settings, localappdata="localappdata", wait=True)

        self.mock_popen.return_value.__enter__.return_value.terminate.assert_called_once_with()

        self.mock_popen.return_value.__enter__.return_value.wait.assert_called_once_with()
