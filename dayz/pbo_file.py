import dataclasses
import typing


class ContentReader(typing.Protocol):
    def read(self, count: int) -> bytes:
        ...


@dataclasses.dataclass
class PBOFile():
    filename: bytes
    mime_type: bytes
    original_size: int
    reserved: int
    time_stamp: int
    data_size: int
    content_reader: ContentReader

    def unpack(self, output_file: typing.BinaryIO) -> None:
        output_file.write(self.content_reader.read(self.data_size))
