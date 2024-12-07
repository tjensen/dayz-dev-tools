import argparse
import logging
import os
import pathlib
import subprocess
import sys

import dayz_dev_tools
from dayz_dev_tools import logging_configuration
from dayz_dev_tools import misc
from dayz_dev_tools import pbo_writer
from dayz_dev_tools import tools_directory


def _split_header(option: str) -> tuple[str, str]:
    header, value = option.split("=", maxsplit=1)
    return header, value


def main() -> None:
    parser = argparse.ArgumentParser(usage="%(prog)s [options] pbofile [files...]")
    parser.register("type", "header", _split_header)
    parser.add_argument(
        "-b", "--no-convert", action="store_true",
        help="Do not convert config.cpp files to config.bin files")
    parser.add_argument(
        "-C", "--chdir", metavar="DIR", help="Change to directory DIR before creating PBO")
    parser.add_argument("-D", "--debug", action="store_true", help="Enable debug logs")
    parser.add_argument(
        "-H", "--header", type="header", action="append", default=[], metavar="HEADER=VALUE",
        help="Add a header to the PBO")
    parser.add_argument(
        "-P", "--pattern", action="append", default=[], metavar="GLOB",
        help="Add files matching GLOB")
    parser.add_argument(
        "-s", "--sign", metavar="KEYFILE",
        help="Sign the PBO with the provided private key")
    parser.add_argument("-V", "--version", action="version", version=dayz_dev_tools.version)
    parser.add_argument("pbofile", help="The PBO file to create")
    parser.add_argument("files", nargs="*", default=[], help="Files to add to the PBO")
    args = parser.parse_args()

    logging_configuration.configure_logging(debug=args.debug)

    try:
        with misc.chdir(args.chdir or "."):
            tools_dir = tools_directory.tools_directory()

            cfgconvert = None
            if not args.no_convert and tools_dir is not None:
                cfgconvert = os.path.join(tools_dir, "bin", "CfgConvert", "CfgConvert.exe")

            writer = pbo_writer.PBOWriter(cfgconvert=cfgconvert)

            writer.add_header(
                "product",
                f"DayZ Dev Tools v{dayz_dev_tools.version}"
                " - https://dayz-dev-tools.readthedocs.io/en/stable/")

            for header in args.header:
                logging.info("Adding header: `%s` = `%s`", header[0], header[1])
                writer.add_header(*header)

            for pattern in args.pattern:
                anchor = pathlib.Path(pathlib.Path(pattern).anchor)
                rest = pathlib.Path(pattern).relative_to(anchor)
                for path in anchor.glob(str(rest)):
                    if not path.is_dir():
                        logging.info("Adding file `%s`", path)
                        writer.add_file(path)

            for file in args.files:
                path = pathlib.Path(file)
                if path.is_dir():
                    for subpath in path.glob("**/*"):
                        if not subpath.is_dir():
                            logging.info("Adding file `%s`", subpath)
                            writer.add_file(subpath)
                else:
                    logging.info("Adding file `%s`", path)
                    writer.add_file(path)

            with open(args.pbofile, "wb") as output:
                logging.info("Writing PBO file `%s`", args.pbofile)
                writer.write(output)

            if args.sign is not None:
                if tools_dir is None:
                    raise Exception("Unable to find DayZ Tools directory!")

                logging.info(
                    "Signing PBO file `%s` using private key `%s`", args.pbofile, args.sign)
                subprocess.run(
                    [
                        os.path.join(tools_dir, "bin", "DsUtils", "DSSignFile.exe"),
                        args.sign,
                        args.pbofile
                    ],
                    check=True)

        logging.info("Done!")

    except Exception as error:
        logging.debug("Uncaught exception in main", exc_info=True)
        logging.error("%s: %s", type(error).__name__, error)
        sys.exit(1)


if __name__ == "__main__":
    main()
