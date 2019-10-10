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
import contextlib
import pkg_resources
import collections
import pkgutil
import importlib

from clldutils.clilib import ParserError
from clldutils.loglib import Logging, get_colorlog
import termcolor

import cldfbench
from cldfbench.catalogs import BUILTIN_CATALOGS
import cldfbench.commands


def iter_modules(pkg):
    """ Autodiscover and import all modules in a packge.
    """
    for _, name, ispkg in pkgutil.iter_modules(pkg.__path__):
        if not ispkg:
            yield name, importlib.import_module(".".join([pkg.__name__, name]))


def main(args=None, catch_all=False, parsed_args=None):  # pragma: no cover
    parser = argparse.ArgumentParser(
        prog=cldfbench.__name__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--log',
        default=get_colorlog(cldfbench.__name__),
        help=argparse.SUPPRESS)
    parser.add_argument(
        '--log-level',
        default=logging.INFO,
        help='log level [ERROR|WARN|INFO|DEBUG]',
        type=lambda x: getattr(logging, x))

    subparsers = parser.add_subparsers(
        title="available commands",
        dest="_command",
        description='Run "COMAMND -h" to get help for a specific command.',
        metavar="COMMAND")

    # Discover available commands:
    # Commands are identified by (<entry point name>).<module name>
    _cmds = collections.OrderedDict()
    _cmds.update(list(iter_modules(cldfbench.commands)))
    # ... then look for commands provided in other packages:
    for ep in pkg_resources.iter_entry_points('cldfbench.commands'):
        _cmds.update([('.'.join([ep.name, name]), mod) for name, mod in iter_modules(ep.load())])

    for name, mod in _cmds.items():
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
                        main([args._command, '-h'])
                        return 1

            try:
                return args.main(args) or 0
            except KeyboardInterrupt:
                return 0
            except ParserError as e:
                print(e)
                main([args._command, '-h'])
                return 64
            except Exception as e:
                if catch_all:
                    print(e)
                    return 1
                raise


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main() or 0)
