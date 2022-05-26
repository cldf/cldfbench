import argparse
import json
import typing
from time import time

from clldutils.clilib import ParserError
import termcolor

import pycldf

import cldfbench
from cldfbench import ENTRY_POINT
from cldfbench import get_dataset as _get
from cldfbench import get_datasets as _gets

__all__ = ['DatasetNotFoundException',
           'add_entry_point', 'add_dataset_spec', 'add_catalog_spec',
           'get_dataset', 'get_datasets', 'get_cldf_dataset',
           'with_dataset', 'with_datasets']

IGNORE_MISSING = '-'


class DatasetNotFoundException(Exception):
    pass


def add_entry_point(parser, ep=ENTRY_POINT):
    parser.add_argument(
        '--entry-point',
        help='Name of entry_points to identify datasets',
        default=ep)


def add_dataset_spec(parser, ep=ENTRY_POINT, multiple=False):
    """
    Add arguments and options to specify `cldfbench` Datasets to the CLI.

    :param multiple: Flag signaling whether selection of multiple datasets should be allowed.

    .. note::

        This funtion is supposed to be used in tandem with :func:`get_dataset`, called in a
        command's `run` function.
    """
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


def get_dataset(args: argparse.Namespace) -> cldfbench.Dataset:
    """
    Get the `cldfbench.Dataset` specified by `args`.

    :raises ParserError: If no matching dataset was found.
    """
    ds = _get(args.dataset, ep=args.entry_point)
    if ds:
        return ds
    raise ParserError(termcolor.colored(
        '\nInvalid dataset spec: <{0}> {1}\n'.format(args.entry_point, args.dataset), "red"))


def get_datasets(args: argparse.Namespace) -> typing.List[cldfbench.Dataset]:
    """
    Get the `cldfbench.Dataset` s specified by `args`.

    :raises ParserError: If no matching datasets were found.
    """
    if args.glob or args.dataset == '_':
        args.dataset = args.dataset.replace('_', '*')
    res = _gets(args.dataset, ep=args.entry_point, glob=args.glob)
    if res:
        return res
    raise ParserError(termcolor.colored(
        '\nInvalid dataset spec: <{0}> {1}\n'.format(args.entry_point, args.dataset), "red"))


def get_cldf_dataset(args: argparse.Namespace, cldf_spec=None) -> pycldf.Dataset:
    """
    Get the `pycldf.Dataset` specified by `cldf_spec` for the `cldfbench.Dataset` specified by \
    `args`.
    """
    try:
        return get_dataset(args).cldf_reader(cldf_spec=cldf_spec)
    except (ParserError, ModuleNotFoundError):
        # Try to load plain (i.e. non-cldfbench-enabled) CLDF dataset.
        try:
            return pycldf.Dataset.from_metadata(args.dataset)
        except json.JSONDecodeError:
            return pycldf.Dataset.from_data(args.dataset)


def add_catalog_spec(
        parser: argparse.ArgumentParser,
        name: str,
        with_version: bool = True,
        default=None):
    """
    Add an option for a reference catalog (at a specific version tag) to the CLI.

    :param parser: Subparser for the subcommand.
    :param name: Option name to use for the catalog.
    :param with_version: Flag signaling whether an option to select a version tag for the \
    catalog should be added.
    :param default: The default value for the argument. `None` will trigger config lookup, \
    `IGNORE_MISSING` will set the argument to `None` if no user-supplied value is found.

    .. note::

        If one of the `cldfbench.catalogs.BUILTIN_CATALOGS` is added (using its name as `name`),
        `cldfbench` will add an initialized `cldfcatalog.Catalog` object (with entered context,
        if a particular version was requested) as `name` to the `argparse.Namespace` passed to the
        command's `run` function.
    """
    parser.add_argument(
        '--' + name,
        metavar=name.upper(),
        help='Path to repository clone of {0} data'.format(name.capitalize()),
        default=default)
    if with_version:
        parser.add_argument(
            '--{0}-version'.format(name),
            help='Version of {0} data to checkout'.format(name.capitalize()),
            default=None)


def with_dataset(args: argparse.Namespace, func: typing.Union[callable, str], dataset=None) \
        -> typing.Any:
    """
    Run a callable, passing a dataset and `args` as arguments, returning it's result.

    :param args: CLI arguments
    :param func: Callable with suitable signature or `str`, in which case a method `_cmd_<name>` \
    will be looked up on the dataset and run.
    :param dataset: `cldfbench.Dataset` instance or `None`, in which case a dataset will be \
    retrieved as specified by `args`.
    """
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
    """
    Run `func` on all datasets specified by `args`.

    See :func:`with_dataset` for details.
    """
    res = []
    for ds in get_datasets(args):
        res.append(with_dataset(args, func, dataset=ds))
    return res
