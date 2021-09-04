import os
import re
import time
import typing


SCRIPT_LOG_RE = re.compile(r"script_.*\.log$", re.IGNORECASE)


def newest(directory: str) -> typing.Optional[str]:
    """Find the newest ``script_*.log`` file in a directory.

    :Parameters:
      - `directory`: The directory to search for ``script_*.log`` files.

    :Returns:
      The filename of the newest ``script_*.log`` file, or ``None`` if no script logs could be
      found.
    """
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
    """Wait for a script log that is newer than another script log to be created in a directory.

    :Parameters:
      - `directory`: The directory to search for a newer ``script_*.log`` file.
      - `previous_log_name`: The current newest ``script_*.log`` file.

    :Returns:
      The filename of the newer ``script_*.log`` file, or ``None`` if no newer script logs are
      created.
    """
    while (new_log_name := newest(directory)) == previous_log_name:
        time.sleep(1)

    return new_log_name


def stream(
    outfile: typing.TextIO, infile: typing.TextIO, keep_streaming: typing.Callable[[], bool]
) -> None:
    """Stream the contents of a log file to another file.

    :Parameters:
      - `outfile`: A file-like object to stream the log file contents to.
      - `infile`: A file-like object containing the log to stream.
      - `keep_streaming`: A callback function taking no arguments that returns `True` if streaming
        should continue or `False` if streaming should stop and the function should return.
    """
    while keep_streaming():
        content = infile.readline()

        if content != "":
            outfile.write(content)
        else:
            time.sleep(0.5)
