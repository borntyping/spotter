=======
spotter
=======

.. image:: https://pypip.in/v/spotter/badge.png
    :target: https://crate.io/packages/spotter/
    :alt: Latest PyPI version

Spotter is a simple command line tool for watching files and running shell commands when they change.
Directives are read from a text file, and spotter will look for a file named ``.spotter`` in the current directory if no filenames are given.

Usage
=====

::

    spotter [-h] [-v] [-q] [-c] [filename [filename ...]]

Positional arguments:
    * ``filename``: A list of files containing directives to load, defaulting to ``[".spotter"]``.

Optional arguments:
    * ``-h``, ``--help``: Explain the command line options.
    * ``-v``, ``--version``: Show the current version number.
    * ``-q``, ``--quiet``: The output of commands is not printed unless they fail.
    * ``-c``, ``--continue``: Failed commands will not stop spotter from continuing.

Spotter can also be run as a python module:

::

    python -m spotter ...

Directives
==========

All directives are in the following form::

    <directive>: <argument> [-> <second argument>]

Not all directives take a second argument, but all of them take a first argument.

Watch
-----

::

    watch: <pattern> -> <command>

The Watch directive takes two arguments: ``<pattern>`` is a unix-style filename pattern, and ``<command>`` is a shell command to run when a file matching the pattern is created or changed.
More information on the pattern matching used can be found in the `fnmatch library documentation <http://docs.python.org/3/library/fnmatch.html>`_.

::

    watch: *.txt -> echo "Text file changed"

Multiple watch directives can be given, and spotter will continue to run matching watch directives until one fails (i.e. returns an exit code above 0) or until it runs a matching ``watch-final`` directive.

::

    watch: * -> return 1
    watch: * -> echo "This command will not run"

The ``--continue`` command line argument can be used to disable this behaviour, forcing spotter to continue processing watches even if one fails.

Watch-Final
-----------

::

    watch-final: <pattern> -> <command>

Watch-final has exactly the same syntax and behaviour as the Watch directive.
Unlike the Watch directive, if the pattern matches and the command is run, no further watches will be processed.

::

    watch-final: *.txt -> echo "No commands will run after this"

Start / Stop
------------

::

    start: <command>
    stop: <command>

The start and stop directives can be used to run commands when spotter starts running and when spotter stops running.

::

    start: echo "Started watching files"
    stop: echo "Stopped watching files"

Define
------

::

    define: <name> -> <value>

The Define directive allows values to be stored and then included in other directives when they are run.
``filename`` is always available in watch commands, and contains the path of the file that matched the pattern.
Definitions are included in the commands using `python format specifications <http://docs.python.org/3/library/string.html#formatspec>`_, and are inserted when the command is run, not when the command is loaded.

::

    define: python_command -> python2.6

    watch: *.py -> {python_command} "{filename}"
