"""
Watch files and then run commands

Written by Sam Clements (sam@borntyping.co.uk),
and released under the MIT license.

http://github.com/borntyping/spotter
"""

from __future__ import absolute_import, print_function, unicode_literals

__version__ = '1.3'
__all__ = ['Spotter']

from argparse import ArgumentParser

from spotter.spotter import Spotter

parser = ArgumentParser(description="Watch files for changes")
parser.add_argument('-v', '--version', action='version', version="0.2")
parser.add_argument('-q', '--quiet', action='store_true',
    help="don't display the output of successful commands")
parser.add_argument('filename', default=[".spotter.json"],
    help="the configuration file to read")

def main():
    args = parser.parse_args()
    Spotter(args.filename).go()

if __name__ == '__main__':
    main()
