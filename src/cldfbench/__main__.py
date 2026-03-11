"""
Main command line interface of the cldfbench package.

Like programs such as git, this cli splits its functionality into sub-commands
(see e.g. https://docs.python.org/2/library/argparse.html#sub-commands).
The rationale behind this is that while a lot of different tasks may be
triggered using this cli, most of them require common configuration.
"""
import csv
import sys
import argparse
import contextlib
from typing import Optional

from clldutils.clilib import (
    register_subcommands, get_parser_and_subparsers, ParserError, add_csv_field_size_limit,
    add_random_seed,
)
from clldutils.loglib import Logging
from cldfcatalog import Config

import cldfbench
from cldfbench.catalogs import BUILTIN_CATALOGS
from cldfbench.cli_util import IGNORE_MISSING
from cldfbench.util import colored
import cldfbench.commands


def print_red(text, **kw):  # pylint: disable=C0116
    print(colored('red', text, **kw))


def _add_catalog(
        cls: type,
        cfg: Config,
        args: argparse.Namespace,
        stack: contextlib.ExitStack,
) -> tuple[Optional[Exception], bool]:
    """Catalogs are context managers, so they have to be added to the exit stack."""
    name = cls.cli_name()
    if not hasattr(args, name):
        return None, False
    path = getattr(args, name)
    from_cfg = False
    if path != IGNORE_MISSING:
        if (not path) and (not args.no_config):
            try:
                path = cfg.get_clone(name)
                from_cfg = True
            except KeyError as e:  # pragma: no cover
                return e, False
        try:
            version = getattr(args, name + '_version', None)
            setattr(args, name, stack.enter_context(cls(path, version)))
            assert getattr(args, name).api
        except ValueError as e:
            return e, from_cfg
    else:
        setattr(args, name, None)  # pragma: no cover
    return None, False


def main(args=None, catch_all=False, parsed_args=None, log=None):  # pylint: disable=C0116,R0911
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

    def cmd_help(err):
        print_red(err + '\n', attrs={'bold'})
        return main([args._command, '-h'])  # pylint: disable=W0212

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
                e, from_cfg = _add_catalog(cls, cfg, args, stack)
                if isinstance(e, KeyError):  # pragma: no cover
                    return cmd_help(str(e))
                if isinstance(e, ValueError):
                    print_red(f'\nError initializing catalog {cls.cli_name()}')
                    if from_cfg:
                        print_red(f'from config {cfg.fname()}')
                    return cmd_help(str(e))
                assert e is None

        try:
            return args.main(args) or 0
        except KeyboardInterrupt:  # pragma: no cover
            return 0
        except ParserError as e:
            return cmd_help(f'ERROR: {e}')
        except Exception as e:
            if catch_all:  # pragma: no cover
                print_red(f'ERROR: {e}\n', attrs={'bold'})
                return 1
            raise


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main() or 0)
