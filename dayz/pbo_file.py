import dataclasses
import ntpath
import os
import typing

from dayz import pbo_file_reader


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

        output_file.write(self.content_reader.read(self.data_size))

    def normalized_filename(self) -> bytes:
        return os.path.join(*self.split_filename())

    def split_filename(self) -> typing.List[bytes]:
        def rec_split(s: bytes) -> typing.List[bytes]:
            rest, tail = ntpath.split(s)
            if len(rest) == 0:
                return [tail]
            return rec_split(rest) + [tail]
        return rec_split(self.filename)
