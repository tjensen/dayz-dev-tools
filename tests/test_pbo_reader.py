import io
import unittest

from dayz import pbo_reader


class TestUnpack(unittest.TestCase):
    def test_files_returns_empty_list(self) -> None:
        pbo_file = io.BytesIO()
        reader = pbo_reader.PBOReader(pbo_file)

        files = reader.files()

        assert files == []
