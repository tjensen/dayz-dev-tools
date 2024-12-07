Commands
========

All included command-line tools offer built-in help, accessible by passing
either the ``-h`` or ``--help`` option, e.g.:

.. code:: batch

   unpbo -h

.. note:: More tools will be added in the future.

guid
----

The ``guid`` command can be used to convert 64-bit Steam IDs to DayZ GUIDs.
Pass the SteamID64 to convert as a parameter to the command:

.. code:: batch

   guid 76561197970002375

pbo
---

The ``pbo`` command can be used to create PBO files. Pass the name of the PBO
file to create, followed by the names of any files to add to the PBO. For
example:

.. code:: batch

   pbo mymod.pbo config.cpp scripts\3_game\something.c

Note that this command is relatively low level compared to many other PBO
creation tools, like PboProject and AddonBuilder. Adding headers and signing
the resulting PBO requires additional options. See the ``-h`` or ``--help``
output for further details.

unpbo
-----

The ``unpbo`` command enables the viewing or extracting of the contents of a
PBO file. Pass ``-l`` or ``--list`` to list the contents of the PBO:

.. code:: batch

   unpbo --list C:\path\to\filename.pbo

To extract all of the files contained in the PBO into the current directory:

.. code:: batch

   unpbo C:\path\to\filename.pbo

To extract one or more individual files from the PBO, list their full names (as
displayed in the ``-l``/``--list`` output), space separated, on the command
line after the PBO filename:

.. code:: batch

   unpbo C:\path\to\filename.pbo Prefix\scripts\3_Game\foo.c Prefix\config.cpp

run-server
----------

The ``run-server`` command provides a convenient method for running DayZ Server
locally (i.e. for testing mods). It supports loading collections of mods and
configuring server parameters through the use of "bundles", which are specified
on the command line. Bundles can be defined either in the ``server.toml``
config file or as functions in a Python module.

Bundles defined in the config file generally look like:

.. code:: toml

   [bundle.mybundle]
   mods = '@CF;@MasPuertas;P:\MyModPack'
   mission_directory = 'mpmissions\dayzoffline.enoch'

To load a bundle, specify it on the command line as a positional argument. For
example:

.. code:: batch

   run-server mybundle

Bundles defined in Python require more typing but offer more flexibility than
config file bundles.

.. seealso::

   `Bundles as Configuration`_

   `Python Bundles`_

Configuration File
^^^^^^^^^^^^^^^^^^

The ``run-server`` command can be configured using a config file, named
``server.toml`` by default. Most settings are in the ``server`` table of the
file. For example:

.. code:: toml

   [server]
   executable = "server.exe"
   config = "config.cfg"
   directory = 'server\dir'
   profile_directory = "profile"
   mission_directory = 'mpmissions\dayzoffline.enoch'
   bundles = 'path\to\module.py'
   parameters = [ '-opt1', '-opt2=value' ]

   [workshop]
   directory = 'E:\DayZ\Workshop'

.. note:: All settings are optional and have reasonable defaults.

Server Executable
"""""""""""""""""

By default, ``run-server`` will try to run DayZ Server by running
``.\DayZServer_x64.exe`` on Windows or ``./DayZServer`` on Linux. To override
the executable path, set the ``executable`` key:

.. code:: toml

   [server]
   executable = "server.exe"

Server Configuration
""""""""""""""""""""

By default, ``run-server`` will tell DayZ Server to load its configuration from
``serverDZ.cfg``. To override the config file path, set the ``config`` key:

.. code:: toml

   [server]
   config = "config.cfg"

Server Directory
""""""""""""""""

By default, ``run-server`` will run DayZ Server from the current working
directory. To have ``run-server`` change to a different directory before
running DayZ Server, set the ``directory`` key:

.. code:: toml

   [server]
   directory = 'server\directory'

.. note:: The current working directory is changed after loading bundles
   specified on the command line.

Profile Directory
"""""""""""""""""

By default, ``run-server`` will let DayZ Server choose a profile directory
automatically (usually, ``%LOCALAPPDATA%\DayZ``). The profile directory is where
DayZ Server writes logs and other information. To override the profile
directory, set the ``profile_directory`` key:

.. code:: toml

   [server]
   profile_directory = "profile"

DayZ Mission Directory
""""""""""""""""""""""

By default, ``run-server`` will let DayZ Server choose the mission directory
based on the server configuration file (e.g. ``serverDZ.cfg``). To override the
mission directory, set the ``mission_directory`` key:

.. code:: toml

   [server]
   mission_directory = 'mpmissions\dayzoffline.enoch'

Bundles Python Module
"""""""""""""""""""""

By default, ``run-server`` will look for bundles in a Python file named
``bundles.py``. To override the Python bundles module filename, set the
``bundles`` key:

.. code:: toml

   [server]
   bundles = 'path\to\module.py'

Bundles can also be loaded from the ``run-server`` config file, as described
below.

Extra Parameters
""""""""""""""""

Use the ``parameters`` key to pass extra command line parameters to DayZ
Server. For example, to enable admin logs:

.. code:: toml

   [server]
   parameters = [ '-adminLog' ]

DayZ Workshop Directory
"""""""""""""""""""""""

By default, ``run-server`` will load mods prefixed with ``@`` from
the ``C:\Program Files (x86)\Steam\steamapps\common\DayZ\!Workshop`` directory
on Windows or ``$HOME/.steam/steamapps/common/DayZ/!Workshop`` on Linux. If
DayZ client is installed in a different location or you have installed mods
from the Steam workshop in a different location, override the default by
setting the ``directory`` key in the ``workshop`` table:

.. code:: toml

   [workshop]
   directory = 'E:\DayZ\Workshop'

.. note:: As there is currently no Linux version of DayZ *client*, Linux users
   who want to specify mods using the ``@`` prefix should override this setting
   to the location where they have installed mods using SteamCMD.

Bundles as Configuration
""""""""""""""""""""""""

In the config file, each bundle is defined as a
`table <https://toml.io/en/v1.0.0#table>`_. For example, to define a bundle
named ``example``:

.. code:: toml

   [bundle.example]
   executable = 'path\to\server.exe'
   config = 'path\to\config.cfg'
   directory = 'path\to\server\dir'
   profile_directory = 'path\to\profile'
   mission_directory = 'path\to\mission'
   workshop_directory = 'path\to\workshop'
   parameters = [ '-extraParam', '-another=arg' ]

These settings work the same as the ones of the same names described in
`Configuration File`_. In addition, bundles can define DayZ mods and server
mods to add to the command line:

.. code:: toml

   [bundle.example]
   mods = '@Mod1;@Mod2;C:\path\to\mod'
   server_mods = '@ServerMod;@ServerMod2;C:\path\to\servermod'

Mods and server mods can also be configured as lists of strings:

.. code:: toml

   [bundle.example]
   mods = [ '@Mod1', '@Mod2', 'C:\path\to\mod' ]
   server_mods = [ '@ServerMod', '@ServerMod2', 'C:\path\to\servermod' ]

Mod names and server mod names that start with ``@`` will be loaded from the
DayZ workshop directory (see `DayZ Workshop Directory`_).

Python Bundles
^^^^^^^^^^^^^^

More advanced bundles can be created using Python code in the
`Bundles Python Module`_. Each function defined in the module can be referenced
as a bundle. Bundle functions must take a single
:class:`dayz_dev_tools.launch_settings.LaunchSettings` argument. For example,
to define a bundle named ``example``:

.. code:: python

   def example(settings):
       settings.set_mission_directory(r"path\to\mission")
       settings.add_mod("@Mod1")
       settings.add_mod(r"C:\path\to\mod")
