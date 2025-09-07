import dataclasses
import os
import re
import typing

from dayz_dev_tools import pbo_file_reader
from dayz_dev_tools_rust import expand


INVALID_FILENAME_RE = re.compile(b"[\t?*<>:\"|\x80-\xff]")

RESERVED_FILENAME_RE = re.compile(b"(CON|PRN|AUX|NUL|COM\\d|LPT\\d)\\.?")


def normalize_filename(parts: list[bytes]) -> str:
    return os.path.sep.encode().join(parts).decode(errors="replace")


@dataclasses.dataclass
class PBOFile:
    """Interface for accessing a file contained within a PBO archive. Instances should be obtained
    using :meth:`dayz_dev_tools.pbo_reader.PBOReader.file`."""
    prefix: typing.Optional[bytes]
    #: The raw name of the file
    filename: bytes
    mime_type: bytes
    original_size: int
    reserved: int
    #: The file's creation or modification time as a Unix timestamp
    time_stamp: int
    #: The size of the file in the PBO archive
    data_size: int
    content_reader: typing.Optional[pbo_file_reader.PBOFileReader] = None

    def unpack(self, output_file: typing.BinaryIO) -> None:
        """Write the contents of the file.

        :Parameters:
          - `output_file`: A binary file-like object where the contents are to be written.
        """
        assert self.content_reader is not None

        if self.original_size != 0 and self.original_size != self.data_size:
            expanded = expand(self.content_reader.read(self.data_size - 4), self.original_size)
            expected_checksum = self.content_reader.readuint()
            actual_checksum = sum(expanded)

            if actual_checksum != expected_checksum:
                raise Exception(
                    f"Checksum mismatch ({actual_checksum:#x} != {expected_checksum:#x})")

            output_file.write(expanded)
        else:
            output_file.write(self.content_reader.read(self.data_size))

    def normalized_filename(self) -> str:
        """Get the normalized version of the file's name.

        The resulting filename will contain the local OS's native directory separator character and
        any bytes representing illegal UTF-8 will be replaced.

        :Returns:
          A normalized version of the file's name.
        """
        return normalize_filename(self.split_filename())

    def split_filename(self) -> list[bytes]:
        """Get the file's name as a ``list``, where each element in the list represents a component
        of the file's path.

        :Returns:
          A list of path components.
        """
        result = list(filter(lambda c: len(c) > 0, re.split(b"[\\\\/]", self.filename)))

        if self.prefix is not None:
            result.insert(0, self.prefix)

        if len(result) == 0:
            return [b""]

        return result

    def unpacked_size(self) -> int:
        """Get the original size of the file. If the file is compressed, this will be different
        from the :any:`PBOFile.data_size`.

        :Returns:
          The original size of the file.
        """
        if self.original_size == 0:
            return self.data_size

        return self.original_size

    def type(self) -> str:
        """Get the type of the file.

        :Returns:
          A 4-character string representing the file type.
        """
        return "".join([
            c if ord(c) >= 32 and ord(c) < 127 else " "
            for c in f"{self.mime_type.decode('ascii', errors='replace'):<4}"
        ])

    def invalid(self) -> bool:
        if INVALID_FILENAME_RE.search(self.filename) is not None:
            return True

        for segment in self.split_filename():
            if RESERVED_FILENAME_RE.match(segment) is not None:
                return True

        return False

    def obfuscated(self) -> bool:
        return self.invalid() and self.filename.endswith(b".c")

    def deobfuscated_split(self, index: int) -> list[bytes]:
        segments = []
        for segment in self.split_filename():
            if INVALID_FILENAME_RE.search(segment) \
                    or RESERVED_FILENAME_RE.match(segment) is not None:
                segments.append(f"deobfs{index:05}.c".encode())
                break
            segments.append(segment.rstrip(b" "))

        return segments

    def deobfuscated_filename(self, index: int) -> str:
        return normalize_filename(self.deobfuscated_split(index))
