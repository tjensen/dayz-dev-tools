import os
import unittest
from unittest import mock

from dayz_dev_tools import launch_settings
from dayz_dev_tools import server_config


BUNDLE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "bundles.py")


class TestLaunchSettings(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.config = server_config.ServerConfig(
            server_executable="server.exe",
            server_config="config.cfg",
            workshop_directory="workshop/dir",
            bundle_path=BUNDLE_PATH,
            bundles={
                "override_all": server_config.BundleConfig(
                    executable="OVERRIDDEN-EXE",
                    config="OVERRIDDEN-CFG",
                    profile="OVERRIDDEN-PROFILE",
                    workshop="OVERRIDDEN-WORKSHOP",
                    mods=["mod1", "mod2", "mod3"],
                    server_mods=["mod4", "mod5", "mod6"],
                    mission="OVERRIDDEN-MISSION"),
                "override_some": server_config.BundleConfig(
                    mods=["mod7", "mod8"],
                    server_mods=["mod9"])
            })

    def test_executable_returns_specified_executable(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        assert settings.executable() == self.config.server_executable

    def test_executable_returns_executable_overridden_using_set_executable(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        settings.set_executable("overridden.bat")

        assert settings.executable() == "overridden.bat"

    def test_config_returns_specified_config_file(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        assert settings.config() == "config.cfg"

    def test_config_returns_config_overridden_using_set_config(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        settings.set_config("other.cfg")

        assert settings.config() == "other.cfg"

    def test_profile_returns_specified_profile_directory(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        assert settings.profile() is None

    def test_profile_returns_profile_overridden_using_set_profile(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        settings.set_profile("PROFILE")

        assert settings.profile() == "PROFILE"

    def test_workshop_directory_returns_specified_workshop_path(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        assert settings.workshop_directory() == self.config.workshop_directory

    def test_workshop_directory_returns_overridden_workshop_directory(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        settings.set_workshop_directory("overridden/location")

        assert settings.workshop_directory() == "overridden/location"

    def test_mods_returns_empty_list_by_default(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        assert settings.mods() == []

    def test_mods_returns_list_of_mods_added_with_add_mod(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        settings.add_mod("MOD1")
        settings.add_mod("MOD2")
        settings.add_mod("MOD3")

        assert settings.mods() == ["MOD1", "MOD2", "MOD3"]

    def test_server_mods_returns_empty_list_by_default(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        assert settings.server_mods() == []

    def test_server_mods_returns_list_of_mods_added_with_add_server_mod(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        settings.add_server_mod("MOD1")
        settings.add_server_mod("MOD2")
        settings.add_server_mod("MOD3")

        assert settings.server_mods() == ["MOD1", "MOD2", "MOD3"]

    def test_mission_returns_specified_mission_directory(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        assert settings.mission() is None

    def test_mission_returns_mission_configured_with_set_mission(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        settings.set_mission("MISSION")

        assert settings.mission() == "MISSION"

    def test_load_bundle_loads_bundle_from_config_when_present_in_config(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        settings.load_bundle("override_all")

        assert settings.executable() == "OVERRIDDEN-EXE"
        assert settings.config() == "OVERRIDDEN-CFG"
        assert settings.profile() == "OVERRIDDEN-PROFILE"
        assert settings.workshop_directory() == "OVERRIDDEN-WORKSHOP"
        assert settings.mods() == ["mod1", "mod2", "mod3"]
        assert settings.server_mods() == ["mod4", "mod5", "mod6"]
        assert settings.mission() == "OVERRIDDEN-MISSION"

    def test_load_bundle_from_config_only_sets_settings_in_config(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        settings.load_bundle("override_some")

        assert settings.executable() == "server.exe"
        assert settings.config() == "config.cfg"
        assert settings.profile() is None
        assert settings.workshop_directory() == "workshop/dir"
        assert settings.mods() == ["mod7", "mod8"]
        assert settings.server_mods() == ["mod9"]
        assert settings.mission() is None

    def test_load_bundle_calls_bundle_function_by_name_in_bundle_module(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        with mock.patch("bundles.bundle1") as mock_bundle1:
            settings.load_bundle("bundle1")

        mock_bundle1.assert_called_once_with(settings)

    def test_load_bundle_does_not_call_function_in_module_if_bundle_name_is_in_config(self) -> None:
        self.config.bundles["bundle1"] = self.config.bundles["override_all"]

        settings = launch_settings.LaunchSettings(self.config)

        with mock.patch("bundles.bundle1") as mock_bundle1:
            settings.load_bundle("bundle1")

        mock_bundle1.assert_not_called()

    def test_load_bundle_raises_if_bundle_path_is_invalid(self) -> None:
        self.config.bundle_path = "invalid"

        settings = launch_settings.LaunchSettings(self.config)

        with self.assertRaises(Exception):
            settings.load_bundle("does_not_matter")

    def test_load_bundle_raises_if_bundle_function_does_not_exist_in_module(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        with self.assertRaises(Exception):
            settings.load_bundle("missing")

    def test_constructor_raises_if_bundle_exists_but_loading_fails(self) -> None:
        self.config.bundle_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "bad_bundle.py")

        with self.assertRaises(Exception):
            launch_settings.LaunchSettings(self.config)
