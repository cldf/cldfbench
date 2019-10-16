"""
Display basic info about a dataset
"""
from cldfbench.cli_util import with_datasets, add_dataset_spec


def register(parser):
    add_dataset_spec(parser, multiple=True)


def run(args):
    with_datasets(args, lambda ds, _: print(ds))
