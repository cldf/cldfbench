"""
Functionality to be plugged into cldfbench datasets to make writing of CLDF datasets easier.
"""
import sys
import shutil
import pathlib
import argparse
import collections
import dataclasses
from typing import Optional, Union

from csvw.metadata import Link, Table, Column
import pycldf
from pycldf.dataset import get_module_impl, get_modules, MD_SUFFIX, Dataset, SchemaObjectType
from pycldf.util import pkg_path
from cldfcatalog import Repository

from cldfbench.catalogs import Catalog
from cldfbench.util import iter_requirements

__all__ = ['CLDFWriter', 'CLDFSpec']


class CLDFWriter:
    """
    An object mediating writing data as proper CLDF dataset.

    Implements a context manager which upon exiting will write all objects acquired within the
    context to disk.

    :ivar cldf_spec: :class:`CLDFSpec` instance, configuring the CLDF dataset written by the writer.
    :ivar objects: `dict` of `list` s to collect the data items. Will be passed as kwargs to \
    `pycldf.Dataset.write`.

    Usage:

    .. code-block:: python

        >>> with Writer(cldf_spec) as writer:
        ...     writer.objects['ValueTable'].append(...)
    """
    def __init__(self,
                 cldf_spec: Optional['CLDFSpec'] = None,
                 args: argparse.Namespace = None,
                 dataset: Optional[pycldf.Dataset] = None,
                 clean: bool = True):
        """
        :param cldf_spec: `CLDFSpec` instance
        :param args: `argparse.Namespace`, passed if the writer is instantiated from a cli command.
        :param dataset: `cldfbench.Dataset`, passed if instantiated from a dataset method.
        :param clean: `bool` flag signaling whether to clean the CLDF dir before writing.
        """
        self.cldf_spec: CLDFSpec = cldf_spec or CLDFSpec(dir=getattr(dataset, 'cldf_dir', '.'))
        self.objects: dict[str, list] = collections.defaultdict(list)
        self.args = args
        self.dataset = dataset
        self._cldf = None
        self._clean = clean

    @property
    def cldf(self) -> pycldf.Dataset:
        """
        The `pycldf.Dataset` used to write the data.

        :raises AttributeError: If accessed outside of the context managed by this writer.
        """
        if self._cldf is None:
            raise AttributeError('Writer.cldf is only set when Writer is used in with statement!')
        return self._cldf

    def __getitem__(self, type_: SchemaObjectType) -> Union[Table, Column]:
        """
        Mirrors `pycldf.Dataset.__getitem__`
        """
        return self.cldf[type_]

    def __enter__(self):
        """
        Upon entering the writer context

        - the target directory is cleaned up,
        - the CLDF metadata is initialized and
        - provided as attribute `cldf`.

        Within the context,

        - the CLDF schema can be manipulated via `CLDFWriter.cldf`, see \
          `<https://pycldf.readthedocs.io/en/latest/dataset.html#editing-metadata-and-schema>`
        - sources can be added, see \
          `<https://pycldf.readthedocs.io/en/latest/dataset.html#adding-data>`
        - data items can be appended to `self.objects`.
        """
        if self._clean:
            self.cldf_spec.make_clean()
        self.cldf_spec.copy_metadata()
        self._cldf = self.cldf_spec.get_dataset()
        for comp, fname in self.cldf_spec.data_fnames.items():
            try:
                t = self._cldf[comp]
                t.url = Link(fname)
            except KeyError:
                self._cldf.add_component(comp, url=fname)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        When exiting the writer context, write data (and metadata) to disk.
        """
        self.write(zipped=self.cldf_spec.zipped, **self.objects)

    @staticmethod
    def _get_sources(
            dataset: Optional[Dataset],
            args: argparse.Namespace,
            props: dict,
    ) -> list[dict]:
        srcs = []
        # Let's see whether self.dataset is repository:
        if dataset:
            props.setdefault('rdf:ID', dataset.id)
            for k, v in dataset.metadata.common_props().items():
                props.setdefault(k, v)
            if dataset.repo:
                if dataset.repo.url:
                    props.setdefault('dcat:accessURL', dataset.repo.url)
                try:
                    srcs.append(dataset.repo.json_ld())
                except:  # pragma: no cover  # noqa: E722  # pylint: disable=W0702
                    # If a git repository has no commit, git describe fails.
                    pass
        if args:
            # We inspect the cli arguments to see whether some `Catalog`'s were used.
            for cat in vars(args).values():
                if isinstance(cat, Catalog):
                    srcs.append(cat.json_ld())
        # And check, whether any repositories have been "mounted" via git submodules in raw/:
        if dataset and dataset.raw_dir.exists():
            for p in dataset.raw_dir.iterdir():
                if p.is_dir():
                    try:
                        repo = Repository(p)
                    except ValueError:
                        continue
                    srcs.append(repo.json_ld())
        return srcs

    def write(self, **kw):
        """
        Write the data specified as lists of rows according to the metadata.
        """
        self.cldf.properties.setdefault('rdf:type', 'http://www.w3.org/ns/dcat#Distribution')
        srcs = self._get_sources(self.dataset, self.args, self.cldf.properties)
        if srcs:
            self.cldf.add_provenance(wasDerivedFrom=srcs)
        reqs = [
            collections.OrderedDict([
                ('dc:title', "python"),
                ('dc:description', sys.version.split()[0])])]
        try:
            self.cldf_spec.dir.joinpath('requirements.txt').write_text(
                '\n'.join(iter_requirements()), encoding='utf8')
            reqs.append(
                collections.OrderedDict([
                    ('dc:title', "python-packages"), ('dc:relation', 'requirements.txt')]))
        except ValueError:  # pragma: no cover
            pass

        self.cldf.add_provenance(wasGeneratedBy=reqs)
        self.cldf.write(**kw)


@dataclasses.dataclass
class CLDFSpec:
    """
    Basic specification to initialize a CLDF Dataset.

    :ivar dir: A directory where the CLDF data is located.
    :ivar module: `pycldf.Dataset` subclass or name of a CLDF module
    :ivar default_metadata_path: Path to the source file for the default metadata for a dataset.
    :ivar metadata_fname: Filename to be used for the actual copy of the metadata.
    :ivar data_fnames: A `dict` mapping component names to custom csv file names (which may be \
    important if multiple different CLDF datasets are created in the same directory).
    :ivar writer_cls: `CLDFWriter` subclass to use for writing the data.
    :ivar zipped: An `iterable` listing component names or csv file names for which the \
    corresponding tables should be zipped.
    """
    dir: pathlib.Path
    module: str = 'Generic'
    default_metadata_path: Optional[pathlib.Path] = None
    metadata_fname: Optional[str] = None
    data_fnames: Optional[dict[str, str]] = dataclasses.field(default_factory=dict)
    writer_cls: type = CLDFWriter
    zipped: Union[set[str], list[str]] = dataclasses.field(default_factory=set)

    def __post_init__(self):
        self.dir = pathlib.Path(self.dir)
        self.module = getattr(self.module, '__name__', self.module)
        if self.module not in {m.id for m in get_modules()}:
            raise ValueError(f'Invalid module: {self.module}')

        if self.default_metadata_path:
            self.default_metadata_path = pathlib.Path(self.default_metadata_path)
            try:
                Dataset.from_metadata(self.default_metadata_path)
            except Exception as e:
                raise ValueError(f'invalid default metadata: {self.default_metadata_path}') from e
        else:
            self.default_metadata_path = pkg_path('modules', f'{self.module}{MD_SUFFIX}')

        if not self.metadata_fname:
            self.metadata_fname = self.default_metadata_path.name

    @property
    def metadata_path(self) -> pathlib.Path:  # pylint: disable=C0116
        return (self.dir / self.metadata_fname) if self.dir else pathlib.Path(self.metadata_fname)

    def make_clean(self):
        """Clean out the cldf directory (typically preparing a new run of `makecldf`)."""
        self.dir.mkdir(exist_ok=True)
        for p in self.dir.iterdir():
            if p.is_file() and p.name not in ['.gitattributes', 'README.md']:
                p.unlink()
        gitattributes = self.dir / '.gitattributes'
        if not gitattributes.exists():
            with gitattributes.open('wt') as fp:
                fp.write('*.csv text eol=crlf')

    def copy_metadata(self):
        """Copy the default metadata to the location specified in spec."""
        shutil.copy(str(self.default_metadata_path), str(self.metadata_path))

    def get_dataset(self) -> pycldf.Dataset:
        """Initialized CLDF Dataset"""
        return self.cls.from_metadata(self.metadata_path)

    def get_writer(self, args=None, dataset=None, clean=True) -> CLDFWriter:
        """An initialized CLDFWriter."""
        return self.writer_cls(cldf_spec=self, args=args, dataset=dataset, clean=clean)

    @property
    def cls(self) -> type:
        """A suitable Dataset subclass to represent the module."""
        res = get_module_impl(Dataset, self.module)
        assert res, self.module
        return res
