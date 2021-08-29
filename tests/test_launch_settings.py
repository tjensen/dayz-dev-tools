import os
import unittest
from unittest import mock

from dayz_dev_tools import launch_settings


BUNDLE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "bundles.py")


class TestLaunchSettings(unittest.TestCase):
    def test_executable_returns_specified_executable(self) -> None:
        settings = launch_settings.LaunchSettings("server.exe", "workshop/dir", BUNDLE_PATH)

        assert settings.executable() == "server.exe"

    def test_executable_returns_executable_overridden_using_set_executable(self) -> None:
        settings = launch_settings.LaunchSettings("server.exe", "workshop/dir", BUNDLE_PATH)

        settings.set_executable("overridden.bat")

        assert settings.executable() == "overridden.bat"

    def test_workshop_directory_returns_specified_workshop_path(self) -> None:
        settings = launch_settings.LaunchSettings("server.exe", "workshop/dir", BUNDLE_PATH)

        assert settings.workshop_directory() == "workshop/dir"

    def test_workshop_directory_returns_overridden_workshop_directory(self) -> None:
        settings = launch_settings.LaunchSettings("server.exe", "workshop/dir", BUNDLE_PATH)

        settings.set_workshop_directory("overridden/location")

        assert settings.workshop_directory() == "overridden/location"

    def test_mods_returns_empty_list_by_default(self) -> None:
        settings = launch_settings.LaunchSettings("server.exe", "workshop/dir", BUNDLE_PATH)

        assert settings.mods() == []

    def test_mods_returns_list_of_mods_added_with_add_mod(self) -> None:
        settings = launch_settings.LaunchSettings("server.exe", "workshop/dir", BUNDLE_PATH)

        settings.add_mod("MOD1")
        settings.add_mod("MOD2")
        settings.add_mod("MOD3")

        assert settings.mods() == ["MOD1", "MOD2", "MOD3"]

    def test_server_mods_returns_empty_list_by_default(self) -> None:
        settings = launch_settings.LaunchSettings("server.exe", "workshop/dir", BUNDLE_PATH)

        assert settings.server_mods() == []

    def test_server_mods_returns_list_of_mods_added_with_add_server_mod(self) -> None:
        settings = launch_settings.LaunchSettings("server.exe", "workshop/dir", BUNDLE_PATH)

        settings.add_server_mod("MOD1")
        settings.add_server_mod("MOD2")
        settings.add_server_mod("MOD3")

        assert settings.server_mods() == ["MOD1", "MOD2", "MOD3"]

    def test_mission_returns_none_by_default(self) -> None:
        settings = launch_settings.LaunchSettings("server.exe", "workshop/dir", BUNDLE_PATH)

        assert settings.mission() is None

    def test_mission_returns_mission_configured_with_set_mission(self) -> None:
        settings = launch_settings.LaunchSettings("server.exe", "workshop/dir", BUNDLE_PATH)

        settings.set_mission("MISSION")

        assert settings.mission() == "MISSION"

    def test_load_bundle_calls_bundle_function_by_name_in_bundle_module(self) -> None:
        settings = launch_settings.LaunchSettings("server.exe", "workshop/dir", BUNDLE_PATH)

        with mock.patch("bundles.bundle1") as mock_bundle1:
            settings.load_bundle("bundle1")

        mock_bundle1.assert_called_once_with(settings)

    def test_load_bundle_raises_if_bundle_path_is_invalid(self) -> None:
        settings = launch_settings.LaunchSettings("server.exe", "workshop/dir", "invalid")

        with self.assertRaises(Exception):
            settings.load_bundle("does_not_matter")

    def test_load_bundle_raises_if_bundle_function_does_not_exist_in_module(self) -> None:
        settings = launch_settings.LaunchSettings("server.exe", "workshop/dir", BUNDLE_PATH)

        with self.assertRaises(Exception):
            settings.load_bundle("missing")
