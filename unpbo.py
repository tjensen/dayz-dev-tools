import argparse
import datetime
import os
import sys
import typing

from dayz import pbo_file
from dayz import pbo_reader


def _extract_file(pbofile: pbo_file.PBOFile) -> None:
    parts = pbofile.split_filename()

    if len(parts) > 1:
        os.makedirs(os.path.join(*parts[:-1]), exist_ok=True)

    with open(os.path.join(*parts), "wb") as out_file:
        pbofile.unpack(out_file)


def extract_pbo(reader: pbo_reader.PBOReader, files_to_extract: typing.List[str]) -> None:
    if len(files_to_extract) == 0:
        for file in reader.files():
            _extract_file(file)

    else:
        for file_to_extract in files_to_extract:
            pbofile = reader.file(file_to_extract)

            if pbofile is None:
                raise Exception(f"File not found: {file_to_extract}")

            _extract_file(pbofile)


def list_pbo(reader: pbo_reader.PBOReader, *, verbose: bool) -> None:
    if verbose:
        print("Headers:")
        print("--------")
        for key, value in reader.headers():
            print(f"{key.decode(errors='replace')} = {value.decode(errors='replace')}")
        print()
        print(" Original  Type    Size        Date    Time   Name")
        print("---------  ----  ---------  ---------- -----  ----")
    else:
        print(" Original     Date    Time   Name")
        print("---------  ---------- -----  ----")

    for file in reader.files():
        timestamp = datetime.datetime.fromtimestamp(file.time_stamp).strftime("%Y-%m-%d %H:%M")

        if verbose:
            print(
                f"{file.unpacked_size():9}  {file.type()}  {file.data_size:9}  {timestamp}"
                f"  {file.normalized_filename()}")
        else:
            print(f"{file.unpacked_size():9}  {timestamp}  {file.normalized_filename()}")


def main(argv: typing.List[str]) -> None:
    parser = argparse.ArgumentParser(description="View or extract a PBO file")
    parser.add_argument("-l", "--list", action="store_true", help="List contents of the PBO")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("pbofile", help="The PBO file to read")
    parser.add_argument("files", nargs="*", help="Files to extract from the PBO")
    args = parser.parse_args(argv[1:])

    with open(args.pbofile, "rb") as pbo_file:
        reader = pbo_reader.PBOReader(pbo_file)

        if args.list:
            list_pbo(reader, verbose=args.verbose)
        else:
            extract_pbo(reader, args.files)


if __name__ == "__main__":
    main(sys.argv)
