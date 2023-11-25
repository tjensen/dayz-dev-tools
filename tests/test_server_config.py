import os
import pathlib
import tempfile
import unittest

from dayz_dev_tools import server_config


class TestLoad(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.config_file = tempfile.NamedTemporaryFile("w+", delete=False)
        self.config_file.close()
        self.addCleanup(lambda: pathlib.Path(self.config_file.name).unlink(missing_ok=True))

    def test_returns_default_configuration_when_config_file_does_not_exist(self) -> None:
        os.unlink(self.config_file.name)

        config = server_config.load(self.config_file.name)

        assert config == server_config.ServerConfig(
            executable=server_config.DEFAULT_EXECUTABLE,
            config="serverDZ.cfg",
            directory=None,
            profile_directory=None,
            mission_directory=None,
            bundle_path="bundles.py",
            workshop_directory=server_config.DEFAULT_WORKSHOP_DIRECTORY,
            parameters=[],
            bundles={})

    def test_raises_for_other_errors(self) -> None:
        with open(self.config_file.name, "w") as f:
            f.write("invalid toml file")

        with self.assertRaises(Exception) as error:
            server_config.load(self.config_file.name)

        assert f"Configuration error in {self.config_file.name}" in str(error.exception)

    def test_requires_settings_to_have_correct_types(self) -> None:
        with open(self.config_file.name, "w") as f:
            f.write("""\
[server]
executable = 42
""")

        with self.assertRaises(Exception) as error:
            server_config.load(self.config_file.name)

        assert str(error.exception) == \
            "Configuration error at server.executable: 42: Input should be a valid string"

    def test_returns_defaults_for_attributes_not_set_in_config_file(self) -> None:
        config = server_config.load(self.config_file.name)

        assert config == server_config.ServerConfig(
            executable=server_config.DEFAULT_EXECUTABLE,
            config="serverDZ.cfg",
            directory=None,
            profile_directory=None,
            mission_directory=None,
            bundle_path="bundles.py",
            workshop_directory=server_config.DEFAULT_WORKSHOP_DIRECTORY,
            parameters=[],
            bundles={})

    def test_returns_config_file_settings(self) -> None:
        with open(self.config_file.name, "w") as f:
            f.write("""\
[server]
executable = "EXECUTABLE"
config = "CONFIG-FILE"
directory = "SERVER-DIRECTORY"
profile_directory = "PROFILE"
mission_directory = "MISSION"
parameters = ["-opt1", "-opt2=value"]
bundles = "BUNDLES"

[workshop]
directory = "WORKSHOP-DIRECTORY"
""")

        config = server_config.load(self.config_file.name)

        assert config == server_config.ServerConfig(
            executable="EXECUTABLE",
            config="CONFIG-FILE",
            directory="SERVER-DIRECTORY",
            profile_directory="PROFILE",
            mission_directory="MISSION",
            bundle_path="BUNDLES",
            workshop_directory="WORKSHOP-DIRECTORY",
            parameters=["-opt1", "-opt2=value"],
            bundles={})

    def test_returns_config_with_bundles_when_present_in_config_file(self) -> None:
        with open(self.config_file.name, "w") as f:
            f.write("""\
[bundle.override_all]
executable = "OVERRIDDEN-EXE"
config = "OVERRIDDEN-CFG"
directory = "OVERRIDDEN-SERVER-DIRECTORY"
profile_directory = "OVERRIDDEN-PROFILE"
workshop_directory = "OVERRIDDEN-WORKSHOP"
mods = ["mod1", "mod2", "mod3"]
server_mods = ["smod1", "smod2", "smod3"]
mission_directory = "OVERRIDDEN-MISSION"
parameters = ["-opt1", "-opt2=value"]

[bundle.override_some]
mods = ["mod1", "mod2"]
server_mods = ["mod3"]

[bundle.add_mods_as_string]
mods = "mod1;mod2"
server_mods = "mod3"

[bundle.override_nothing]
""")

        config = server_config.load(self.config_file.name)

        assert config.bundles == {
            "override_all": server_config.BundleConfig(
                executable="OVERRIDDEN-EXE",
                config="OVERRIDDEN-CFG",
                directory="OVERRIDDEN-SERVER-DIRECTORY",
                profile_directory="OVERRIDDEN-PROFILE",
                workshop_directory="OVERRIDDEN-WORKSHOP",
                mods=["mod1", "mod2", "mod3"],
                server_mods=["smod1", "smod2", "smod3"],
                mission_directory="OVERRIDDEN-MISSION",
                parameters=["-opt1", "-opt2=value"]),
            "override_some": server_config.BundleConfig(
                mods=["mod1", "mod2"],
                server_mods=["mod3"]),
            "add_mods_as_string": server_config.BundleConfig(
                mods=["mod1", "mod2"],
                server_mods=["mod3"]),
            "override_nothing": server_config.BundleConfig()
        }

    def test_requires_bundles_to_have_correct_types(self) -> None:
        with open(self.config_file.name, "w") as f:
            f.write("""\
[bundle.invalid]
mods = 2112
""")

        with self.assertRaises(Exception):
            server_config.load(self.config_file.name)
