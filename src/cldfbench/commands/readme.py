"""
Write dataset metadata to a README.md in the dataset's directory.
"""
from cldfbench.cli_util import add_dataset_spec, with_datasets


def register(parser):
    add_dataset_spec(parser, multiple=True)


def run(args):
    with_datasets(args, 'readme')
