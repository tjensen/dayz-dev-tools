import math

from dayz_dev_tools import pbo_file_reader


def expand(reader: pbo_file_reader.PBOFileReader) -> bytes:
    result = b""

    while not reader.eof():
        flagbits = reader.read(1)[0]

        for bit in range(8):
            if reader.eof():
                break

            if flagbits >> bit & 1 == 1:
                result += reader.read(1)
            else:
                pointer = reader.readuword()
                rpos = len(result) - ((pointer & 0xff) + ((pointer & 0xf000) >> 4))
                rlen = ((pointer >> 8) & 0xf) + 3

                if rpos < 0:
                    result += bytes(b" " * rlen)
                elif rpos + rlen > len(result):
                    chunk = result[rpos:]
                    result += (chunk * math.ceil(rlen / len(chunk)))[:rlen]
                else:
                    result += result[rpos:rpos + rlen]

    return result
