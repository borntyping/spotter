"""The Spotter class"""

from __future__ import absolute_import, print_function, unicode_literals

import collections
import os
import time
import subprocess

import pyinotify

class Watch(object):
    def __init__(self, path, command, exclude=[], minimum_interval=1.00):
        self.path = path
        self.command = command
        self.exclude = [os.path.join(self.path, path) for path in exclude]

        self.minimum_interval = minimum_interval
        self.last_executed = time.time() - self.minimum_interval

    def run_if_interval_passed(self, event):
        """Run if the minimum interval has passed since the last run"""
        if time.time() - self.last_executed > self.minimum_interval:
            self.last_executed = time.time()
            return self.run_command(event)
        else:
            return None

    def run_command(self, event):
        """Run the Watch's command and wait for it to finish"""
        command = self.command.format(filename=event.pathname)
        proccess = subprocess.Popen(command, shell=True)
        return (proccess.wait() == 0)

    def exclude_filter(self, path):
        """Used by pyinotify to filter paths that the watch will not match"""
        return path in self.exclude

    def __repr__(self):
        return "<Watch: '{}' {}>".format(self.path, self.exclude)

class SpotterLoader(object):
    Data = collections.namedtuple('Data', ['watches', 'start', 'stop'])

    def __init__(self, spotter, filename):
        self.spotter = spotter
        self.filename = filename

        # The watch ids managed by this loader
        self.watch_ids = set()

    def read(self):
        """Return the data read from the configuration file"""
        return self.Data([
            Watch("README.*", "echo README updated"),
            Watch("spotter/*.py", "echo {filename}", exclude=["__pycache__"])
        ], [], [])

    def load(self, data=None):
        """Load the read data into the spotter instance"""
        if data is None:
            data = self.read()
        
        for watch in data.watches:
            descriptors = self.spotter.add_watch(watch)
            self.watch_ids.update(descriptors.values())

    def unload(self):
        """Unload all watches managed by this loader"""
        for wd in self.watch_ids:
            self.spotter.rm_watch(wd)
        self.watch_ids = set()

    def reload(self, event):
        """Unload and load the data, but only if the file parses"""
        try:
            data = self.read()
        except:
            print("Could not read spotter configuration file", self.filename)
        else:
            self.unload()
            self.load(data)
        
class Spotter(object):
    EVENT_MASK = pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE

    def __init__(self, filename):
        self.loader = SpotterLoader(self, filename)
        self.watch_manager = pyinotify.WatchManager()
        self.watch_manager.add_watch(
            filename, self.EVENT_MASK, proc_fun=self.loader.reload)

        self.loader.load()

    def add_watch(self, watch):
        """Adds a watch object to the WatchManager"""
        return self.watch_manager.add_watch(
            watch.path, self.EVENT_MASK,
            auto_add=True, rec=True, do_glob=True,
            proc_fun=watch.run_if_interval_passed,
            exclude_filter=watch.exclude_filter)

    def rm_watch(self, wd):
        """Removes a watch from the WatchManager"""
        self.watch_manager.rm_watch(wd)

    def describe_watches(self):
        print("Watching", ', '.join([v.path for v in self.watch_manager.watches.values()]))

    def go(self):
        # Start notifying for watches
        notifier = pyinotify.Notifier(self.watch_manager)
        notifier.coalesce_events()
        notifier.loop()
