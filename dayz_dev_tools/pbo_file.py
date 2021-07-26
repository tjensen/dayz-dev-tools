import dataclasses
import ntpath
import os
import typing

from dayz_dev_tools import expand
from dayz_dev_tools import pbo_file_reader


@dataclasses.dataclass
class PBOFile():
    filename: bytes
    mime_type: bytes
    original_size: int
    reserved: int
    time_stamp: int
    data_size: int
    content_reader: typing.Optional[pbo_file_reader.PBOFileReader] = None

    def unpack(self, output_file: typing.BinaryIO) -> None:
        assert self.content_reader is not None

        if self.original_size != 0 and self.original_size != self.data_size:
            self.content_reader.seek(self.data_size - 4)
            expected_checksum = self.content_reader.readuint()

            expanded = expand.expand(self.content_reader.subreader(0, self.data_size - 4))

            actual_checksum = sum(expanded)

            if actual_checksum != expected_checksum:
                raise Exception(
                    f"Checksum mismatch ({actual_checksum:#x} != {expected_checksum:#x})")

            output_file.write(expanded)
        else:
            output_file.write(self.content_reader.read(self.data_size))

    def normalized_filename(self) -> str:
        return os.path.join(*self.split_filename()).decode(errors="replace")

    def split_filename(self) -> typing.List[bytes]:
        def rec_split(s: bytes) -> typing.List[bytes]:
            rest, tail = ntpath.split(s)
            if len(rest) == 0:
                return [tail]
            return rec_split(rest) + [tail]
        return rec_split(self.filename)

    def unpacked_size(self) -> int:
        if self.original_size == 0:
            return self.data_size

        return self.original_size

    def type(self) -> str:
        return "".join([
            c if ord(c) >= 32 and ord(c) < 127 else " "
            for c in f"{self.mime_type.decode('ascii', errors='replace'):<4}"
        ])
