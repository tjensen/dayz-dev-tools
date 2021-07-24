import dataclasses
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
