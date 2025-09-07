import io
import os
import pathlib
import re
import typing

from dayz_dev_tools import config_cpp
from dayz_dev_tools import pbo_file
from dayz_dev_tools import pbo_reader


OBFUSCATE_RE = re.compile(
    b'^(?:(?://[^\\r\\n]*|/\\*(?:\\*(?!\\/)|[^*])*\\*/)\\r\\n)?#include "([^"]+)"(?:\\r\\n)?$')


_deobfs_count = 0


def _deobfuscate(
    out_file: typing.BinaryIO,
    pbofile: pbo_file.PBOFile,
    reader: pbo_reader.PBOReader,
    prefix: typing.Optional[bytes],
    verbose: bool,
    ignored: list[bytes]
) -> bool:
    buffer = io.BytesIO()
    pbofile.unpack(buffer)
    content = buffer.getvalue()

    if (match := OBFUSCATE_RE.match(content)) is None:
        out_file.write(content)
        return True

    target_filename = match.group(1)

    if prefix is not None:
        target_filename = target_filename.removeprefix(prefix + b"\\")

    unobfuscated = reader.file(target_filename)

    if unobfuscated is None:
        out_file.write(content)
        return False

    ignored.append(unobfuscated.filename)

    return _deobfuscate(out_file, unobfuscated, reader, prefix, verbose, ignored)


def _extract_file(
    reader: pbo_reader.PBOReader, pbofile: pbo_file.PBOFile, verbose: bool, deobfuscate: bool,
    cfgconvert: typing.Optional[str], ignored: list[bytes]
) -> None:
    global _deobfs_count

    if deobfuscate and (
            (pbofile.filename in ignored)
            or (pbofile.invalid() and not pbofile.filename.endswith(b".c"))):
        if verbose:
            print(f"Skipping obfuscation file: {pbofile.normalized_filename()}")
        return

    prefix = reader.prefix()

    parts = pbofile.deobfuscated_split(_deobfs_count) if deobfuscate else pbofile.split_filename()

    if len(parts) == 0 or len(parts[-1]) == 0 or parts == [pbofile.prefix]:
        print("Skipping empty obfuscation filename")
        return

    if len(parts) > 1:
        os.makedirs(os.path.join(*parts[:-1]), exist_ok=True)

    if parts[-1].lower() == b"config.bin" and cfgconvert is not None:
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

    renamed_filename: typing.Optional[str] = None
    normalized = pbofile.normalized_filename()

    if deobfuscate and pbofile.obfuscated():
        normalized = renamed_filename = pbofile.deobfuscated_filename(_deobfs_count)
        _deobfs_count += 1

    with open(normalized, "w+b") as out_file:
        if verbose:
            if renamed_filename is None:
                print(f"Extracting {pbofile.normalized_filename()}")
            else:
                print(f"Extracting {pbofile.normalized_filename()} -> {renamed_filename}")

        if deobfuscate:
            if not _deobfuscate(out_file, pbofile, reader, prefix, verbose, ignored):
                if verbose:
                    print(f"Unable to deobfuscate {pbofile.normalized_filename()}")

        else:
            pbofile.unpack(out_file)


def extract_pbo(
    reader: pbo_reader.PBOReader,
    files_to_extract: list[str],
    *,
    verbose: bool,
    deobfuscate: bool,
    cfgconvert: typing.Optional[str],
    pattern: typing.Optional[str] = None
) -> None:
    """Extract one or more files contained in a PBO archive.

    :Parameters:
      - `reader`: A :class:`~dayz_dev_tools.pbo_reader.PBOReader` instance representing the PBO
        archive containing the file(s) to be extracted.
      - `files_to_extract`: A list of fully-qualified paths of the files to be extracted.
      - `verbose`: When `True`, print the paths of the files being extracted to stdout.
      - `deobfuscate`: When `True`, **attempt** to deobfuscate obfuscated script files.
      - `cfgconvert`: Location of the DayZ Tools CfgConvert.exe binary, or None if binarized
        configs should not be converted.
      - `pattern`: Only extract filenames matching this glob pattern, or None if all files should
        be extracted.

    .. note:: Deobfuscation may not always work, as obfuscation techniques may evolve over time.
    """
    global _deobfs_count
    _deobfs_count = 0

    ignored: list[bytes] = []

    if len(files_to_extract) == 0:
        for file in reader.files():
            if pattern is not None and not pathlib.PureWindowsPath(
                    file.normalized_filename()).full_match(pattern):
                continue
            _extract_file(reader, file, verbose, deobfuscate, cfgconvert, ignored)

    else:
        for file_to_extract in files_to_extract:
            pbofile = reader.file(file_to_extract)

            if pbofile is None:
                raise Exception(f"File not found: {file_to_extract}")

            _extract_file(reader, pbofile, verbose, deobfuscate, cfgconvert, [])
