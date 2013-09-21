"""Watch and watch-file data structures"""

from __future__ import absolute_import, print_function, unicode_literals

import fnmatch


class Watch(object):
    """A filename pattern and a shell command"""

    __slots__ = ('pattern', 'command', 'final')

    def __init__(self, pattern, command, final=False):
        self.pattern = pattern
        self.command = command
        self.final = final

    def pattern_matches(self, path):
        """Return true if the given path matches the watch pattern"""
        return fnmatch.fnmatch(path, self.pattern) or path == self.pattern

    def __repr__(self):
        return "<Watch{}: {} -> {}>".format(
            " (final)" if self.final else "", self.pattern, self.command)

    def __str__(self):
        return "watch{}: {} -> {}".format(
            "-final" if self.final else "", self.pattern, self.command)


class WatchList(list):
    """A list of watches, and the associated definitions"""

    def __init__(self, iterable=None, definitions=None,
                 entry_commands=None, exit_commands=None):
        super(WatchList, self).__init__(iterable or list())
        self.definitions = definitions or dict()
        self.entry_commands = entry_commands or list()
        self.exit_commands = exit_commands or list()

    def __repr__(self):
        return "<WatchList: {}, definitions={}, entry={}, exit={}>".format(
            super(WatchList, self).__repr__(), self.definitions,
            self.entry_commands, self.exit_commands)

    def __str__(self):
        strings = []
        for key, value in self.definitions.items():
            strings.append("define: {} -> {}".format(key, value))
        for command in self.entry_commands:
            strings.append("start: {}".format(command))
        for watch in self:
            strings.append(str(watch))
        for command in self.exit_commands:
            strings.append("start: {}".format(command))
        return "\n".join(strings)


class WatchFile(WatchList):
    """A list of watches read directly from a watch-file"""

    def __init__(self, filename):
        super(WatchFile, self).__init__()
        self.read_file(filename)

    def read_file(self, filename):
        """Read each line of a watch-file"""
        with open(filename, 'r') as file:
            lines = [line.strip() for line in file]

        for line in lines:
            if line and not line.startswith('#'):
                self.read_line(line)

    def read_line(self, line):
        """Read in a single line and return a (directive, arguments) tuple"""
        directive, arguments = line.split(':', 1)
        arguments = [a.strip() for a in arguments.split('->')]
        self.read_directive(directive.strip(), *arguments)

    def read_directive(self, directive, *arguments):
        """Read a parsed directive and add it to the current instance"""
        try:
            {
                'define':      self._add_definition,
                'start':       self._add_entry_command,
                'stop':        self._add_exit_command,
                'watch':       self._add_watch,
                'watch-final': self._add_final_watch,
            }[directive](*arguments)
        except KeyError:
            print("Unknown directive '{}'".format(directive))
            raise

    def _add_definition(self, key, value):
        self.definitions[key] = value

    def _add_entry_command(self, command):
        self.entry_commands.append(command)

    def _add_exit_command(self, command):
        self.exit_commands.append(command)

    def _add_watch(self, pattern, command, final=False):
        self.append(Watch(pattern, command, final))

    def _add_final_watch(self, pattern, command):
        self._add_watch(pattern, command, final=True)
