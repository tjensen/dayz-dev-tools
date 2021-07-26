import math
import struct
import typing

from dayz_dev_tools import pbo_file_reader


def _log(msg: str) -> None:
    print(msg)


def _nolog(msg: str) -> None:
    pass


def expand(
    reader: pbo_file_reader.PBOFileReader, *, debug: typing.Callable[[str], None] = _nolog
) -> bytes:
    result = b""

    while not reader.eof():
        flagbits = reader.read(1)[0]

        debug(f"Flagbits = {flagbits:08b}")

        for bit in range(8):
            if reader.eof():
                break

            if flagbits >> bit & 1 == 1:
                result += reader.read(1)
            else:
                debug(f"Buffer = {repr(result)}")

                pointer = struct.unpack("<H", reader.read(2))[0]
                debug(f"pointer = {pointer:#04x}")
                rpos = len(result) - ((pointer & 0xff) + ((pointer & 0xf000) >> 4))
                rlen = ((pointer >> 8) & 0xf) + 3
                debug(f"rpos = {rpos}, rlen = {rlen}, FL={len(result)}")

                if rpos < 0:
                    result += bytes(b" " * rlen)
                elif rpos + rlen > len(result):
                    chunk = result[rpos:]
                    debug(f"chunk len={len(chunk)} ({repr(chunk)})")
                    result += (chunk * math.ceil(rlen / len(chunk)))[:rlen]
                else:
                    result += result[rpos:rpos + rlen]

    return result
