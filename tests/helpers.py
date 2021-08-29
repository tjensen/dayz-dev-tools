import sys
import types
import typing
from unittest import mock


def call_main(module: types.ModuleType) -> typing.Callable[[typing.List[str]], None]:
    def wrapper(argv: typing.List[str]) -> None:
        with mock.patch.object(sys, "argv", argv):
            getattr(module, "main")()

    return wrapper
