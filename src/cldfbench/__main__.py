"""
Main command line interface of the cldfbench package.

Like programs such as git, this cli splits its functionality into sub-commands
(see e.g. https://docs.python.org/2/library/argparse.html#sub-commands).
The rationale behind this is that while a lot of different tasks may be
triggered using this cli, most of them require common configuration.

The basic invocation looks like

    cldfbench [OPTIONS] <command> [args]

"""
import sys
import contextlib

from clldutils.clilib import ParserError, get_parser_and_subparsers, register_subcommands
from clldutils.loglib import Logging
import termcolor

import cldfbench
from cldfbench.catalogs import BUILTIN_CATALOGS
import cldfbench.commands


def main(args=None, catch_all=False, parsed_args=None):
    parser, subparsers = get_parser_and_subparsers(cldfbench.__name__)

    # Discover available commands:
    # Commands are identified by (<entry point name>).<module name>
    register_subcommands(subparsers, cldfbench.commands, entry_point='cldfbench.commands')

    args = parsed_args or parser.parse_args(args=args)
    if not hasattr(args, "main"):
        parser.print_help()
        return 1

    with Logging(args.log, level=args.log_level):
        with contextlib.ExitStack() as stack:
            for cls in BUILTIN_CATALOGS:
                name = cls.cli_name()
                if hasattr(args, name):
                    try:
                        setattr(
                            args,
                            name,
                            stack.enter_context(
                                cls(getattr(args, name), getattr(args, name + '_version', None))),
                        )
                    except ValueError as e:
                        print(termcolor.colored('\n' + str(e) + '\n', 'red'))
                        return main([args._command, '-h'])

            try:
                return args.main(args) or 0
            except KeyboardInterrupt:  # pragma: no cover
                return 0
            except ParserError as e:
                print(e)
                return main([args._command, '-h'])
            except Exception as e:
                if catch_all:  # pragma: no cover
                    print(e)
                    return 1
                raise


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main() or 0)
