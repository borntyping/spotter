"""
Watch files and then run commands

Written by Sam Clements (sam@borntyping.co.uk),
and released under the MIT license.

http://github.com/borntyping/spotter
"""

from __future__ import absolute_import, print_function, unicode_literals

__version__ = '1.7'
__all__ = ['Spotter', 'Watch', 'WatchList', 'WatchFile']

from argparse import ArgumentParser

from spotter.spotter import Spotter
from spotter.watches import Watch, WatchList, WatchFile

parser = ArgumentParser(description="Watch files for changes")
parser.add_argument('-v', '--version', action='version', version="0.2")
parser.add_argument('-q', '--quiet', action='store_true',
    help="don't display the output of successful commands")
parser.add_argument('-c', '--continue',
    dest='continue_on_fail', action='store_true',
    help="continue running commands when one fails")
parser.add_argument('filenames',
    nargs='*', default=[".spotter"], metavar="filename",
    help="a list of files containing directives")

def main():
    Spotter(parser.parse_args(), start=True)

if __name__ == '__main__':
    main()
