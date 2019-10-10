"""
Stub command for experimentation
"""
from cldfbench.cli_util import add_catalog_spec


def register(parser):
    add_catalog_spec(parser, 'concepticon')


def run(args):  # pragma: no cover
    pass
