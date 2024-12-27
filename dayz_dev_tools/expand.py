from dayz_dev_tools import pbo_file_reader
import dayz_dev_tools_rust


def expand(reader: pbo_file_reader.PBOFileReader, outsize: int) -> bytes:
    inbuffer = reader.read(reader.size)
    return dayz_dev_tools_rust.expand(inbuffer, outsize)
