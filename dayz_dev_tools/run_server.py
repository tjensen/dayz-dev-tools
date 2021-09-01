import argparse
import logging
import os
import subprocess
import time
import typing

from dayz_dev_tools import keys
from dayz_dev_tools import launch_settings
from dayz_dev_tools import script_logs
from dayz_dev_tools import server_config


def _resolve_mod(mod: str, workshop_directory: str) -> str:
    if mod.startswith("@"):
        return os.path.join(workshop_directory, mod)
    else:
        return mod


def _copy_keys(mod_dirs: typing.List[str], keys_dir: str) -> None:
    for mod_dir in mod_dirs:
        keys.copy_keys(os.path.join(mod_dir, "keys"), keys_dir)


def _mod_parameter(option: str, mods: typing.List[str], workshop_directory: str) -> str:
    mods = [_resolve_mod(mod, workshop_directory) for mod in mods]

    _copy_keys(mods, "keys")

    return f"-{option}={';'.join(mods)}"


def run_server(settings: launch_settings.LaunchSettings, *, wait: bool) -> None:
    args = [
        settings.executable(),
        f"-config={settings.config()}"
    ]

    if settings.profile() is not None:
        args.append(f"-profiles={settings.profile()}")

    if settings.mission() is not None:
        args.append(f"-mission={settings.mission()}")

    if len(settings.mods()) > 0:
        args.append(_mod_parameter("mod", settings.mods(), settings.workshop_directory()))

    if len(settings.server_mods()) > 0:
        args.append(
            _mod_parameter("servermod", settings.server_mods(), settings.workshop_directory()))

    logging.info(f"Running server with: {args}")

    if wait:
        profile = settings.profile()
        assert profile is not None

        previous_log_name = script_logs.newest(profile)

        with subprocess.Popen(args) as proc:
            logging.info("Server started with PID {proc.pid}; waiting for new script log...")
            while (script_logs.newest(profile)) == previous_log_name:
                time.sleep(1)

            logging.info("Streaming script log:")

    else:
        proc = subprocess.Popen(args)

        logging.info(f"Server started with PID {proc.pid}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-wait", action="store_true", help="Do not wait for server to finish running")
    parser.add_argument(
        "-c", "--config", default="server.toml", help="Read configuration from this file")
    parser.add_argument(
        "bundles", nargs="*", metavar="BUNDLE", help="The name of a function in the bundles module")
    args = parser.parse_args()

    config = server_config.load(args.config)

    settings = launch_settings.LaunchSettings(config)

    for bundle in args.bundles:
        settings.load_bundle(bundle)

    run_server(settings, wait=not args.no_wait)


if __name__ == "__main__":
    main()
