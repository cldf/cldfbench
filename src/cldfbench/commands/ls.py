"""
List installed datasets.
"""
import inspect

from clldutils.markup import Table

from cldfbench.cli_util import add_entry_point
from cldfbench import iter_datasets


def register(parser):
    add_entry_point(parser)
    parser.add_argument(
        '--modules',
        help="List only python modules, suitable as DATASET arguments for other commands.",
        action='store_true',
        default=False)


def run(args):
    t = Table('id', 'dir', 'title')
    for ds in iter_datasets(ep=args.entry_point):
        if args.modules:
            print(inspect.getfile(ds))
            continue
        ds = ds()
        t.append((ds.id, ds.dir, getattr(ds.metadata, 'title', '')))
    if not args.modules:
        print(t.render(tablefmt='simple'))
