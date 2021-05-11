"""
Run makecldf command of a dataset
"""
from cldfbench.cli_util import with_dataset, add_dataset_spec, add_catalog_spec
from cldfbench.commands import cldfreadme, zenodo


def register(parser):
    parser.add_argument(
        '--with-cldfreadme',
        help="Run 'cldfbench cldfreadme' after successfull CLDF creation",
        action='store_true',
        default=False,
    )
    parser.add_argument(
        '--with-zenodo',
        help="Run 'cldfbench zenodo' after successfull CLDF creation",
        action='store_true',
        default=False,
    )
    parser.add_argument(
        '--communities',
        default='',
        help='Comma-separated list of communities to which the dataset should be submitted, '
             'passed through to "cldfbench zenodo"',
    )
    add_dataset_spec(parser)
    add_catalog_spec(parser, 'glottolog')


def run(args):
    with_dataset(args, 'makecldf')
    if getattr(args, 'with_cldfreadme', None):
        cldfreadme.run(args)
    if getattr(args, 'with_zenodo', None):
        zenodo.run(args)
