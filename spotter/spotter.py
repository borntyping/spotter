"""The Spotter class"""

from __future__ import absolute_import, print_function, unicode_literals

import subprocess
import os
import sys

import errno

import pyinotify

from spotter.watches import WatchFile


class Spotter(pyinotify.ProcessEvent):
    INOTIFY_EVENT_MASK = pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE

    def __init__(self, options, start=False):
        self.options = options
        self.watchlists = list()

        if self.options.filenames is not None:
            self.read_files(self.options.filenames)

        if start:
            self.loop()

    def read_files(self, filenames):
        for filename in filenames:
            try:
                self.watchlists.append(WatchFile(filename))
            except IOError as e:
                if e.errno is not errno.ENOENT:
                    raise e
                sys.exit("No such file or directory: %s" % filename)

    def loop(self):
        """Run the inotify loop, running the entry and exit commands with a
        context manager."""
        with self:
            self.inotify_loop()

    def inotify_loop(self):
        watch_manager = pyinotify.WatchManager()
        notifier = pyinotify.Notifier(watch_manager, self)
        watch_manager.add_watch('.', Spotter.INOTIFY_EVENT_MASK, rec=True, auto_add=True)
        notifier.loop()

    def process_default(self, event):
        """Run the commands that have a pattern matching the events path

        Stops running commands once one fails or is marked as final"""
        path = event.pathname.decode(sys.getfilesystemencoding())

        for watchlist in self.watchlists:
            for watch in watchlist:
                if watch.pattern_matches(os.path.relpath(path)):
                    success = self.run(
                        watch.command,
                        filename=path, **watchlist.definitions)
                    # Always stop if the watch was final
                    if watch.final:
                        break
                    # Stop if we failed without --continue-on-fail
                    if not (success or self.options.continue_on_fail):
                        break

    def run(self, command, **kwargs):
        """Run a single command

        Returns True if the command exited with a code of 0, else False

        If ``self.quiet`` is set, the output is redirected and only printed
        if the command failed. The output is not redirected and then printed
        when it can be avoided, so that output is instant.

        The command is formatted using the stored definitions and any keyword
        arguments passed to the function."""
        stdout = subprocess.PIPE if self.options.quiet else None
        stderr = subprocess.STDOUT if self.options.quiet else None

        proccess = subprocess.Popen(
            command.format(**kwargs),
            shell=True, stdout=stdout, stderr=stderr)

        return_code = proccess.wait()

        # When running with --quiet, print the output of failed commands
        if self.options.quiet and return_code != 0:
            print(proccess.stdout.read().decode('utf-8'), end="")

        return (return_code == 0)

    def __enter__(self):
        for watchlist in self.watchlists:
            for command in watchlist.entry_commands:
                self.run(command)

    def __exit__(self, type, value, traceback):
        for watchlist in self.watchlists:
            for command in watchlist.exit_commands:
                self.run(command)
