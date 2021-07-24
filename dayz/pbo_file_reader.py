import typing


class PBOFileReader():
    def __init__(self, content_file: typing.BinaryIO, offset: int, size: int) -> None:
        self.content_file = content_file
        self.offset = offset
        self.pos = 0
        self.size = size

    def read(self, size: int) -> bytes:
        self.content_file.seek(self.offset + self.pos)

        result = self.content_file.read(min(size, self.size - self.pos))

        self.pos += len(result)

        return result

    def readz(self) -> bytes:
        self.content_file.seek(self.offset + self.pos)

        result = b""

        while self.pos < self.size:
            byte = self.content_file.read(1)
            self.pos += len(byte)

            if byte[0] == 0:
                return result

            result += byte

        return result
