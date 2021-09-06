import io
import os
import re
import typing

from dayz_dev_tools import config_cpp
from dayz_dev_tools import pbo_file
from dayz_dev_tools import pbo_reader


INVALID_FILENAME_RE = re.compile(b"[\t?*\x80-\xff]")

OBFUSCATE_RE = re.compile(
    b'^(?:(?://[^\\r\\n]*|/\\*(?:\\*(?!\\/)|[^*])*\\*/)\\r\\n)?#include "([^"]+)"\\r\\n$')


def _invalid_filename(filename: bytes) -> bool:
    return INVALID_FILENAME_RE.search(filename) is not None


def _extract_file(
    reader: pbo_reader.PBOReader, pbofile: pbo_file.PBOFile, verbose: bool, deobfuscate: bool,
    cfgconvert: typing.Optional[str], ignored: typing.List[bytes]
) -> None:
    if deobfuscate and ((pbofile.filename in ignored) or _invalid_filename(pbofile.filename)):
        if verbose:
            print(f"Skipping obfuscation file: {pbofile.normalized_filename()}")
        return

    prefix = reader.prefix()

    parts = pbofile.split_filename()

    if len(parts) > 1:
        os.makedirs(os.path.join(*parts[:-1]), exist_ok=True)

    if parts[-1] == b"config.bin" and cfgconvert is not None:
        converted_filename = os.path.join(
            os.path.dirname(pbofile.normalized_filename()), "config.cpp")

        if verbose:
            print(f"Converting {pbofile.normalized_filename()} -> {converted_filename}")

        buffer = io.BytesIO()
        pbofile.unpack(buffer)
        try:
            cpp_content = config_cpp.bin_to_cpp(buffer.getvalue(), cfgconvert)
            with open(converted_filename, "w+b") as out_file:
                out_file.write(cpp_content)
                return
        except Exception as error:
            print(f"Failed to convert {pbofile.normalized_filename()}: {error}")

    with open(os.path.join(*parts), "w+b") as out_file:
        if verbose:
            print(f"Extracting {pbofile.normalized_filename()}")

        if deobfuscate:
            buffer = io.BytesIO()
            pbofile.unpack(buffer)
            content = buffer.getvalue()

            if (match := OBFUSCATE_RE.match(content)) is not None:
                target_filename = match.group(1)

                if prefix is not None and not target_filename.startswith(prefix + b"\\"):
                    target_filename = prefix + b"\\" + target_filename

                unobfuscated = reader.file(target_filename)

                if unobfuscated is None:
                    if verbose:
                        print(f"Unable to deobfuscate {pbofile.normalized_filename()}")
                    out_file.write(content)
                else:
                    ignored.append(unobfuscated.filename)

                    unobfuscated.unpack(out_file)
            else:
                out_file.write(content)

        else:
            pbofile.unpack(out_file)


def extract_pbo(
    reader: pbo_reader.PBOReader, files_to_extract: typing.List[str], *, verbose: bool,
    deobfuscate: bool, cfgconvert: typing.Optional[str]
) -> None:
    """Extract one or more files contained in a PBO archive.

    :Parameters:
      - `reader`: A :class:`~dayz_dev_tools.pbo_reader.PBOReader` instance representing the PBO
        archive containing the file(s) to be extracted.
      - `files_to_extract`: A list of fully-qualified paths of the files to be extracted.
      - `verbose`: When `True`, print the paths of the files being extracted to stdout.
      - `deobfuscate`: When `True`, **attempt** to deobfuscate obfuscated script files.

    .. note:: Deobfuscation may not always work, as obfuscation techniques may evolve over time.
    """
    ignored: typing.List[bytes] = []

    if len(files_to_extract) == 0:
        for file in reader.files():
            _extract_file(reader, file, verbose, deobfuscate, cfgconvert, ignored)

    else:
        for file_to_extract in files_to_extract:
            pbofile = reader.file(file_to_extract)

            if pbofile is None:
                raise Exception(f"File not found: {file_to_extract}")

            _extract_file(reader, pbofile, verbose, deobfuscate, cfgconvert, [])
