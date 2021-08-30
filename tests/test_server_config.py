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
            server_executable=r".\DayZServer_x64.exe",
            server_config="serverDZ.cfg",
            bundle_path="bundles.py",
            workshop_directory=r"C:\Program Files (x86)\Steam\steamapps\common\DayZ\!Workshop")

    def test_returns_defaults_for_attributes_not_set_in_config_file(self) -> None:
        config = server_config.load(self.config_file.name)

        assert config == server_config.ServerConfig(
            server_executable=r".\DayZServer_x64.exe",
            server_config="serverDZ.cfg",
            bundle_path="bundles.py",
            workshop_directory=r"C:\Program Files (x86)\Steam\steamapps\common\DayZ\!Workshop")

    def test_returns_config_file_settings(self) -> None:
        with open(self.config_file.name, "w") as f:
            f.write("""\
[server]
executable = "EXECUTABLE"
config = "CONFIG-FILE"
bundles = "BUNDLES"

[workshop]
directory = "WORKSHOP-DIRECTORY"
""")

        config = server_config.load(self.config_file.name)

        assert config == server_config.ServerConfig(
            server_executable="EXECUTABLE",
            server_config="CONFIG-FILE",
            bundle_path="BUNDLES",
            workshop_directory="WORKSHOP-DIRECTORY")
