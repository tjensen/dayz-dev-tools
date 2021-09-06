import argparse
import os

import dayz_dev_tools
from dayz_dev_tools import extract_pbo
from dayz_dev_tools import list_pbo
from dayz_dev_tools import pbo_reader
from dayz_dev_tools import tools_directory


def main() -> None:
    parser = argparse.ArgumentParser(
        description="View or extract a PBO file",
        epilog="See also: https://community.bistudio.com/wiki/PBO_File_Format")
    parser.add_argument("-l", "--list", action="store_true", help="List contents of the PBO")
    parser.add_argument(
        "-d", "--deobfuscate", action="store_true", help="Attempt to deobfuscate extracted files")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-V", "--version", action="version", version=dayz_dev_tools.version)
    parser.add_argument("pbofile", help="The PBO file to read")
    parser.add_argument("files", nargs="*", help="Files to extract from the PBO")
    args = parser.parse_args()

    try:
        with open(args.pbofile, "rb") as pbo_file:
            reader = pbo_reader.PBOReader(pbo_file)

            if args.list:
                list_pbo.list_pbo(reader, verbose=args.verbose)
            else:
                tools_dir = tools_directory.tools_directory()
                if tools_dir is None:
                    cfgconvert = None
                else:
                    cfgconvert = os.path.join(tools_dir, "bin", "CfgConvert", "CfgConvert.exe")

                extract_pbo.extract_pbo(
                    reader, args.files,
                    verbose=args.verbose, deobfuscate=args.deobfuscate, cfgconvert=cfgconvert)
    except Exception as error:
        print(f"ERROR: {error}")


if __name__ == "__main__":
    main()
