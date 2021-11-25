import argparse
import sys
import typing
import inspect
import pathlib
import logging
import pkg_resources
import importlib
import subprocess
from datetime import datetime

import pycldf
from clldutils.path import sys_path
from clldutils.misc import lazyproperty, nfilter
from cldfcatalog import Repository

from cldfbench.cldf import CLDFSpec, CLDFWriter
from cldfbench.datadir import DataDir
from cldfbench.metadata import Metadata
from cldfbench.ci import build_status_badge

__all__ = ['iter_datasets', 'get_dataset', 'get_datasets', 'Dataset', 'ENTRY_POINT']
ENTRY_POINT = 'cldfbench.dataset'
NOOP = -1


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

    The following class attributes are supposed to be overwritten by subclasses:

    :ivar dir: `pathlib.Path` pointing to the root directory of the dataset.
    :ivar id: A `str` identifier for the dataset. No assumption about uniqueness properties of \
    this identifier is made.
    :ivar metadata_cls: Subclass of :class:`Metadata` (or :class:`Metadata` if not overwritten)
    """
    dir = None
    id = None
    metadata_cls = Metadata
    datadir_cls = DataDir

    def __init__(self):
        if not self.dir:
            self.dir = pathlib.Path(inspect.getfile(self.__class__)).parent
        self.dir = self.datadir_cls(self.dir)
        md = self.dir / 'metadata.json'
        self.metadata = self.metadata_cls.from_file(md) if md.exists() else self.metadata_cls()
        self.metadata.id = self.id

    def __str__(self):
        return '{0.__class__.__name__} "{0.id}" at {1}'.format(self, self.dir.resolve())

    @lazyproperty
    def cldf_dir(self) -> DataDir:
        """
        Directory where CLDF data generated from the Dataset will be stored (unless specified
        differently by a :class:`CLDFSpec`).
        """
        return self.dir / 'cldf'

    @lazyproperty
    def raw_dir(self) -> DataDir:
        """
        Directory where cldfbench expects the raw or source data.
        """
        return self.dir / 'raw'

    @lazyproperty
    def etc_dir(self) -> DataDir:
        """
        Directory where cldfbench expects additional configuration or metadata.
        """
        return self.dir / 'etc'

    def cldf_specs(self) -> typing.Union[CLDFSpec, typing.Dict[str, CLDFSpec]]:
        """
        A `Dataset` must declare all CLDF datasets that are derived from it.

        :return: A single :class:`CLDFSpec` instance, or a `dict`, mapping names to `CLDFSpec` \
        instances, where the name will be used by `cldf_reader`/`cldf_writer` to look up \
        the spec.
        """
        return CLDFSpec(dir=self.cldf_dir)

    @property
    def cldf_specs_dict(self) -> typing.Dict[typing.Union[str, None], CLDFSpec]:
        """
        Turn :meth:`cldf_specs` into a `dict` for simpler lookup.

        :return: `dict` mapping lookup keys to `CLDFSpec` instances.
        """
        specs = self.cldf_specs()
        if isinstance(specs, CLDFSpec):
            return {None: specs}
        assert isinstance(specs, dict)
        return specs

    def update_submodules(self):
        """
        Convenience method to be used in a `Dataset`'s `cmd_download` to update raw data curated
        as git submodules.
        """
        subprocess.check_call(
            'git -C {} submodule update --remote'.format(self.dir.resolve()), shell=True)

    def cldf_writer(self, args, cldf_spec=None, clean=True) -> CLDFWriter:
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

    def cldf_reader(self, cldf_spec: typing.Union[str, None] = None) -> pycldf.Dataset:
        """
        :param cldf_spec:
        :return: a `pycldf.Dataset` instance, for read-access to the CLDF data.
        """
        if not isinstance(cldf_spec, CLDFSpec):
            cldf_spec = self.cldf_specs_dict[cldf_spec]
        return cldf_spec.get_dataset()

    @lazyproperty
    def repo(self) -> typing.Union[Repository, None]:
        """
        The git repository cloned to the dataset's directory (or `None`).
        """
        try:
            return Repository(self.dir)
        except ValueError:  # pragma: no cover
            return

    def _cmd_download(self, args):
        self.raw_dir.mkdir(exist_ok=True)
        self.cmd_download(args)
        (self.raw_dir / 'README.md').write_text(
            'Raw data downloaded {0}'.format(datetime.utcnow().isoformat()), encoding='utf8')

    def cmd_download(self, args: argparse.Namespace):
        """
        Implementations of this methods should populate the dataset's `raw_dir` with the source
        data.
        """
        args.log.warning('cmd_{0} not implemented for dataset {1}'.format('download', self.id))
        return NOOP

    def _cmd_readme(self, args):
        if self.metadata:
            badge = build_status_badge(self)
            md = self.cmd_readme(args)
            if badge:
                lines, title_found = [], False
                for line in md.split('\n'):
                    lines.append(line)
                    if line.startswith('# ') and not title_found:
                        title_found = True
                        lines.extend(['', badge])
                md = '\n'.join(lines)

            section = [
                '\n\n## CLDF Datasets\n',
                'The following CLDF datasets are available in [{0}]({0}):\n'.format(
                    self.cldf_dir.resolve().relative_to(self.dir.resolve())
                )
            ]
            for ds in self.cldf_specs_dict.values():
                if ds.metadata_path.exists():
                    p = ds.metadata_path.resolve().relative_to(self.dir.resolve())
                    section.append(
                        '- CLDF [{0}](https://github.com/cldf/cldf/tree/master/modules/{0}) '
                        'at [{1}]({1})'.format(ds.module, p))

            self.dir.joinpath('README.md').write_text(md + '\n'.join(section), encoding='utf8')

    def cmd_readme(self, args: argparse.Namespace) -> str:
        """
        Implementations of this method should create the content for the dataset's README.md
        and return it as markdown formatted string.
        """
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

    def cmd_makecldf(self, args: argparse.Namespace):
        """
        Implementations of this method should write the CLDF data curated by the dataset.

        :param args: An `argparse.Namespace` including attributes: \
        - `writer`: :class:`CLDFWriter` instance
        """
        args.log.warning('cmd_{0} not implemented for dataset {1}'.format('makecldf', self.id))
        return NOOP


def iter_datasets(ep: str = ENTRY_POINT) -> typing.Generator[Dataset, None, None]:
    """
    Yields `Dataset` instances registered for the specified entry point.

    :param ep: Name of the entry point.
    """
    for ep in pkg_resources.iter_entry_points(ep):
        try:
            cls = ep.load()
            yield cls()  # yield an initialized `Dataset` object.
        except ImportError as e:  # pragma: no cover
            logging.getLogger('cldfbench').warning('Error importing {0}: {1}'.format(ep.name, e))


def get_dataset(spec, ep=ENTRY_POINT) -> Dataset:
    """
    Get an initialised `Dataset` instance.

    :param spec: Specification of the dataset, either an ID or a path to a Python module \
    containing a subclass of :class:`Dataset`.
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


def get_datasets(spec, ep=ENTRY_POINT, glob: bool = False) -> typing.List[Dataset]:
    """
    :param spec: Either `'*'` to get all datasets for a specific entry point, or glob pattern \
    matching dataset modules in the current directory (if `glob == True`), or a `str` as accepted \
    by :func:`get_dataset`.
    """
    if spec == '*':
        return list(iter_datasets(ep))
    if glob:
        return nfilter(dataset_from_module(p) for p in pathlib.Path('.').glob(spec))
    return nfilter([get_dataset(spec, ep=ep)])


def dataset_from_module(path) -> typing.Union[Dataset, None]:
    """
    load the first `Dataset` subclass found in the module which does not have any subclasses.
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
