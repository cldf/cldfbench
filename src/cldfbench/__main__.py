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
import argparse
import logging

from clldutils.clilib import ParserError
from clldutils.loglib import Logging, get_colorlog

import cldfbench


def discover_commands():
    """ Autodiscover and import all modules in the cldfbench.commands namespace.
    """
    import pkgutil
    import importlib
    import cldfbench.commands
    for _, name, ispkg in pkgutil.iter_modules(cldfbench.commands.__path__):
        if not ispkg:
            ipath = cldfbench.commands.__name__ + "." + name
            yield name, importlib.import_module(ipath)


def main(args=None, catch_all=False, parsed_args=None):  # pragma: no cover
    parser = argparse.ArgumentParser(
        prog=cldfbench.__name__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--log', default=get_colorlog(cldfbench.__name__), help=argparse.SUPPRESS)
    parser.add_argument(
        '--log-level',
        default=logging.INFO,
        help='log level [ERROR|WARN|INFO|DEBUG]',
        type=lambda x: getattr(logging, x))

    subparsers = parser.add_subparsers(
        title="available commands",
        description='Run "COMAMND -h" to get help for a specific command.',
        metavar="COMMAND")

    for name, mod in discover_commands():
        subparser = subparsers.add_parser(
            name,
            help=mod.__doc__.strip().splitlines()[0] if mod.__doc__.strip() else '',
            description=mod.__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        if hasattr(mod, 'register'):
            mod.register(subparser)
        subparser.set_defaults(main=mod.run)

    args = parsed_args or parser.parse_args(args=args)
    if not hasattr(args, "main"):
        parser.print_help()
        return 1

    with Logging(args.log, level=args.log_level):
        try:
            return args.main(args) or 0
        except KeyboardInterrupt:
            return 0
        except ParserError as e:
            print(e)
            parser.print_help()
            return 64
        except Exception as e:
            if catch_all:
                print(e)
                return 1
            raise


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main() or 0)
