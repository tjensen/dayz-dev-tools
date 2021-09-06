import os
import subprocess
import tempfile


def bin_to_cpp(bin_content: bytes, executable: str) -> bytes:
    with tempfile.TemporaryDirectory() as tempdir:
        bin_path = os.path.join(tempdir, "config.bin")
        cpp_path = os.path.join(tempdir, "config.cpp")

        with open(bin_path, "w+b") as binfile:
            binfile.write(bin_content)

        subprocess.run(
            [
                executable,
                "-txt",
                "-dst", cpp_path,
                bin_path
            ],
            check=True)

        with open(cpp_path, "rb") as cppfile:
            return cppfile.read()
