import unittest

from dayz_dev_tools import guid


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
