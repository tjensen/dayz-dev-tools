from typing import TypeAlias

BufferType: TypeAlias = bytes | bytearray


def expand(input: BufferType, capacity: int) -> bytes:
    ...


def compute_checksum(data: BufferType) -> int:
    ...
