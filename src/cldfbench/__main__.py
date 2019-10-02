"""
Main command line interface of the cldfbench package.

Like programs such as git, this cli splits its functionality into sub-commands
(see e.g. https://docs.python.org/2/library/argparse.html#sub-commands).
The rationale behind this is that while a lot of different tasks may be
triggered using this cli, most of them require common configuration.

The basic invocation looks like

    cldfbanch [OPTIONS] <command> [args]

"""
import sys

from clldutils.clilib import ArgumentParserWithLogging

import cldfbench


def main(args=None):
    parser = ArgumentParserWithLogging(cldfbench.__name__)
    sys.exit(parser.main(args))
