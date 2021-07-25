import io
import typing

from dayz import pbo_file
from dayz import pbo_file_reader


def _read_headers(reader: pbo_file_reader.PBOFileReader) -> typing.Dict[bytes, bytes]:
    headers: typing.Dict[bytes, bytes] = {}
    if len(reader.readz()) == 0:
        # Skip the "Vers" property entry
        reader.seek(reader.tell() + 24)

        while True:
            key = reader.readz()
            if len(key) == 0:
                break

            value = reader.readz()
            headers[key] = value
    else:
        reader.seek(0)

    return headers


def _read_file_entries(reader: pbo_file_reader.PBOFileReader) -> typing.List[pbo_file.PBOFile]:
    entries: typing.List[pbo_file.PBOFile] = []

    while True:
        filename = reader.readz()

        if len(filename) == 0:
            break

        mime_type = reader.read(4)
        original_size = reader.readuint()
        reserved = reader.readuint()
        time_stamp = reader.readuint()
        data_size = reader.readuint()
        entries.append(
            pbo_file.PBOFile(
                filename, mime_type, original_size, reserved, time_stamp, data_size))

    offset = reader.tell()
    for entry in entries:
        entry.content_reader = reader.subreader(offset, entry.data_size)
        offset += entry.data_size

    return entries


class PBOReader():
    def __init__(self, file: typing.BinaryIO):
        self._file = file
        self._file.seek(0, io.SEEK_END)
        size = file.tell()

        reader = pbo_file_reader.PBOFileReader(self._file, 0, size)
        self._headers = _read_headers(reader)
        self._files = _read_file_entries(reader)

    def files(self) -> typing.List[pbo_file.PBOFile]:
        return self._files

    def file(self, filename: bytes) -> typing.Optional[pbo_file.PBOFile]:
        for f in self._files:
            if filename == f.normalized_filename():
                return f

        return None

    def headers(self) -> typing.Dict[bytes, bytes]:
        return self._headers
