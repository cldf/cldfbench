import inspect
import pathlib
import contextlib
import zipfile
import shutil
import pkg_resources
from xml.etree import ElementTree as et

from clldutils.path import import_module, TemporaryDirectory
from clldutils.misc import xmlchars, lazyproperty, slug
from clldutils import jsonlib
from csvw import dsv
from pycldf.sources import Source
import termcolor
import xlrd
import openpyxl
import requests
import pybtex

from cldfbench.cldf import CLDFWriter

__all__ = ['iter_datasets', 'get_dataset', 'Dataset']


def iter_datasets(ep='cldfbench.dataset'):
    for ep in pkg_resources.iter_entry_points(ep):
        yield ep.load()


def get_dataset(spec, **kw):
    """
    Get an initialised `Dataset` instance.

    :param spec: Specification of the dataset, either an ID or a path to amodule.
    :param kw: Keyword arguments to initialize the dataset class with.
    :return: `Dataset` instance.
    """
    # First assume `spec` is the ID of an installed dataset:
    # iterate over registered entry points
    for cls in iter_datasets():
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

    def __init__(self):
        if not self.dir:
            self.dir = pathlib.Path(inspect.getfile(self.__class__)).parent

    @lazyproperty
    def cldf_dir(self):
        return DataDir(self.dir / 'cldf')

    @lazyproperty
    def raw_dir(self):
        return DataDir(self.dir / 'raw')

    @lazyproperty
    def etc_dir(self):
        return DataDir(self.dir / 'etc')

    def cldf_writer(self, outdir=None, cldf_spec=None):
        return CLDFWriter(outdir or self.cldf_dir, cldf_spec)

    #
    # TODO: workflow commands, to be tied into cli!
    #


def get_url(url, log=None, **kw):
    res = requests.get(url, **kw)
    if log:
        level = log.info if res.status_code == 200 else log.warn
        level('HTTP {0} for {1}'.format(
            termcolor.colored(res.status_code, 'blue'), termcolor.colored(url, 'blue')))
    return res


class DataDir(type(pathlib.Path())):
    def _path(self, fname):
        """
        Interpret strings without "/" as names of files in `self`.

        :param fname:
        :return: `pathlib.Path` instance
        """
        if isinstance(fname, str) and '/' not in fname:
            return self / fname
        return pathlib.Path(fname)

    def read(self, fname, encoding='utf8'):
        return self._path(fname).read_text(encoding=encoding)

    def write(self, fname, text, encoding='utf8'):
        self._path(fname).write_text(text, encoding=encoding)
        return fname

    def read_csv(self, fname, **kw):
        return list(dsv.reader(self._path(fname), **kw))

    def read_xml(self, fname, wrap=True):
        xml = xmlchars(self.read(fname))
        if wrap:
            xml = '<r>{0}</r>'.format(xml)
        return et.fromstring(xml.encode('utf8'))

    def read_json(self, fname, **kw):
        return jsonlib.load(self._path(fname))

    def read_bib(self, fname='sources.bib'):
        bib = pybtex.database.parse_string(self.read(fname), bib_format='bibtex')
        return [Source.from_entry(k, e) for k, e in bib.entries.items()]

    def xls2csv(self, fname, outdir=None):
        fname = self._path(fname)
        res = {}
        outdir = outdir or self
        wb = xlrd.open_workbook(str(fname))
        for sname in wb.sheet_names():
            sheet = wb.sheet_by_name(sname)
            if sheet.nrows:
                path = outdir.joinpath(fname.stem + '.' + slug(sname, lowercase=False) + '.csv')
                with dsv.UnicodeWriter(path) as writer:
                    for i in range(sheet.nrows):
                        writer.writerow([col.value for col in sheet.row(i)])
                res[sname] = path
        return res

    def xlsx2csv(self, fname, outdir=None):
        def _excel_value(x):
            if x is None:
                return ""
            if isinstance(x, float):
                return '{0}'.format(int(x))
            return '{0}'.format(x).strip()

        fname = self._path(fname)
        res = {}
        outdir = outdir or self
        wb = openpyxl.load_workbook(str(fname), data_only=True)
        for sname in wb.sheetnames:
            sheet = wb.get_sheet_by_name(sname)
            path = outdir.joinpath(fname.stem + '.' + slug(sname, lowercase=False) + '.csv')
            with dsv.UnicodeWriter(path) as writer:
                for row in sheet.rows:
                    writer.writerow([_excel_value(col.value) for col in row])
            res[sname] = path
        return res

    @contextlib.contextmanager
    def temp_download(self, url, fname, log=None):
        p = None
        try:
            p = self.download(url, fname, log=log)
            yield p
        finally:
            if p and p.exists():
                p.unlink()

    def download(self, url, fname, log=None, skip_if_exists=False):
        p = self._path(fname)
        if p.exists() and skip_if_exists:
            return p
        res = get_url(url, log=log, stream=True)
        with open(str(self / fname), 'wb') as fp:
            for chunk in res.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    fp.write(chunk)
        return p

    def download_and_unpack(self, url, *paths, **kw):
        """
        Download a zipfile and immediately unpack selected content.

        :param url:
        :param paths:
        :param kw:
        :return:
        """
        with self.temp_download(url, 'ds.zip', log=kw.pop('log', None)) as zipp:
            with TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(str(zipp)) as zipf:
                    for info in zipf.infolist():
                        if (not paths) or info.filename in paths:
                            zipf.extract(info, path=str(tmpdir))
                            shutil.copy(str(tmpdir.joinpath(info.filename)), str(self))
