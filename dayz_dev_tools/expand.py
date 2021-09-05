from dayz_dev_tools import pbo_file_reader
import dayz_dev_tools_ext  # type: ignore[import]


def expand(reader: pbo_file_reader.PBOFileReader, outsize: int) -> bytes:
    inbuffer = reader.read(reader.size)
    outbuffer = bytearray(outsize)
    dayz_dev_tools_ext.expand(outbuffer, inbuffer)

    return bytes(outbuffer)
