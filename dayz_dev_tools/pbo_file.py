import dataclasses
import ntpath
import os
import typing

from dayz_dev_tools import expand
from dayz_dev_tools import pbo_file_reader


@dataclasses.dataclass
class PBOFile:
    """Interface for accessing a file contained within a PBO archive. Instances should be obtained
    using :meth:`dayz_dev_tools.pbo_reader.PBOReader.file`."""
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
            self.content_reader.seek(self.data_size - 4)
            expected_checksum = self.content_reader.readuint()

            expanded = expand.expand(
                self.content_reader.subreader(0, self.data_size - 4), self.original_size)

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
        return os.path.join(*self.split_filename()).decode(errors="replace")

    def split_filename(self) -> typing.List[bytes]:
        """Get the file's name as a ``list``, where each element in the list represents a component
        of the file's path.

        :Returns:
          A list of path components.
        """
        def rec_split(s: bytes) -> typing.List[bytes]:
            rest, tail = ntpath.split(s)
            if len(rest) == 0:
                return [tail]
            return rec_split(rest) + [tail]
        return rec_split(self.filename)

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
