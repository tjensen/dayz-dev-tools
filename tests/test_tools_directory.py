import unittest
from unittest import mock

from dayz_dev_tools import tools_directory


class TestToolsDirectory(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        import_module_patcher = mock.patch("importlib.import_module")
        self.mock_import_module = import_module_patcher.start()
        self.addCleanup(import_module_patcher.stop)

        self.mock_winreg = self.mock_import_module.return_value

    def test_returns_none_when_winreg_module_is_not_available(self) -> None:
        self.mock_import_module.side_effect = ModuleNotFoundError

        assert tools_directory.tools_directory() is None

    def test_raises_when_importing_winreg_fails_for_other_reasons(self) -> None:
        self.mock_import_module.side_effect = Exception("other import error")

        with self.assertRaises(Exception) as error:
            tools_directory.tools_directory()

        assert error.exception == self.mock_import_module.side_effect

    def test_returns_dayz_tools_directory_path_when_present_in_windows_registry(self) -> None:
        mock_key = self.mock_winreg.OpenKey.return_value
        self.mock_winreg.QueryValueEx.return_value = ("path/to/dayz/tools", 1)

        assert tools_directory.tools_directory() == "path/to/dayz/tools"

        self.mock_import_module.assert_called_once_with("winreg")

        self.mock_winreg.OpenKey.assert_called_once_with(
            self.mock_winreg.HKEY_CURRENT_USER, r"Software\bohemia interactive\Dayz Tools")

        self.mock_winreg.QueryValueEx.assert_called_once_with(mock_key, "path")

        mock_key.Close.assert_called_once_with()

    def test_returns_none_when_key_is_not_present_in_registry(self) -> None:
        self.mock_winreg.OpenKey.side_effect = OSError

        assert tools_directory.tools_directory() is None

        self.mock_winreg.QueryValueEx.assert_not_called()

    def test_closes_key_when_querying_its_value_fails(self) -> None:
        mock_key = self.mock_winreg.OpenKey.return_value
        self.mock_winreg.QueryValueEx.side_effect = Exception("query failure")

        assert tools_directory.tools_directory() is None

        mock_key.Close.assert_called_once_with()
