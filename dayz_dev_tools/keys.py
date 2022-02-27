import itertools
import logging
import os
import shutil


def copy_keys(source: str, destination: str) -> None:
    """Recursively search for `*.bikey` (public key) files in one directory and copy them to
    another directory.

    :Parameters:
      - `source`: The source directory to be searched for ``*.bikey`` files.
      - `destination`: The destination directory where found ``*.bikey`` files are to be copied to.
        This directory will be created if it does not already exist.
    """
    keys = list(itertools.chain.from_iterable(
        [os.path.join(root, file) for file in files if file.lower().endswith(".bikey")]
        for root, _, files in os.walk(source)
    ))

    if len(keys) == 0:
        logging.warning(f"No *.bikey files found in {source}")
        return

    os.makedirs(destination, exist_ok=True)

    for key in keys:
        shutil.copy2(key, destination)
