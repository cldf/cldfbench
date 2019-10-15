from time import time

from clldutils.clilib import ParserError

from cldfbench import get_dataset, ENTRY_POINT


class DatasetNotFoundException(Exception):
    pass


def add_entry_point(parser, ep=ENTRY_POINT):
    parser.add_argument(
        '--entry-point',
        help='Name of entry_points to identify datasets',
        default=ep)


def add_dataset_spec(parser, ep=ENTRY_POINT):
    parser.add_argument(
        'dataset',
        metavar='DATASET',
        help='Dataset spec, either ID of installed dataset or path to python module')
    add_entry_point(parser, ep=ep)


def add_catalog_spec(parser, name):
    parser.add_argument(
        name,
        metavar=name.upper(),
        help='Path to repository clone of {0} data'.format(name.capitalize()))
    parser.add_argument(
        '--{0}-version'.format(name),
        help='Version of {0} data to checkout'.format(name.capitalize()),
        default=None)


def with_dataset(args, func, dataset=None):
    dataset = dataset or get_dataset(args.dataset, ep=args.entry_point)
    s = time()
    arg = [dataset]
    if isinstance(func, str):
        func_ = getattr(dataset, '_cmd_' + func, getattr(dataset, 'cmd_' + func, None))
        if not func_:
            raise ParserError('Dataset {0} has no {1} command'.format(dataset.id, func))
        func, arg = func_, []
    args.log.info('running {0} on {1} ...'.format(getattr(func, '__name__', func), dataset.id))
    func(*arg, args)
    args.log.info('... done %s [%.1f secs]' % (dataset.id, time() - s))
