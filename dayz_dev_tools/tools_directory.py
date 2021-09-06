import importlib
import logging
import typing


class _Key:
    def Close(self) -> None:
        ...


class _WinReg:
    HKEY_CURRENT_USER: _Key

    def OpenKey(self, key: typing.Any, sub_key: str) -> _Key:
        ...

    def QueryValueEx(self, key: _Key, value_name: str) -> typing.Tuple[str, int]:
        ...


def tools_directory() -> typing.Optional[str]:
    try:
        winreg = typing.cast(_WinReg, importlib.import_module("winreg"))
    except ModuleNotFoundError:
        logging.debug("Unable to load 'winreg' module")
        return None

    key = None

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\bohemia interactive\Dayz Tools")

        value = winreg.QueryValueEx(key, "path")

        return value[0]
    except Exception:
        logging.debug("Unable to read DayZ Tools directory from registry", exc_info=True)
    finally:
        if key is not None:
            key.Close()

    return None
