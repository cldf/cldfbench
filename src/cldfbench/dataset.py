import inspect
import pathlib
import pkg_resources
import logging
from datetime import datetime

from clldutils.path import import_module
from clldutils.misc import lazyproperty

import cldfbench
from cldfbench.cldf import CLDFWriter
from cldfbench.repository import Repository
from cldfbench.datadir import DataDir
from cldfbench.metadata import Metadata

__all__ = ['iter_datasets', 'get_dataset', 'Dataset', 'ENTRY_POINT']
ENTRY_POINT = 'cldfbench.dataset'
NOOP = -1


def iter_datasets(ep=ENTRY_POINT):
    for ep in pkg_resources.iter_entry_points(ep):
        yield ep.load()


def get_dataset(spec, ep=ENTRY_POINT, **kw):
    """
    Get an initialised `Dataset` instance.

    :param spec: Specification of the dataset, either an ID or a path to amodule.
    :param kw: Keyword arguments to initialize the dataset class with.
    :return: `Dataset` instance.
    """
    # First assume `spec` is the ID of an installed dataset:
    # iterate over registered entry points
    for cls in iter_datasets(ep=ep):
        if cls.id == spec:
            return cls(**kw)

    # Then check whether `spec` points to a python module and if so, load the first
    # `Dataset` subclass found in the module:
    p = pathlib.Path(spec)
    if p.exists() and p.is_file():
        mod = import_module(p)
        for _, obj in inspect.getmembers(mod):
            if inspect.isclass(obj) and issubclass(obj, Dataset) and obj != Dataset:
                return obj(**kw)


class Dataset(object):
    """
    A cldfbench dataset ties together
    - `raw` data, to be used as source for the
    - `cldf` data, which is created using config data from
    - `etc`.

    To use the cldfbench infrastructure, one should sub-class `Dataset`.

    cldfbench supports the following workflow:
    - a `download` command populates a `Dataset`'s `raw` directory.
    - a `makecldf` command (re)creates the CLDF dataset in `cldf`.
    """
    dir = None
    id = None
    metadata_cls = Metadata

    def __init__(self):
        if not self.dir:
            self.dir = pathlib.Path(inspect.getfile(self.__class__)).parent
        md = self.dir / 'metadata.json'
        self.metadata = self.metadata_cls.from_file(md) if md.exists() else self.metadata_cls()
        self.metadata.id = self.id

    def __str__(self):
        return '{0.__class__.__name__} "{0.id}" at {1}'.format(self, self.dir.resolve())

    @lazyproperty
    def cldf_dir(self):
        return DataDir(self.dir / 'cldf')

    @lazyproperty
    def raw_dir(self):
        return DataDir(self.dir / 'raw')

    @lazyproperty
    def etc_dir(self):
        return DataDir(self.dir / 'etc')

    def cldf_writer(self, args, outdir=None, cldf_spec=None):
        return CLDFWriter(outdir or self.cldf_dir, cldf_spec=cldf_spec, args=args, dataset=self)

    @lazyproperty
    def repo(self):
        try:
            return Repository(self.dir)
        except ValueError:  # pragma: no cover
            return

    #
    # Workflow commands are implemented with two methods for each command:
    # - cmd_<command>: The implementation of the command, typically overwritten by datasets.
    # - _cmd_<command>: An (optional) wrapper providing setup and teardown functionality, calling
    #   cmd_<command> in between.
    #
    # Workflow commands must accept an `argparse.Namespace` as sole positional argument.
    #
    def _cmd_download(self, args):
        if not self.raw_dir.exists():
            self.raw_dir.mkdir()
        self.cmd_download(args)
        (self.raw_dir / 'README.md').write_text(
            'Raw data downloaded {0}'.format(datetime.utcnow().isoformat()), encoding='utf8')

    def cmd_download(self, args):
        self._not_implemented('download')
        return NOOP

    def cmd_makecldf(self, args):
        self._not_implemented('makecldf')
        return NOOP

    def _not_implemented(self, method):
        log = logging.getLogger(cldfbench.__name__)
        log.warning('cmd_{0} not implemented for dataset {1}'.format(method, self.id))
