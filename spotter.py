#!/usr/bin/env python3
"""
Watch files and then run commands

TODO:
- Stop on external program error
- Reload on .spotter changes
- A ~/.spotter-presets/ folder?
"""

import argparse
import collections
import fnmatch
import re
import subprocess
import os

import pyinotify

def merge(*dictionaries):
    """Merge any number of dictionaries into a single dictionary"""
    dictionary = dict()
    for d in dictionaries:
        dictionary.update(d)
    return dictionary

class Watch(object):
    def __init__(self, pattern, command, final=False):
        self.pattern = pattern
        self.command = command
        self.final = final

    def pattern_matches(self, path):
        """Return true if the given path matches the watch pattern"""
        return fnmatch.fnmatch(path, self.pattern) or path == self.pattern

class Spotter(pyinotify.ProcessEvent):
    INOTIFY_EVENT_MASK = pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE
    
    COMMANDS = ('define', 'start', 'watch', 'watch-final', 'stop')

    def __init__(self, filename=None, quiet=False):
        self.definitions = dict()
        self.entry_commands = list()
        self.exit_commands = list()
        self.watches = list()
        self.quiet = quiet
        
        # Read in the configuration, if initialised with a filename
        if not filename is None:
            self.read_file(filename)

    # --------------------------------------------------
    # Initialisation
    # --------------------------------------------------

    def read_file(self, filename):
        """Yield each command from a spotter config file"""
        with open(filename, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    self.read_line(line)

    def read_line(self, line):
        """Read in a single line and return a (directive, arguments) tuple"""
        directive, arguments = line.split(':')
        arguments = [a.strip() for a in arguments.split('->')]
        self.read_directive(directive.strip(), *arguments)
        
    def read_directive(self, directive, *arguments):
        """Read a parsed directive and add it to the current instance"""
        try:
            {
                'define':      self.add_definition,
                'start':       self.entry_commands.append,
                'stop':        self.exit_commands.append,
                'watch':       self.add_watch,
                'watch-final': self.add_final_watch,
            }[directive](*arguments)
        except KeyError:
            print("Unknown directive '{}'".format(directive))
            raise

    def add_definition(self, key, value):
        self.definitions[key] = value

    def add_watch(self, pattern, command):
        self.watches.append(Watch(pattern, command))

    def add_final_watch(self, pattern, command):
        self.watches.append(Watch(pattern, command, final=True))

    # --------------------------------------------------
    # Running
    # --------------------------------------------------

    def run(self, command, **kwargs):
        """Run a single command

        The command is formatted using the stored definitions and any keyword
        arguments passed to the function."""
        command = command.format(**merge(self.definitions, kwargs))
        subprocess.call(command, shell=True, stdout=open(os.devnull, 'wb') if
                                                    self.quiet else None)

    def loop(self):
        """Run the inotify loop inside the context manager"""
        with self:
            self.inotify_loop()
    
    def inotify_loop(self):
        watch_manager = pyinotify.WatchManager()
        notifier = pyinotify.Notifier(watch_manager, self)
        watch_manager.add_watch('.', Spotter.INOTIFY_EVENT_MASK, rec=True)
        notifier.loop()

    def process_default(self, event):
        """Run the command associated with the event"""
        for watch in self.watches:
            if watch.pattern_matches(os.path.relpath(event.pathname)):
                self.run(watch.command, filename=event.pathname)
                if watch.final == True:
                    break

    def __enter__(self):
        for command in self.entry_commands:
            self.run(command)

    def __exit__(self, type, value, traceback):
        for command in self.exit_commands:
            self.run(command)

parser = argparse.ArgumentParser(description="Watch files for changes")
parser.add_argument('-v', '--version', action='version', version="0.2")
parser.add_argument('-q', '--quiet', dest='quiet', action='store_true', default=False,
                    help="don't display the output of commands")
parser.add_argument('filename', nargs='?', default=".spotter",
    help="the spotter file to use")

def main():
    args = parser.parse_args()
    Spotter(filename=args.filename, quiet=args.quiet).loop()

if __name__ == '__main__':
    main()
