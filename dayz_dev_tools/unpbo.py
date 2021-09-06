import argparse
import logging
import os
import sys

import dayz_dev_tools
from dayz_dev_tools import extract_pbo
from dayz_dev_tools import list_pbo
from dayz_dev_tools import logging_configuration
from dayz_dev_tools import pbo_reader
from dayz_dev_tools import tools_directory


def main() -> None:
    parser = argparse.ArgumentParser(
        description="View or extract a PBO archive",
        epilog="See also: https://community.bistudio.com/wiki/PBO_File_Format")
    parser.add_argument(
        "-l", "--list", action="store_true", help="List contents of the PBO archive")
    parser.add_argument(
        "-b", "--no-convert", action="store_true",
        help="Do not convert config.bin files to config.cpp files")
    parser.add_argument(
        "-d", "--deobfuscate", action="store_true", help="Attempt to deobfuscate extracted files")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-D", "--debug", action="store_true", help="Enable debug logs")
    parser.add_argument("-V", "--version", action="version", version=dayz_dev_tools.version)
    parser.add_argument("pbofile", help="The PBO archive to read")
    parser.add_argument("files", nargs="*", help="Files to extract from the PBO archive")
    args = parser.parse_args()

    logging_configuration.configure_logging(debug=args.debug)

    try:
        with open(args.pbofile, "rb") as pbo_file:
            reader = pbo_reader.PBOReader(pbo_file)

            if args.list:
                list_pbo.list_pbo(reader, verbose=args.verbose)
            else:
                cfgconvert = None
                if args.no_convert is False:
                    tools_dir = tools_directory.tools_directory()
                    if tools_dir is not None:
                        cfgconvert = os.path.join(tools_dir, "bin", "CfgConvert", "CfgConvert.exe")

                extract_pbo.extract_pbo(
                    reader, args.files,
                    verbose=args.verbose, deobfuscate=args.deobfuscate, cfgconvert=cfgconvert)
    except Exception as error:
        logging.debug("Uncaught exception in main", exc_info=True)
        logging.error(f"{type(error).__name__}: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
