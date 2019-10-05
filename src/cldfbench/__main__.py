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
import pathlib

from clldutils.clilib import ArgumentParserWithLogging, command, ParserError

import cldfbench
from cldfbench import scaffold


@command('list')
def list_(args):
    for sc in scaffold.iter_scaffolds():
        print('{}: {}'.format(sc.prefix, sc.__doc__ or ''))


@command()
def new(args):
    """Usage:

    cldfbench new SCAFFOLD_ID OUT_DIR
    """
    # TODO: command to create skeleton for new dataset!
    # (with options for setup.py, test.py, metadata.json?)

    if len(args.args) < 2:
        raise ParserError('scaffold name or output directory missing!')

    for sc in scaffold.iter_scaffolds():
        if sc.prefix == args.args[0]:
            break
    else:
        raise ParserError('Invalid scaffold id: {0}'.format(args.args[0]))

    tmpl = sc()
    md = tmpl.metadata.elicit()
    out = pathlib.Path(args.args[1])
    tmpl.render(out, md)


def main(args=None):
    parser = ArgumentParserWithLogging(cldfbench.__name__)
    sys.exit(parser.main(args))
