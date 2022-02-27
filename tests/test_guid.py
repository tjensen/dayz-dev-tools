import unittest
from unittest import mock

from dayz_dev_tools import guid

from tests import helpers


main = helpers.call_main(guid)


class TestGUIDForSteamID64(unittest.TestCase):
    def test_returns_dayz_guid_for_provided_steam_id64(self) -> None:
        assert guid.guid_for_steamid64(0) \
            == "X-zrZv_IbzjZUnhsbWlsecLbwjndTpG0ZynXOif7V-k="

        assert guid.guid_for_steamid64(1234567890) \
            == "x3Xnt1ft5jDNCqERO9ECZhqziCnKUqZCKreChi8mhkY="

        assert guid.guid_for_steamid64(76561197970002375) \
            == "hYJaNGoMDv2QEno2R7tXKUSj8eXefMiv_UvAF_EUKto="

        assert guid.guid_for_steamid64(0xffffffffffffffff) \
            == "LNsmJltNxl47RNaU8SH9bembnkuK5_CNhL-pU3Y1rkM="


class TestMain(unittest.TestCase):
    @mock.patch("builtins.print")
    def test_prints_dayz_guid_for_given_steamid64(self, mock_print: mock.Mock) -> None:
        main(
            [
                "ignored",
                "76561197970002375"
            ],
            {}
        )

        mock_print.assert_called_once_with(
            "DayZ GUID: hYJaNGoMDv2QEno2R7tXKUSj8eXefMiv_UvAF_EUKto=")
