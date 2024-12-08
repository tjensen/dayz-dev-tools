from collections import abc
import contextlib
import os
import typing


@contextlib.contextmanager
def chdir(path: typing.Optional[str]) -> abc.Generator[None, None, None]:
    if path is not None:
        original_cwd = os.getcwd()
        os.chdir(path)

    yield

    if path is not None:
        os.chdir(original_cwd)
