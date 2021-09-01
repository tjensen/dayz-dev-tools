import os
import re
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
