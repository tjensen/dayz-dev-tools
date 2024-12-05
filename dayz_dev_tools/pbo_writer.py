import pathlib
import struct
import typing


def _write_file_entry(output: typing.BinaryIO, path: pathlib.Path, size: int, mtime: int) -> None:
    output.write("\\".join(path.relative_to(path.anchor).parts).encode("utf8") + b"\x00")
    output.write(struct.pack("LLLLL", 0, size, 0, mtime, size))


class PBOWriter:
    def __init__(self) -> None:
        self.headers: list[tuple[bytes, bytes]] = []
        self.paths: list[pathlib.Path] = []

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
        self.paths.append(path)

    def write(self, output: typing.BinaryIO) -> None:
        output.write(b"\x00")
        output.write(b"sreV\x00")
        output.write(b"\x00" * 15)

        for header in self.headers:
            output.write(header[0] + b"\x00" + header[1] + b"\x00")

        output.write(b"\x00")

        for path in self.paths:
            info = path.stat()
            _write_file_entry(output, path, info.st_size, int(info.st_mtime))

        _write_file_entry(output, pathlib.Path(""), 0, 0)

        for path in self.paths:
            with open(path, "rb") as infile:
                output.write(infile.read())
