import enum
import os
import subprocess
import tempfile


class _Mode(enum.Enum):
    BIN = "-bin"
    TXT = "-txt"


def _run(executable: str, mode: _Mode, in_bytes: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as tempdir:
        in_path = os.path.join(tempdir, "input.tmp")
        out_path = os.path.join(tempdir, "output.tmp")

        with open(in_path, "w+b") as infile:
            infile.write(in_bytes)

        subprocess.run(
            [
                executable,
                mode.value,
                "-dst", out_path,
                in_path
            ],
            check=True)

        with open(out_path, "rb") as outfile:
            return outfile.read()


def bin_to_cpp(bin_content: bytes, executable: str) -> bytes:
    return _run(executable, _Mode.TXT, bin_content)


def cpp_to_bin(cpp_content: bytes, executable: str) -> bytes:
    return _run(executable, _Mode.BIN, cpp_content)
