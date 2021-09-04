import logging
import os
import shutil


def copy_keys(source: str, destination: str) -> None:
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
