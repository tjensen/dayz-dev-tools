import dataclasses
import fnmatch
import pathlib
import struct
import typing

from dayz_dev_tools import config_cpp


@dataclasses.dataclass
class _Entry:
    read_path: pathlib.Path
    stored_path: str
    size: int
    mtime: int
    contents: typing.Optional[bytes]


class PBOWriter:
    def __init__(self, *, cfgconvert: typing.Optional[str]) -> None:
        self.cfgconvert = cfgconvert
        self.headers: list[tuple[bytes, bytes]] = []
        self.entries: list[_Entry] = []

    @typing.overload
    def add_header(self, name: bytes, value: bytes) -> None:
        pass

    @typing.overload
    def add_header(self, name: str, value: str) -> None:
        pass

    def add_header(self, name: typing.Union[str, bytes], value: typing.Union[str, bytes]) -> None:
        self.headers.append((
            name.encode("utf8") if hasattr(name, "encode") else name,
            value.encode("utf8") if hasattr(value, "encode") else value
        ))

    def add_file(self, path: pathlib.Path) -> None:
        info = path.stat()
        size = info.st_size

        if self.cfgconvert is not None and fnmatch.fnmatch(path.name, "config.cpp"):
            with open(path, "rb") as infile:
                contents = config_cpp.cpp_to_bin(infile.read(), self.cfgconvert)

            path = path.with_suffix(".bin")
            size = len(contents)

        else:
            contents = None

        self.entries.append(
            _Entry(
                read_path=path,
                stored_path="\\".join(path.relative_to(path.anchor).parts),
                size=size,
                mtime=info.st_mtime,
                contents=contents))

    def write(self, output: typing.BinaryIO) -> None:
        output.write(b"\x00")
        output.write(b"sreV\x00")
        output.write(b"\x00" * 15)

        for header in self.headers:
            output.write(header[0] + b"\x00" + header[1] + b"\x00")

        output.write(b"\x00")

        for entry in self.entries:
            output.write(entry.stored_path.encode("utf8") + b"\x00")
            output.write(struct.pack("LLLLL", 0, entry.size, 0, int(entry.mtime), entry.size))

        output.write(b"\x00" * 21)

        for entry in self.entries:
            if entry.contents is None:
                with open(entry.read_path, "rb") as infile:
                    output.write(infile.read())
            else:
                output.write(entry.contents)
