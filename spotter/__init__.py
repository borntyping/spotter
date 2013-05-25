#!/usr/bin/env python3
"""
Watch files and then run commands

Written by Sam Clements (sam@borntyping.co.uk),
and released under the MIT license.

http://github.com/borntyping/spotter
"""

from __future__ import print_function, unicode_literals

__version__ = '1.1'

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

    def __repr__(self):
        return "<Watch{}: {} -> {}>".format(
            " (final)" if self.final else "", self.pattern, self.command)

class Spotter(pyinotify.ProcessEvent):
    INOTIFY_EVENT_MASK = pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE
    
    COMMANDS = ('define', 'start', 'watch', 'watch-final', 'stop')

    def __init__(self, filenames=None, quiet=False, continue_on_fail=False):
        self.definitions = dict()
        self.entry_commands = list()
        self.exit_commands = list()
        self.watches = list()
        
        self.quiet = quiet
        self.continue_on_fail = continue_on_fail
        
        # Read in the configuration, if initialised with a filename
        if filenames is not None:
            self.read_files(filenames)

    # --------------------------------------------------
    # Initialisation
    # --------------------------------------------------

    def read_files(self, filenames):
        """Read in multiple config files"""
        for filename in filenames:
            self.read_file(filename)

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

        Returns True if the command exited with a code of 0, else False

        If ``self.quiet`` is set, the output is redirected and only printed
        if the command failed.

        The command is formatted using the stored definitions and any keyword
        arguments passed to the function."""
        command = command.format(**merge(self.definitions, kwargs))

        # The output is redirected when running with --quiet
        stdout = subprocess.PIPE if self.quiet else None
        stderr = subprocess.STDOUT if self.quiet else None
        
        proccess = subprocess.Popen(
            command, shell=True, stdout=stdout, stderr=stderr)

        return_code = proccess.wait()

        # When running with --quiet, print the output of failed commands
        if self.quiet and return_code != 0:
            print(proccess.stdout.read().decode('utf-8'), end="")

        return return_code == 0

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
        """Run the commands that have a pattern matching the events path

        Stops running commands once one fails or is marked as final"""
        for watch in self.watches:
            if watch.pattern_matches(os.path.relpath(event.pathname)):
                success = self.run(watch.command, filename=event.pathname)
                if watch.final or (not self.continue_on_fail and not success):
                    break

    def __enter__(self):
        for command in self.entry_commands:
            self.run(command)

    def __exit__(self, type, value, traceback):
        for command in self.exit_commands:
            self.run(command)

# --------------------------------------------------
# Command line interface
# --------------------------------------------------

parser = argparse.ArgumentParser(description="Watch files for changes")
parser.add_argument('-v', '--version', action='version', version="0.2")
parser.add_argument('-q', '--quiet', action='store_true',
    help="don't display the output of successful commands")
parser.add_argument('-c', '--continue',
    dest='continue_on_fail', action='store_true',
    help="continue running commands when one fails")
parser.add_argument('filenames',
    nargs='*', default=[".spotter"], metavar="filename",
    help="a list of files containing directives")

def filename_hint(missing_file, prefix='.spotter'):
    """Print a hint listing other files starting with the given prefix"""
    print("Could not read file '{}'".format(missing_file))
    filenames = [f for f in os.listdir('.') if f.startswith(prefix)]
    if len(filenames) > 1:
        print("Maybe you meant:")
        for filename in filenames:
            print("  " + filename)

def main():
    args = parser.parse_args()

    spotter = Spotter(None, args.quiet, args.continue_on_fail)

    try:
        spotter.read_files(args.filenames)
    except IOError as error:
        filename_hint(error.filename)
        exit(1)

    spotter.loop()

if __name__ == '__main__':
    main()
