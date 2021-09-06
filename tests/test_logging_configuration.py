import logging
import unittest
from unittest import mock

from dayz_dev_tools import logging_configuration


class TestConfigureLogging(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        basic_config_patcher = mock.patch("logging.basicConfig")
        self.mock_basic_config = basic_config_patcher.start()
        self.addCleanup(basic_config_patcher.stop)

    def test_sets_log_format_and_level_when_debug_is_false(self) -> None:
        logging_configuration.configure_logging(debug=False)

        self.mock_basic_config.assert_called_once_with(
            format="%(asctime)s %(levelname)s:%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S%z",
            level=logging.INFO)

    def test_sets_log_format_and_level_when_debug_is_true(self) -> None:
        logging_configuration.configure_logging(debug=True)

        self.mock_basic_config.assert_called_once_with(
            format="%(asctime)s %(levelname)s:%(module)s:%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S%z",
            level=logging.DEBUG)
