import argparse
import logging
import os
import subprocess
import typing

import toml

from dayz_dev_tools import launch_settings


def _resolve_mod(mod: str, workshop_directory: str) -> str:
    if mod.startswith("@"):
        return os.path.join(workshop_directory, mod)
    else:
        return mod


def _mod_parameter(option: str, mods: typing.List[str], workshop_directory: str) -> str:
    mods = [_resolve_mod(mod, workshop_directory) for mod in mods]

    return f"-{option}={';'.join(mods)}"


def run_server(settings: launch_settings.LaunchSettings) -> None:
    args = [settings.executable()]

    if len(settings.mods()) > 0:
        args.append(_mod_parameter("mod", settings.mods(), settings.workshop_directory()))

    if len(settings.server_mods()) > 0:
        args.append(
            _mod_parameter("servermod", settings.server_mods(), settings.workshop_directory()))

    with subprocess.Popen(args):
        pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", default="server.toml", help="Read configuration from this file")
    parser.add_argument(
        "bundles", nargs="*", metavar="BUNDLE", help="The name of a function in the bundles module")
    args = parser.parse_args()

    try:
        config = toml.load(args.config)
    except FileNotFoundError:
        logging.debug(f"Unable to read config file ({args.config})", exc_info=True)
        config = {}

    config.setdefault("server", {})
    config["server"].setdefault("executable", r".\DayZServer_x64.exe")
    config["server"].setdefault("bundles", "bundles.py")
    config.setdefault("workshop", {})
    config["workshop"].setdefault(
        "directory", r"C:\Program Files (x86)\Steam\steamapps\common\DayZ\!Workshop")

    settings = launch_settings.LaunchSettings(
        config["server"]["executable"],
        config["workshop"]["directory"],
        config["server"]["bundles"])

    for bundle in args.bundles:
        settings.load_bundle(bundle)

    run_server(settings)


if __name__ == "__main__":
    main()
