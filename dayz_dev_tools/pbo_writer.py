import dataclasses
import fnmatch
import hashlib
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


class _HashWriter:
    def __init__(self, output: typing.BinaryIO) -> None:
        self.output = output
        self.hash = hashlib.sha1()

    def write(self, data: bytes) -> int:
        self.hash.update(data)
        return self.output.write(data)

    def finalize(self) -> int:
        return self.output.write(b"\x00" + self.hash.digest())


class PBOWriter:
    """Interface for writing a PBO archive."""
    def __init__(self, *, cfgconvert: typing.Optional[str]) -> None:
        """Create a new :class:`PBOWriter` instance.

        :Parameters:
          - `cfgconvert`: The location of the DayZ Tools ``CfgConvert.exe`` program, or ``None`` if
            ``config.cpp`` files should not be binarized.
        """
        self.cfgconvert = cfgconvert
        self.headers: list[tuple[bytes, bytes]] = []
        self.entries: list[_Entry] = []

    @typing.overload
    def add_header(self, name: bytes, value: bytes) -> None:
        """Add a header to the PBO archive.

        :Parameters:
          - `name`: The name of the header.
          - `value`: The value of the header.
        """
        pass

    @typing.overload
    def add_header(self, name: str, value: str) -> None:
        """Add a header to the PBO archive.

        :Parameters:
          - `name`: The name of the header.
          - `value`: The value of the header.
        """
        pass

    def add_header(self, name: typing.Union[str, bytes], value: typing.Union[str, bytes]) -> None:
        self.headers.append((
            name.encode("utf8") if hasattr(name, "encode") else name,
            value.encode("utf8") if hasattr(value, "encode") else value
        ))

    def add_file(self, path: pathlib.Path) -> None:
        """Add a file to the PBO archive.

        :Parameters:
          - `path`: A ``pathlib.Path`` instance containing the location of the file to be added.
        """
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
        """Create the PBO archive.

        :Parameters:
          - `output`: A binary file-like object to receive the PBO archive contents.
        """
        writer = _HashWriter(output)
        writer.write(b"\x00")
        writer.write(b"sreV\x00")
        writer.write(b"\x00" * 15)

        for header in self.headers:
            writer.write(header[0] + b"\x00" + header[1] + b"\x00")

        writer.write(b"\x00")

        for entry in self.entries:
            writer.write(entry.stored_path.encode("utf8") + b"\x00")
            writer.write(struct.pack("LLLLL", 0, entry.size, 0, int(entry.mtime), entry.size))

        writer.write(b"\x00" * 21)

        for entry in self.entries:
            if entry.contents is None:
                with open(entry.read_path, "rb") as infile:
                    contents = infile.read()
            else:
                contents = entry.contents

            if len(contents) != entry.size:
                raise Exception(f"File size mismatch {len(contents)} != {entry.size}")

            writer.write(contents)

        writer.finalize()
