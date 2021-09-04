import io
import ntpath
import typing

from dayz_dev_tools import pbo_file
from dayz_dev_tools import pbo_file_reader


def _read_headers(reader: pbo_file_reader.PBOFileReader) -> typing.List[typing.Tuple[bytes, bytes]]:
    headers: typing.List[typing.Tuple[bytes, bytes]] = []
    if len(reader.readz()) == 0:
        pos = reader.tell()
        key = reader.readz()
        if key == b"sreV":
            reader.seek(pos + 20)
        else:
            reader.seek(pos)

        while True:
            key = reader.readz()
            if len(key) == 0:
                break

            value = reader.readz()
            headers.append((key, value))
    else:
        reader.seek(0)

    return headers


def _prefix(headers: typing.List[typing.Tuple[bytes, bytes]]) -> typing.Optional[bytes]:
    for key, value in headers:
        if key == b"prefix":
            return value

    return None


def _read_file_entries(
    reader: pbo_file_reader.PBOFileReader, prefix: typing.Optional[bytes]
) -> typing.List[pbo_file.PBOFile]:
    entries: typing.List[pbo_file.PBOFile] = []

    while True:
        filename = reader.readz()

        if len(filename) == 0:
            break

        if prefix is not None:
            filename = ntpath.join(prefix, filename)

        mime_type = reader.read(4)
        original_size = reader.readuint()
        reserved = reader.readuint()
        time_stamp = reader.readuint()
        data_size = reader.readuint()
        entries.append(
            pbo_file.PBOFile(
                filename, mime_type, original_size, reserved, time_stamp, data_size))

    offset = reader.tell() + 20
    for entry in entries:
        entry.content_reader = reader.subreader(offset, entry.data_size)
        offset += entry.data_size

    return entries


class PBOReader():
    """Interface for reading a PBO archive."""
    def __init__(self, file: typing.BinaryIO):
        """Create a new :class:`PBOReader` instance.

        :Parameters:
          - `file`: A binary file-like object providing PBO archive contents.
        """
        self._file = file
        self._file.seek(0, io.SEEK_END)
        size = file.tell()

        reader = pbo_file_reader.PBOFileReader(self._file, 0, size)
        self._headers = _read_headers(reader)
        self._prefix = _prefix(self._headers)
        self._files = _read_file_entries(reader, self._prefix)

    def files(self) -> typing.List[pbo_file.PBOFile]:
        """Get the list of files contained in the PBO archive.

        :Returns:
          A list of :class:`~dayz_dev_tools.pbo_file.PBOFile` instances representing the files
          contained in the PBO archive.
        """
        return self._files

    def file(self, filename: typing.AnyStr) -> typing.Optional[pbo_file.PBOFile]:
        """Get a file contained in the PBO archive, by name.

        :Parameters:
          - `filename`: A ``str`` or ``bytes`` containing the filename of the file to be retrieved.
            If a ``str``, the filename is matched case-insensitively by the normalized filename in
            the PBO (see :meth:`dayz_dev_tools.pbo_file.PBOFile.normalized_filename`). If a
            ``bytes``, the filename is matched case-insensitively by the raw filename (see
            :any:`dayz_dev_tools.pbo_file.PBOFile.filename`).

        :Returns:
          An instance of :class:`dayz_dev_tools.pbo_file.PBOFile` representing the retrieved file.
        """
        for f in self._files:
            if isinstance(filename, bytes):
                if filename.lower() == f.filename.lower():
                    return f
            else:
                if filename.lower() == f.normalized_filename().lower():
                    return f

        return None

    def headers(self) -> typing.List[typing.Tuple[bytes, bytes]]:
        """Get the PBO archive headers.

        :Returns:
          A list of tuples containing the header names and values.
        """
        return self._headers

    def prefix(self) -> typing.Optional[bytes]:
        """Get the PBO archive prefix.

        :Returns:
          The PBO archive prefix, or ``None`` if the PBO archive does not have a ``prefix`` header.
        """
        return self._prefix
