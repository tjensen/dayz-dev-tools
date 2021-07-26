# DayZ Dev Tools

This project contains tools and libraries that can be useful for DayZ mod
developers and server owners.

## Installation

The easiest way to install this package is using `pip`:

```
pip install dayz-dev-tools
```

Note that Python 3.8 or higher is required.

## Command-Line Tools

All included command-line tools offer built-in help, accessible by passing
either the `-h` or `--help` option, e.g.:

```
unpbo -h
```

Note: More tools will be added in the future.

### unpbo

The `unpbo` command enables the viewing or extracting of the contents of a PBO
file. Pass `-l` or `--list` to list the contents of the PBO:

```
unpbo --list C:\path\to\filename.pbo
```

To extract all of the files contained in the PBO into the current directory:

```
unpbo C:\path\to\filename.pbo
```

To extract one or more individual files from the PBO, list their full names (as
displayed in the `-l`/`--list` output), space separated, on the command line
after the PBO filename:

```
unpbo C:\path\to\filename.pbo Prefix\scripts\3_Game\foo.c Prefix\config.cpp
```
