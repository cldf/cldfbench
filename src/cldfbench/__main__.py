"""
Main command line interface of the cldfbench package.

Like programs such as git, this cli splits its functionality into sub-commands
(see e.g. https://docs.python.org/2/library/argparse.html#sub-commands).
The rationale behind this is that while a lot of different tasks may be
triggered using this cli, most of them require common configuration.
"""
import csv
import sys
import contextlib

from clldutils.clilib import (
    register_subcommands, get_parser_and_subparsers, ParserError, add_csv_field_size_limit,
    add_random_seed,
)
from clldutils.loglib import Logging
from cldfcatalog import Config
import termcolor
import argparse

import cldfbench
from cldfbench.catalogs import BUILTIN_CATALOGS
from cldfbench.cli_util import IGNORE_MISSING
import cldfbench.commands


def main(args=None, catch_all=False, parsed_args=None, log=None):
    parser, subparsers = get_parser_and_subparsers(cldfbench.__name__)

    # We add a "hidden" option to turn-off config file reading in tests:
    parser.add_argument('--no-config', default=False, action='store_true', help=argparse.SUPPRESS)
    add_csv_field_size_limit(parser, default=csv.field_size_limit())
    add_random_seed(parser)

    # Discover available commands:
    # Commands are identified by (<entry point name>).<module name>
    register_subcommands(subparsers, cldfbench.commands, entry_point='cldfbench.commands')

    args = parsed_args or parser.parse_args(args=args)
    if not hasattr(args, "main"):
        parser.print_help()
        return 1

    with contextlib.ExitStack() as stack:
        if not log:  # pragma: no cover
            stack.enter_context(Logging(args.log, level=args.log_level))
        else:
            args.log = log
        # args.no_catalogs is set by the `config` command, because this command specifies
        # catalog options **optionally**, and prompts for user input only in its `run` function.
        if not getattr(args, "no_catalogs", False):
            cfg = Config.from_file()
            for cls in BUILTIN_CATALOGS:
                # Now we loop over known catalogs, see whether they are used by the command,
                # and if so, "enter" the catalog.
                name, from_cfg = cls.cli_name(), False
                if hasattr(args, name):
                    # If no path was passed on the command line, we look up the config:
                    path = getattr(args, name)
                    if path != IGNORE_MISSING:
                        if (not path) and (not args.no_config):
                            try:
                                path = cfg.get_clone(name)
                                from_cfg = True
                            except KeyError as e:  # pragma: no cover
                                print(termcolor.colored(str(e) + '\n', 'red'))
                                return main([args._command, '-h'])
                        try:
                            setattr(
                                args,
                                name,
                                stack.enter_context(
                                    cls(path, getattr(args, name + '_version', None))),
                            )
                            assert getattr(args, name).api
                        except ValueError as e:
                            print(termcolor.colored(
                                '\nError initializing catalog {0}'.format(name), 'red'))
                            if from_cfg:
                                print(
                                    termcolor.colored('from config {0}'.format(cfg.fname()), 'red'))
                            print(termcolor.colored(str(e) + '\n', 'red'))
                            return main([args._command, '-h'])
                    else:
                        setattr(args, name, None)

        try:
            return args.main(args) or 0
        except KeyboardInterrupt:  # pragma: no cover
            return 0
        except ParserError as e:
            print(termcolor.colored('ERROR: {}\n'.format(e), 'red', attrs={'bold'}))
            return main([args._command, '-h'])
        except Exception as e:
            if catch_all:  # pragma: no cover
                print(termcolor.colored('ERROR: {}\n'.format(e), 'red', attrs={'bold'}))
                return 1
            raise


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main() or 0)
