import datetime

from dayz_dev_tools import pbo_reader


def list_pbo(reader: pbo_reader.PBOReader, *, verbose: bool) -> None:
    """Print the contents of a PBO archive to stdout in tabular format.

    :Parameters:
      - `reader`: A :class:`~dayz_dev_tools.pbo_reader.PBOReader` instance representing the PBO
        archive to list.
      - `verbose`: When `True`, additional detail will be printed.
    """
    if verbose:
        print("Headers:")
        print("--------")
        for key, value in reader.headers():
            print(f"{key.decode(errors='replace')} = {value.decode(errors='replace')}")
        print()
        print(" Original  Type    Size        Date    Time   Name")
        print("---------  ----  ---------  ---------- -----  ----")
    else:
        print(" Original     Date    Time   Name")
        print("---------  ---------- -----  ----")

    total_unpacked = 0
    total_size = 0

    for file in reader.files():
        timestamp = datetime.datetime.fromtimestamp(file.time_stamp).strftime("%Y-%m-%d %H:%M")
        total_unpacked += file.unpacked_size()
        total_size += file.data_size

        if verbose:
            print(
                f"{file.unpacked_size():9}  {file.type()}  {file.data_size:9}  {timestamp}"
                f"  {file.normalized_filename()}")
        else:
            print(f"{file.unpacked_size():9}  {timestamp}  {file.normalized_filename()}")

    if verbose:
        print("---------        ---------                    ---------")
        print(
            f"{total_unpacked:9}        {total_size:9}                    "
            f"{len(reader.files())} Files")
    else:
        print("---------                    ---------")
        print(f"{total_unpacked:9}                    {len(reader.files())} Files")
