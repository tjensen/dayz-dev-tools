from typing import Union

BufferType = Union[bytes, bytearray]


def expand(input: BufferType, capacity: int) -> bytes:
    ...


def compute_checksum(data: BufferType) -> int:
    ...
