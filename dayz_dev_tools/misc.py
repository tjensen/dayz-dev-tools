from collections import abc
import contextlib
import os


@contextlib.contextmanager
def chdir(path: str | None) -> abc.Generator[None, None, None]:
    if path is not None:
        original_cwd = os.getcwd()
        os.chdir(path)

    yield

    if path is not None:
        os.chdir(original_cwd)
