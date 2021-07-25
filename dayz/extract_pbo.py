import os
import typing

from dayz import pbo_file
from dayz import pbo_reader


def _extract_file(pbofile: pbo_file.PBOFile, verbose: bool) -> None:
    parts = pbofile.split_filename()

    if len(parts) > 1:
        os.makedirs(os.path.join(*parts[:-1]), exist_ok=True)

    with open(os.path.join(*parts), "wb") as out_file:
        if verbose:
            print(f"Extracting {pbofile.normalized_filename()}")
        pbofile.unpack(out_file)


def extract_pbo(
    reader: pbo_reader.PBOReader, files_to_extract: typing.List[str], *, verbose: bool
) -> None:
    if len(files_to_extract) == 0:
        for file in reader.files():
            _extract_file(file, verbose)

    else:
        for file_to_extract in files_to_extract:
            pbofile = reader.file(file_to_extract)

            if pbofile is None:
                raise Exception(f"File not found: {file_to_extract}")

            _extract_file(pbofile, verbose)
