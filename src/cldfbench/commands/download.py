"""
Run download command of a dataset
"""
from cldfbench.cli_util import with_dataset, add_dataset_spec


def register(parser):  # pylint: disable=C0116
    add_dataset_spec(parser)


def run(args):  # pylint: disable=C0116
    with_dataset(args, 'download')
