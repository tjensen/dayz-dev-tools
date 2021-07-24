import argparse
import os
import sys
import typing

from dayz import pbo_reader


def extract_pbo(reader: pbo_reader.PBOReader, destdir: str) -> None:
    for file in reader.files():
        parts = os.path.split(file.filename)
        os.makedirs(os.path.join(destdir.encode(), *parts[:-1]), exist_ok=True)

        with open(os.path.join(destdir.encode(), *parts), "wb") as out_file:
            file.unpack(out_file)


def list_pbo(reader: pbo_reader.PBOReader) -> None:
    for file in reader.files():
        print(file.filename.decode(errors="replace"))


def main(argv: typing.List[str]) -> None:
    parser = argparse.ArgumentParser(description="View or extract a PBO file")
    parser.add_argument("-l", "--list", action="store_true", help="List contents of the PBO")
    parser.add_argument("pbofile", help="The PBO file to read")
    parser.add_argument("dest", nargs="?", help="The output destination if extracting files")
    args = parser.parse_args(argv[1:])

    if args.dest is None:
        args.dest = os.path.splitext(os.path.basename(argv[1]))[0]

    with open(args.pbofile, "rb") as pbo_file:
        reader = pbo_reader.PBOReader(pbo_file)

        if args.list:
            list_pbo(reader)
        else:
            extract_pbo(reader, args.dest)


if __name__ == "__main__":
    main(sys.argv)
