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

### run-server

The `run-server` command provides a convenient way to run DayZ Server locally
when testing mods. It supports loading collections of mods and configuring
server parameters through the use of "bundles", which are specified on the
command line. Bundles can be defined either in the `server.toml` config file or
as functions in a Python module.

Bundles defined in the config file generally look like:

```toml
[bundle.mybundle]
mods = '@CF;@MasPuertas;P:\MyModPack'
mission_directory = 'mpmissions\dayzoffline.enoch'
```

To load a bundle, specify it on the command line as a positional argument. For
example:

```
run-server mybundle
```

Bundles defined in a Python module require more typing but offer more
flexibility than config file bundles.

#### Configuration

The `run-server` command can be configured using a config file, named
`server.toml` by default. Most settings are in the `server` table of the file.

##### Server Executable

By default, `run-server` will try to run DayZ Server by running
`.\DayZServer_x64.exe`. To override the executable path, set the `executable`
key:

```toml
[server]
executable = "server.exe"
```

##### Server Configuration

By default, `run-server` will tell DayZ Server to load its configuration from
`serverDZ.cfg`. To override the config file path, set the `config` key:

```toml
[server]
config = "config.cfg"
```

##### Server Profile Directory

By default, `run-server` will let DayZ Server choose a profile directory
automatically (usually, `%LOCALAPPDATA\DayZ`). The profile directory is where
DayZ Server writes logs and other information. To override the profile
directory, set the `profile_directory` key:

```toml
[server]
profile_directory = "profile"
```

##### DayZ Mission Directory

By default, `run-server` will let DayZ Server choose the mission directory
based on the server configuration file (e.g. `serverDZ.cfg`). To override the
mission directory, set the `mission_directory` key:

```toml
[server]
mission_directory = 'mpmissions\dayzoffline.enoch'
```

#### Bundles Python Module

By default, `run-server` will look for bundles in a Python file named
`bundles.py`. To override the Python bundles module filename, set the `bundles`
key:

```toml
[server]
bundles = 'path\to\module.py'
```

Bundles can also be loaded from the `run-server` config file, as described
below.

##### DayZ Workshop Directory

By default, `run-server` will load mods prefixed with `@` from
the `C:\Program Files (x86)\Steam\steamapps\common\DayZ\!Workshop` directory.
To override this directory, set the `directory` key in the `workshop` table:

```toml
[workshop]
directory = 'E:\DayZ\Workshop'
```

#### Bundles

In the config file, each bundle is defined as a
[table](https://toml.io/en/v1.0.0#table). For example, to define a bundle named
"example":

```toml
[bundle.example]
```

In a Python module, bundles are defined as functions taking a single argument
of type `dayz_dev_tools.launch_settings.LaunchSettings`. For example:

```python
def example(settings):
    ...
```

##### Server Executable

Bundles can override the DayZ server executable path. In the config file, this
is done by setting the `executable` key:

```toml
[bundle.example]
executable = 'path\to\server.exe'
```

In Python, this is done by calling the `set_executable` method:

```python
def example(settings):
    settings.set_executable(r"path\to\server.exe")
```

##### Server Configuration

Bundles can override the DayZ Server configuration file path. In the config
file, this is done by setting the `config` key:

```toml
[bundle.example]
config = 'path\to\config.cfg'
```

In Python, this is done by calling the `set_config` method:

```python
def example(settings):
    settings.set_config(r"path\to\config.cfg")
```

##### Server Profile Directory

Bundles can override the DayZ Server profile directory. In the config file,
this is done by setting the `profile_directory` key:

```toml
[bundle.example]
profile_directory = 'path\to\profile'
```

In Python, this is done by calling the `set_profile_directory` method:

```python
def example(settings):
    settings.set_profile_directory(r"path\to\profile")
```

##### DayZ Mission Directory

Bundles can override the DayZ mission directory. In the config file, this is
done by setting the `mission_directory` key:

```toml
[bundle.example]
mission_directory = 'path\to\mission'
```

In Python, this is done by calling the `set_mission_directory` method:

```python
def example(settings):
    settings.set_mission_directory(r"path\to\mission")
```

##### DayZ Workshop Directory

Bundles can override the DayZ Workshop directory. In the config file, this is
done by setting the `workshop_directory` key:

```toml
[bundle.example]
workshop_directory = 'path\to\workshop'
```

In Python, this is done by calling the `set_workshop_directory` method:

```python
def example(settings):
    settings.set_workshop_directory(r"path\to\workshop")
```

##### Mods

Bundles can add DayZ mods. In the config file, this is done by setting the
`mods` key. The value can be either a string or an array of strings. Mod names
that start with `@` are loaded from the DayZ workshop directory. Mod names
without `@` prefixes are treated as paths. For example:

```toml
[bundle.example1]
mods = '@Mod1;@Mod2;P:\LocalModDir'

[bundle.example2]
mods = [ '@Mod1', '@Mod2', 'P:\LocalModDir' ]
```

In Python, this is done by calling the `add_mod` method:

```python
def example(settings):
    settings.add_mod("@Mod1")
    settings.add_mod("@Mod2")
    settings.add_mod(r"P:\LocalModDir")
```

##### Server Mods

Bundles can add DayZ server-side mods. In the config file, this is done by
setting the `server_mods` key. The value can be either a string or an array of
strings. Mod names that start with `@` are loaded from the DayZ workshop
directory. Mod names without `@` prefixes are treated as paths. For example:

```toml
[bundle.example1]
server_mods = '@Mod1;@Mod2;P:\LocalModDir'

[bundle.example2]
server_mods = [ '@Mod1', '@Mod2', 'P:\LocalModDir' ]
```

In Python, this is done by calling the `add_server_mod` method:

```python
def example(settings):
    settings.add_server_mod("@Mod1")
    settings.add_server_mod("@Mod2")
    settings.add_server_mod(r"P:\LocalModDir")
```
