import os
import re
import time
import typing


SCRIPT_LOG_RE = re.compile(r"script_.*\.log$", re.IGNORECASE)


def newest(directory: str) -> typing.Optional[str]:
    logs = [
        os.path.join(directory, log)
        for log in os.listdir(directory)
        if SCRIPT_LOG_RE.match(log)
    ]

    newest = None
    newest_mtime = None

    for log in logs:
        mtime = os.lstat(log).st_mtime
        if newest is None or mtime > newest_mtime:
            newest = log
            newest_mtime = mtime

    return newest


def wait_for_new(directory: str, previous_log_name: typing.Optional[str]) -> typing.Optional[str]:
    while (new_log_name := newest(directory)) == previous_log_name:
        time.sleep(1)

    return new_log_name


def stream(
    outfile: typing.TextIO, infile: typing.TextIO, keep_streaming: typing.Callable[[], bool]
) -> None:
    while keep_streaming():
        content = infile.readline()

        if content != "":
            outfile.write(content)
        else:
            time.sleep(0.5)
