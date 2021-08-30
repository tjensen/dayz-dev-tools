import argparse
import os
import subprocess
import typing

from dayz_dev_tools import launch_settings
from dayz_dev_tools import server_config


def _resolve_mod(mod: str, workshop_directory: str) -> str:
    if mod.startswith("@"):
        return os.path.join(workshop_directory, mod)
    else:
        return mod


def _mod_parameter(option: str, mods: typing.List[str], workshop_directory: str) -> str:
    mods = [_resolve_mod(mod, workshop_directory) for mod in mods]

    return f"-{option}={';'.join(mods)}"


def run_server(settings: launch_settings.LaunchSettings) -> None:
    args = [
        settings.executable(),
        f"-config={settings.config()}"
    ]

    if settings.profile() is not None:
        args.append(f"-profiles={settings.profile()}")

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

    config = server_config.load(args.config)

    settings = launch_settings.LaunchSettings(config)

    for bundle in args.bundles:
        settings.load_bundle(bundle)

    run_server(settings)


if __name__ == "__main__":
    main()
