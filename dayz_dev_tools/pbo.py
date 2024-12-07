import argparse
import logging
import pathlib
import sys

from dayz_dev_tools import logging_configuration
from dayz_dev_tools import pbo_writer


def _split_header(option: str) -> tuple[str, str]:
    header, value = option.split("=", maxsplit=1)
    return header, value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.register("type", "header", _split_header)
    parser.add_argument("-D", "--debug", action="store_true", help="Enable debug logs")
    parser.add_argument(
        "-H", "--header", type="header", action="append", default=[], metavar="HEADER=VALUE",
        help="Add a header to the PBO")
    parser.add_argument(
        "-P", "--pattern", action="append", default=[], metavar="GLOB",
        help="Add files matching GLOB")
    parser.add_argument("pbofile", help="The PBO file to create")
    parser.add_argument("files", nargs="*", default=[], help="Files to add to the PBO")
    args = parser.parse_args()

    logging_configuration.configure_logging(debug=args.debug)

    try:
        writer = pbo_writer.PBOWriter()

        for header in args.header:
            writer.add_header(*header)

        for pattern in args.pattern:
            anchor = pathlib.Path(pattern).anchor
            rest = pathlib.Path(pattern).relative_to(anchor)
            for path in pathlib.Path(anchor).glob(rest):
                writer.add_file(path)

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

    except Exception as error:
        logging.debug("Uncaught exception in main", exc_info=True)
        logging.error(f"{type(error).__name__}: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
