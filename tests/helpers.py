import os
import sys
import types
import typing
from unittest import mock


class WrappedMain(typing.Protocol):
    def __call__(self, argv: list[str], environ: dict[str, str] = {}) -> None:
        ...


def call_main(
    module: types.ModuleType
) -> WrappedMain:
    def wrapper(argv: list[str], environ: dict[str, str] = {}) -> None:
        with mock.patch.object(sys, "argv", argv), mock.patch.object(os, "environ", environ):
            getattr(module, "main")()

    return wrapper
