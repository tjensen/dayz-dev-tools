import argparse
import pathlib

from dayz_dev_tools import logging_configuration
from dayz_dev_tools import pbo_writer


def _split_header(option: str) -> tuple[str, str]:
    header, value = option.split("=", maxsplit=1)
    return header, value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.register("type", "header", _split_header)
    parser.add_argument(
        "-H", "--header", type="header", action="append", default=[], metavar="HEADER=VALUE",
        help="Add a header to the PBO")
    parser.add_argument("pbofile", help="The PBO file to create")
    parser.add_argument("files", nargs="*", default=[], help="Files to add to the PBO")
    args = parser.parse_args()

    logging_configuration.configure_logging(debug=False)

    writer = pbo_writer.PBOWriter()

    for header in args.header:
        writer.add_header(*header)

    for file in args.files:
        path = pathlib.Path(file)
        if path.is_dir():
            for subpath in path.glob("**/*"):
                if not subpath.is_dir():
                    writer.add_file(subpath)
        else:
            writer.add_file(path)

    with open(args.pbofile, "wb") as output:
        writer.write(output)


if __name__ == "__main__":
    main()
