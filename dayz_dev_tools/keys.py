import logging
import os
import shutil


def copy_keys(source: str, destination: str) -> None:
    """Search for `*.bikey` (public key) files in one directory and copy them to another directory.

    :Parameters:
      - `source`: The source directory to be searched for ``*.bikey`` files.
      - `destination`: The destination directory where found ``*.bikey`` files are to be copied to.
        This directory will be created if it does not already exist.
    """
    try:
        keys = [filename for filename in os.listdir(source) if filename.lower().endswith(".bikey")]
    except FileNotFoundError:
        logging.debug(f"Error when searching for *.bikey files to copy at {source}", exc_info=True)
        keys = []

    if len(keys) == 0:
        logging.warning(f"No *.bikey files found in {source}")
        return

    os.makedirs(destination, exist_ok=True)

    for key in keys:
        shutil.copy2(os.path.join(source, key), destination)
