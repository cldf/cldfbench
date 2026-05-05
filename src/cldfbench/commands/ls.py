"""
List installed datasets.
"""
import io
import inspect

from clldutils.clilib import Table, add_format

from cldfbench.cli_util import add_dataset_spec, get_datasets


def register(parser):  # pylint: disable=C0116
    add_dataset_spec(parser, multiple=True)
    add_format(parser, 'simple')
    parser.add_argument(
        '--modules',
        help="List only python modules, suitable as DATASET arguments for other commands.",
        action='store_true',
        default=False)


def run(args):  # pylint: disable=C0116
    kw = {'file': io.StringIO()} if args.modules else {}
    with Table(args, 'id', 'dir', 'title', **kw) as t:
        for ds in get_datasets(args):
            if args.modules:
                print(inspect.getfile(ds.__class__))
                continue
            t.append((ds.id, ds.dir, getattr(ds.metadata, 'title', '')))
