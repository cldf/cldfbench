import sys
import inspect
import pathlib
import logging
import pkg_resources
import importlib
from datetime import datetime

from clldutils.path import sys_path
from clldutils.misc import lazyproperty, nfilter
from cldfcatalog import Repository

from cldfbench.cldf import CLDFSpec
from cldfbench.datadir import DataDir
from cldfbench.metadata import Metadata

__all__ = ['iter_datasets', 'get_dataset', 'get_datasets', 'Dataset', 'ENTRY_POINT']
ENTRY_POINT = 'cldfbench.dataset'
NOOP = -1


def iter_datasets(ep=ENTRY_POINT):
    """
    Yields `Dataset` instances registered for the specified entry point.

    :param ep: Name of the entry point.
    :return: Generator.
    """
    for ep in pkg_resources.iter_entry_points(ep):
        try:
            cls = ep.load()
            yield cls()  # yield an initialized `Dataset` object.
        except ImportError as e:  # pragma: no cover
            logging.getLogger('cldfbench').warning('Error importing {0}: {1}'.format(ep.name, e))


def get_dataset(spec, ep=ENTRY_POINT):
    """
    Get an initialised `Dataset` instance.

    :param spec: Specification of the dataset, either an ID or a path to amodule.
    :param kw: Keyword arguments to initialize the dataset class with.
    :return: `Dataset` instance.
    """
    # First assume `spec` is the ID of an installed dataset:
    # iterate over registered entry points
    for ds in iter_datasets(ep=ep):
        if ds.id == spec:
            return ds

    # Then check whether `spec` points to a python module:
    # `Dataset` subclass found in the module:
    ds = dataset_from_module(spec)
    if ds:
        return ds


def get_datasets(spec, ep=ENTRY_POINT, glob=False):
    if spec == '*':
        return list(iter_datasets(ep))
    if glob:
        return nfilter(dataset_from_module(p) for p in pathlib.Path('.').glob(spec))
    return nfilter([get_dataset(spec, ep=ep)])


def dataset_from_module(path):
    """
    load the first `Dataset` subclass found in the module without any subclasses.

    :param path:
    :return:
    """
    path = pathlib.Path(path)
    if path.exists() and path.is_file():
        with sys_path(path.parent):
            if path.stem in sys.modules:
                mod = importlib.reload(sys.modules[path.stem])
            else:
                mod = importlib.import_module(path.stem)

        for _, obj in inspect.getmembers(mod):
            if inspect.isclass(obj) and issubclass(obj, Dataset) and not obj.__subclasses__():
                return obj()


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
        self.dir = DataDir(self.dir)
        md = self.dir / 'metadata.json'
        self.metadata = self.metadata_cls.from_file(md) if md.exists() else self.metadata_cls()
        self.metadata.id = self.id

    def __str__(self):
        return '{0.__class__.__name__} "{0.id}" at {1}'.format(self, self.dir.resolve())

    def cldf_specs(self):
        """
        A `Dataset` must declare all CLDF datasets that are derived from it.

        :return: A single `CLDFSpec` instance, or a `dict`, mapping names to `CLDFSpec` \
        instances, where the name will be used by `cldf_reader`/`cldf_writer` to look up \
        the spec.
        """
        return CLDFSpec(dir=self.cldf_dir)

    @property
    def cldf_specs_dict(self):
        """
        Turn cldf_specs into a `dict` for simpler lookup.

        :return: `dict` mapping lookup keys to `CLDFSpec` instances.
        """
        specs = self.cldf_specs()
        if isinstance(specs, CLDFSpec):
            return {None: specs}
        assert isinstance(specs, dict)
        return specs

    @lazyproperty
    def cldf_dir(self):
        return self.dir / 'cldf'

    @lazyproperty
    def raw_dir(self):
        return self.dir / 'raw'

    @lazyproperty
    def etc_dir(self):
        return self.dir / 'etc'

    def cldf_writer(self, args, cldf_spec=None, clean=True):
        """
        :param args:
        :param cldf_spec: Key of the relevant `CLDFSpec` in `Dataset.cldf_specs`
        :param clean: `bool` flag signaling whether to clean the CLDF dir before writing. \
        Note that `False` must be passed for subsequent calls to `cldf_writer` in case the \
        spec re-uses a directory.
        :return: a `cldf_spec.writer_cls` instance, for write-access to CLDF data. \
        This method should be used in a with-statement, and will then return a `CLDFWriter` with \
        an empty working directory.
        """
        if not isinstance(cldf_spec, CLDFSpec):
            cldf_spec = self.cldf_specs_dict[cldf_spec]
        return cldf_spec.get_writer(args=args, dataset=self, clean=clean)

    def cldf_reader(self, cldf_spec=None):
        """
        :param cldf_spec:
        :return: a `pycldf.Dataset` instance, for read-access to the CLDF data.
        """
        if not isinstance(cldf_spec, CLDFSpec):
            cldf_spec = self.cldf_specs_dict[cldf_spec]
        return cldf_spec.get_dataset()

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
        args.log.warning('cmd_{0} not implemented for dataset {1}'.format('download', self.id))
        return NOOP

    def _cmd_readme(self, args):
        if self.metadata:
            self.dir.joinpath('README.md').write_text(self.cmd_readme(args), encoding='utf8')

    def cmd_readme(self, args):
        return self.metadata.markdown() if self.metadata else ''

    def _cmd_makecldf(self, args):
        specs = list(self.cldf_specs_dict.values())
        if len(specs) == 1:
            # There's only one CLDF spec! We instantiate the writer now and inject it into `args`:
            with self.cldf_writer(args, cldf_spec=specs[0]) as writer:
                args.writer = writer
                self.cmd_makecldf(args)
        else:
            self.cmd_makecldf(args)

        if self.metadata and self.metadata.known_license:
            legalcode = self.metadata.known_license.legalcode
            if legalcode:
                (self.dir / 'LICENSE').write_text(legalcode, encoding='utf8')

    def cmd_makecldf(self, args):
        """
        :param args: An `argparse.Namespace` including attributes:
        - `writer`: `CLDFWriter` instance
        """
        args.log.warning('cmd_{0} not implemented for dataset {1}'.format('makecldf', self.id))
        return NOOP
