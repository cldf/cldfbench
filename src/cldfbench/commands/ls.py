"""
List installed datasets.
"""
import inspect

from clldutils.markup import Table

from cldfbench.cli_util import add_dataset_spec, get_datasets


def register(parser):
    add_dataset_spec(parser, multiple=True)
    parser.add_argument(
        '--modules',
        help="List only python modules, suitable as DATASET arguments for other commands.",
        action='store_true',
        default=False)


def run(args):
    t = Table('id', 'dir', 'title')
    for ds in get_datasets(args):
        if args.modules:
            print(inspect.getfile(ds.__class__))
            continue
        t.append((ds.id, ds.dir, getattr(ds.metadata, 'title', '')))
    if not args.modules:
        print(t.render(tablefmt='simple'))
