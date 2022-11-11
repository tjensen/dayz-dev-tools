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
            executable="server.exe",
            config="config.cfg",
            directory="server/dir",
            workshop_directory="workshop/dir",
            bundle_path=BUNDLE_PATH,
            parameters=["-extraParam"],
            bundles={
                "override_all": server_config.BundleConfig(
                    executable="OVERRIDDEN-EXE",
                    config="OVERRIDDEN-CFG",
                    directory="OVERRIDDEN-SERVER-DIRECTORY",
                    profile_directory="OVERRIDDEN-PROFILE",
                    workshop_directory="OVERRIDDEN-WORKSHOP",
                    mods=["mod1", "mod2", "mod3"],
                    server_mods=["mod4", "mod5", "mod6"],
                    mission_directory="OVERRIDDEN-MISSION",
                    parameters=["-opt1", "-opt2=value"]),
                "override_some": server_config.BundleConfig(
                    mods=["mod7", "mod8"],
                    server_mods=["mod9"])
            })

    def test_executable_returns_specified_executable(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        assert settings.executable() == self.config.executable

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

    def test_directory_returns_directory_specified_in_config(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        assert settings.directory() == "server/dir"

    def test_directory_returns_directory_overridden_using_set_directory(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        settings.set_directory("overridden/server/dir")

        assert settings.directory() == "overridden/server/dir"

    def test_profile_directory_returns_specified_profile_directory(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        assert settings.profile_directory() is None

    def test_profile_directory_returns_profile_overridden_using_set_profile_directory(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        settings.set_profile_directory("PROFILE")

        assert settings.profile_directory() == "PROFILE"

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

    def test_add_mod_ignores_mods_that_have_already_been_added(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)
        settings.add_mod("MOD1")
        settings.add_mod("MOD2")
        settings.add_mod("MOD3")

        settings.add_mod("MOD2")

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

    def test_add_server_mod_ignores_server_mods_that_have_already_been_added(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)
        settings.add_server_mod("MOD1")
        settings.add_server_mod("MOD2")
        settings.add_server_mod("MOD3")

        settings.add_server_mod("MOD2")

        assert settings.server_mods() == ["MOD1", "MOD2", "MOD3"]

    def test_mission_directory_returns_specified_mission_directory(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        assert settings.mission_directory() is None

    def test_mission_directory_returns_mission_configured_with_set_mission_directory(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        settings.set_mission_directory("MISSION")

        assert settings.mission_directory() == "MISSION"

    def test_parameters_returns_parameters_from_config(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        assert settings.parameters() == ["-extraParam"]

    def test_parameters_returns_parameters_added_with_add_parameter(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        settings.add_parameter("-opt1")
        settings.add_parameter("-opt2=value")

        assert settings.parameters() == ["-extraParam", "-opt1", "-opt2=value"]

    def test_load_bundle_loads_bundle_from_config_when_present_in_config(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        settings.load_bundle("override_all")

        assert settings.executable() == "OVERRIDDEN-EXE"
        assert settings.config() == "OVERRIDDEN-CFG"
        assert settings.directory() == "OVERRIDDEN-SERVER-DIRECTORY"
        assert settings.profile_directory() == "OVERRIDDEN-PROFILE"
        assert settings.workshop_directory() == "OVERRIDDEN-WORKSHOP"
        assert settings.mods() == ["mod1", "mod2", "mod3"]
        assert settings.server_mods() == ["mod4", "mod5", "mod6"]
        assert settings.mission_directory() == "OVERRIDDEN-MISSION"
        assert settings.parameters() == ["-extraParam", "-opt1", "-opt2=value"]

    def test_load_bundle_from_config_only_sets_settings_in_config(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        settings.load_bundle("override_some")

        assert settings.executable() == "server.exe"
        assert settings.config() == "config.cfg"
        assert settings.directory() == "server/dir"
        assert settings.profile_directory() is None
        assert settings.workshop_directory() == "workshop/dir"
        assert settings.mods() == ["mod7", "mod8"]
        assert settings.server_mods() == ["mod9"]
        assert settings.mission_directory() is None

    def test_load_bundle_calls_bundle_function_by_name_in_bundle_module(self) -> None:
        settings = launch_settings.LaunchSettings(self.config)

        with mock.patch("__dayz_server_bundles__.bundle1") as mock_bundle1:
            settings.load_bundle("bundle1")

        mock_bundle1.assert_called_once_with(settings)

    def test_load_bundle_does_not_call_function_in_module_if_bundle_name_is_in_config(self) -> None:
        self.config.bundles["bundle1"] = self.config.bundles["override_all"]

        settings = launch_settings.LaunchSettings(self.config)

        with mock.patch("__dayz_server_bundles__.bundle1") as mock_bundle1:
            settings.load_bundle("bundle1")

        mock_bundle1.assert_not_called()

    def test_load_bundle_raises_if_bundle_path_is_invalid(self) -> None:
        self.config.bundle_path = "invalid.py"

        settings = launch_settings.LaunchSettings(self.config)

        with self.assertRaises(Exception):
            settings.load_bundle("does_not_matter")

    def test_load_bundle_raises_if_bundle_filename_missing_extension(self) -> None:
        self.config.bundle_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "bad_filename")

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
