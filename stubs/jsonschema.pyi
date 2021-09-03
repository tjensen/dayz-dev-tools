import typing


class ValidationError(Exception):
    absolute_path: str
    message: str


def validate(instance: typing.Any, schema: typing.Any) -> None:
    ...
