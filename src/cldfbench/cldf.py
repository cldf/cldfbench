import sys
import shutil
import pathlib
import warnings
import collections

import attr
from csvw.metadata import Link
import pycldf
from pycldf.dataset import get_modules, MD_SUFFIX, Dataset
from pycldf.util import pkg_path
from cldfcatalog import Repository

from cldfbench.catalogs import Catalog
from cldfbench.util import iter_requirements

__all__ = ['CLDFWriter', 'CLDFSpec']
WITH_ZIPPED = tuple(map(int, pycldf.__version__.split('.')[:2])) >= (1, 29)


class CLDFWriter(object):
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
    def __init__(self, cldf_spec=None, args=None, dataset=None, clean=True):
        """
        :param cldf_spec: `CLDFSpec` instance
        :param args: `argparse.Namespace`, passed if the writer is instantiated from a cli command.
        :param dataset: `cldfbench.Dataset`, passed if instantiated from a dataset method.
        :param clean: `bool` flag signaling whether to clean the CLDF dir before writing.
        """
        self.cldf_spec = cldf_spec or CLDFSpec(dir=getattr(dataset, 'cldf_dir', '.'))
        self.objects = collections.defaultdict(list)
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

    def __getitem__(self, type_):
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
        if WITH_ZIPPED:
            self.write(zipped=self.cldf_spec.zipped, **self.objects)
        else:  # pragma: no cover
            self.write(**self.objects)

    def write(self, **kw):
        self.cldf.properties.setdefault('rdf:type', 'http://www.w3.org/ns/dcat#Distribution')
        srcs = []
        # Let's see whether self.dataset is repository:
        if self.dataset:
            self.cldf.properties.setdefault('rdf:ID', self.dataset.id)
            for k, v in self.dataset.metadata.common_props().items():
                self.cldf.properties.setdefault(k, v)
            if self.dataset.repo:
                if self.dataset.repo.url:
                    self.cldf.properties.setdefault('dcat:accessURL', self.dataset.repo.url)
                srcs.append(self.dataset.repo.json_ld())
        if self.args:
            # We inspect the cli arguments to see whether some `Catalog`'s were used.
            for cat in vars(self.args).values():
                if isinstance(cat, Catalog):
                    srcs.append(cat.json_ld())
        # And check, whether any repositories have been "mounted" via git submodules in raw/:
        if self.dataset and self.dataset.raw_dir.exists():
            for p in self.dataset.raw_dir.iterdir():
                if p.is_dir():
                    try:
                        repo = Repository(p)
                    except ValueError:
                        continue
                    srcs.append(repo.json_ld())
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


@attr.s
class CLDFSpec(object):
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
    dir = attr.ib(converter=lambda s: pathlib.Path(s) if s else s)
    module = attr.ib(
        default='Generic',
        converter=lambda cls: getattr(cls, '__name__', cls),
        validator=attr.validators.in_([m.id for m in get_modules()])
    )
    default_metadata_path = attr.ib(default=None)
    metadata_fname = attr.ib(default=None)
    data_fnames = attr.ib(default=attr.Factory(dict))
    writer_cls = attr.ib(default=CLDFWriter)
    zipped = attr.ib(default=attr.Factory(set))

    def __attrs_post_init__(self):
        if self.zipped and not WITH_ZIPPED:  # pragma: no cover
            warnings.warn('Writing zipped tables requires pycldf >= 1.29', category=UserWarning)
        if self.default_metadata_path:
            self.default_metadata_path = pathlib.Path(self.default_metadata_path)
            try:
                Dataset.from_metadata(self.default_metadata_path)
            except Exception:
                raise ValueError('invalid default metadata: {0}'.format(self.default_metadata_path))
        else:
            self.default_metadata_path = pkg_path(
                'modules', '{0}{1}'.format(self.module, MD_SUFFIX))

        if not self.metadata_fname:
            self.metadata_fname = self.default_metadata_path.name

    @property
    def metadata_path(self):
        return (self.dir / self.metadata_fname) if self.dir else pathlib.Path(self.metadata_fname)

    def make_clean(self):
        self.dir.mkdir(exist_ok=True)
        for p in self.dir.iterdir():
            if p.is_file() and p.name not in ['.gitattributes', 'README.md']:
                p.unlink()
        gitattributes = self.dir / '.gitattributes'
        if not gitattributes.exists():
            with gitattributes.open('wt') as fp:
                fp.write('*.csv text eol=crlf')

    def copy_metadata(self):
        shutil.copy(str(self.default_metadata_path), str(self.metadata_path))

    def get_dataset(self):
        # Initialize a CLDF Dataset:
        return self.cls.from_metadata(self.metadata_path)

    def get_writer(self, args=None, dataset=None, clean=True):
        return self.writer_cls(cldf_spec=self, args=args, dataset=dataset, clean=clean)

    @property
    def cls(self):
        for m in get_modules():
            if m.id == self.module:
                return m.cls
