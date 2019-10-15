import sys
import inspect
import pathlib
import pkg_resources
import logging
import importlib
from datetime import datetime

from clldutils.path import sys_path
from clldutils.misc import lazyproperty
from cldfcatalog import Repository

import cldfbench
from cldfbench.cldf import CLDFWriter, CLDFSpec
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
        with sys_path(p.parent):
            if p.stem in sys.modules:
                mod = importlib.reload(sys.modules[p.stem])
            else:
                mod = importlib.import_module(p.stem)

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
    cldf_writer_cls = CLDFWriter

    def __init__(self):
        if not self.dir:
            self.dir = pathlib.Path(inspect.getfile(self.__class__)).parent
        self.dir = DataDir(self.dir)
        md = self.dir / 'metadata.json'
        self.metadata = self.metadata_cls.from_file(md) if md.exists() else self.metadata_cls()
        self.metadata.id = self.id

    def __str__(self):
        return '{0.__class__.__name__} "{0.id}" at {1}'.format(self, self.dir.resolve())

    @lazyproperty
    def cldf_dir(self):
        return self.dir / 'cldf'

    @lazyproperty
    def raw_dir(self):
        return self.dir / 'raw'

    @lazyproperty
    def etc_dir(self):
        return self.dir / 'etc'

    @property
    def default_cldf_spec(self):
        """
        For the typical case of a `Dataset` being used to write one CLDF dataset, this property
        can be used to "synchronise" `cldf_writer` and `cldf_reader`, since both these methods
        will use `default_cldf_spec` to determine the location of the CLDF metadata file.

        :return: `CLDFSpec` instance.
        """
        return CLDFSpec(dir=self.cldf_dir)

    def cldf_writer(self, args, cldf_spec=None):
        """
        :param args:
        :param cldf_spec:
        :return: a `self.cldf_writer_cls` instance, for write-access to CLDF data. \
        This method should be used in a with-statement, and will then return a `CLDFWriter` with \
        an empty working directory.
        """
        return self.cldf_writer_cls(
            cldf_spec=cldf_spec or self.default_cldf_spec, args=args, dataset=self)

    def cldf_reader(self, cldf_spec=None):
        """
        :param cldf_spec:
        :return: a `pycldf.Dataset` instance, for read-access to the CLDF data.
        """
        return (cldf_spec or self.default_cldf_spec).get_dataset()

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
        self.raw_dir.mkdir(exist_ok=True)
        self.cmd_download(args)
        (self.raw_dir / 'README.md').write_text(
            'Raw data downloaded {0}'.format(datetime.utcnow().isoformat()), encoding='utf8')

    def cmd_download(self, args):
        self._not_implemented('download')
        return NOOP

    def cmd_makecldf(self, args):
        """
        :param args: An `argparse.Namespace` including attributes:
        - `writer`: `CLDFWriter` instance
        """
        self._not_implemented('makecldf')
        return NOOP

    def _not_implemented(self, method):
        log = logging.getLogger(cldfbench.__name__)
        log.warning('cmd_{0} not implemented for dataset {1}'.format(method, self.id))
