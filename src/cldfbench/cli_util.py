from time import time

from clldutils.clilib import ParserError
import termcolor

from cldfbench import ENTRY_POINT
from cldfbench import get_dataset as _get
from cldfbench import get_datasets as _gets


class DatasetNotFoundException(Exception):
    pass


def add_entry_point(parser, ep=ENTRY_POINT):
    parser.add_argument(
        '--entry-point',
        help='Name of entry_points to identify datasets',
        default=ep)


def add_dataset_spec(parser, ep=ENTRY_POINT, multiple=False):
    h = "Dataset spec, either ID of installed dataset or path to python module"
    if multiple:
        h += " or simplified glob pattern (where _ is understood as *) " \
             "specifying python modules (requires --glob option!)" \
             " or just _, which will match all datasets of the given --entry-point"
    parser.add_argument(
        'dataset',
        metavar='DATASET',
        help=h + '.')
    add_entry_point(parser, ep=ep)
    if multiple:
        parser.add_argument(
            '--glob',
            action='store_true',
            default=False,
            help="Interpret DATASET as simplified glob pattern relative to cwd.")


def get_dataset(args):
    ds = _get(args.dataset, ep=args.entry_point)
    if ds:
        return ds
    raise ParserError(termcolor.colored(
        '\nInvalid dataset spec: <{0}> {1}\n'.format(args.entry_point, args.dataset), "red"))


def get_datasets(args):
    if args.glob or args.dataset == '_':
        args.dataset = args.dataset.replace('_', '*')
    res = _gets(args.dataset, ep=args.entry_point, glob=args.glob)
    if res:
        return res
    raise ParserError(termcolor.colored(
        '\nInvalid dataset spec: <{0}> {1}\n'.format(args.entry_point, args.dataset), "red"))


def add_catalog_spec(parser, name, with_version=True):
    parser.add_argument(
        '--' + name,
        metavar=name.upper(),
        help='Path to repository clone of {0} data'.format(name.capitalize()),
        default=None)
    if with_version:
        parser.add_argument(
            '--{0}-version'.format(name),
            help='Version of {0} data to checkout'.format(name.capitalize()),
            default=None)


def with_dataset(args, func, dataset=None):
    dataset = dataset or get_dataset(args)
    s = time()
    arg = [dataset]
    if isinstance(func, str):
        func_ = getattr(dataset, '_cmd_' + func, getattr(dataset, 'cmd_' + func, None))
        if not func_:
            raise ParserError('Dataset {0} has no {1} command'.format(dataset.id, func))
        func, arg = func_, []
    args.log.info('running {0} on {1} ...'.format(getattr(func, '__name__', func), dataset.id))
    res = func(*arg, args)
    args.log.info('... done %s [%.1f secs]' % (dataset.id, time() - s))
    return res


def with_datasets(args, func):
    res = []
    for ds in get_datasets(args):
        res.append(with_dataset(args, func, dataset=ds))
    return res
