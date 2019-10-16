"""
Run makecldf command of a dataset
"""
from cldfbench.cli_util import with_dataset, add_dataset_spec, add_catalog_spec


def register(parser):
    add_dataset_spec(parser)
    add_catalog_spec(parser, 'glottolog')


def run(args):
    with_dataset(args, 'makecldf')
