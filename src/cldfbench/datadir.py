import gzip
import shutil
import typing
import pathlib
import zipfile
import itertools
import contextlib
from xml.etree import ElementTree as et
import collections
import unicodedata

import requests
import termcolor

try:
    from odf.opendocument import load as load_odf
except ImportError:  # pragma: no cover
    load_odf = None

try:
    import xlrd
except ImportError:  # pragma: no cover
    xlrd = None
try:
    import openpyxl
except ImportError:  # pragma: no cover
    openpyxl = None

import pybtex
from csvw import dsv
from clldutils.misc import xmlchars, slug
from clldutils.path import TemporaryDirectory
from clldutils import jsonlib
from pycldf.sources import Source


__all__ = ['get_url', 'DataDir']


ODF_NS_TABLE = 'urn:oasis:names:tc:opendocument:xmlns:table:1.0'
ODF_NS_TEXT = 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'


def _real_len(seq, pred=bool):
    for index in range(len(seq) - 1, -1, -1):
        if pred(seq[index]):
            return index + 1
    else:
        return 0


def _ods_value(cell):
    return ' '.join(
        str(e).strip()
        for e in cell.childNodes
        if e.qname == (ODF_NS_TEXT, 'p'))


def _ods_cells(row):
    cells = [
        (
            _ods_value(cell),
            int(
                cell.attributes.get((ODF_NS_TABLE, 'number-columns-repeated'))
                or '1')
        )
        for cell in row.childNodes
        if cell.qname == (ODF_NS_TABLE, 'table-cell')]

    real_len = _real_len(cells, pred=lambda pair: bool(pair[0]))
    return [
        cloned_cell
        for cell, number in itertools.islice(cells, real_len)
        for cloned_cell in itertools.repeat(cell, number)]


def _pad_list(li, length):
    if len(li) >= length:
        return li
    else:
        return [e for e in itertools.chain(li, itertools.repeat('', length - len(li)))]


def _ods_to_list(table):
    rows = [
        (
            _ods_cells(row),
            int(
                row.attributes.get((ODF_NS_TABLE, 'number-rows-repeated'))
                or '1')
        )
        for row in table.childNodes
        if row.qname == (ODF_NS_TABLE, 'table-row')]

    real_len = _real_len(rows, pred=lambda pair: bool(pair[0]))

    max_width = max(len(row) for row, _ in rows)
    rows = ((_pad_list(row, max_width), number) for row, number in rows)
    return [
        cloned_row
        for row, number in itertools.islice(rows, real_len)
        for cloned_row in itertools.repeat(row, number)]


def get_url(url, log=None, **kw):
    res = requests.get(url, **kw)
    if log:
        level = log.info if res.status_code == 200 else log.warning
        level('HTTP {0} for {1}'.format(
            termcolor.colored(res.status_code, 'blue'), termcolor.colored(url, 'blue')))
    return res


class DataDir(type(pathlib.Path())):
    """
    A `pathlib.Path` augmented with functionality to read common data formats.
    """
    def _path(self, fname):
        """
        Interpret strings without "/" as names of files in `self`.

        :param fname:
        :return: `pathlib.Path` instance
        """
        if isinstance(fname, str) and '/' not in fname:
            return self / fname
        return pathlib.Path(fname)

    def read(self,
             fname: typing.Union[str, pathlib.Path],
             aname: str = None,
             normalize: str = None,
             suffix: str = None,
             encoding='utf8') -> str:
        """
        Read text data from a file.

        :param fname: Name of a file in `DataDir` or any `pathlib.Path`.
        :param aname: "file in archive" name, if a file from a zip archive is to be read.
        :param suffix: If `None`, suffix will be infered from the path to be read. Otherwise \
        it can be used to force reading compressed content passing `.gz` or `.zip`.
        :param normalize: Any normalization form understood by `unicodedata.normalize`.
        """
        p = self._path(fname)
        suffix = suffix or p.suffix
        if suffix == '.zip':
            zip = zipfile.ZipFile(str(p))
            text = zip.read(aname or zip.namelist()[0]).decode(encoding)
        elif suffix == '.gz':
            with gzip.open(p) as fp:
                text = fp.read().decode(encoding)
        else:
            text = p.read_text(encoding=encoding)

        if normalize:
            text = unicodedata.normalize(normalize, text)
        return text

    def write(self, fname, text, encoding='utf8'):
        self._path(fname).write_text(text, encoding=encoding)
        return fname

    def read_csv(self, fname, normalize=None, **kw) -> list:
        """
        Read CSV data from a file.
        """
        if not normalize:
            return list(dsv.reader(self._path(fname), **kw))
        if kw.get('dicts'):
            return [collections.OrderedDict(
                [(k, unicodedata.normalize(normalize, v)) for k, v in row.items()]
            ) for row in dsv.reader(self._path(fname), **kw)]
        else:
            return [[unicodedata.normalize(normalize, k) for k in row]
                    for row in dsv.reader(self._path(fname), **kw)]

    def write_csv(self, fname, rows, **kw):
        with dsv.UnicodeWriter(self._path(fname), **kw) as writer:
            writer.writerows(rows)

    def read_xml(self, fname, wrap=True) -> et.Element:
        xml = xmlchars(self.read(fname))
        if wrap:
            xml = '<r>{0}</r>'.format(xml)
        return et.fromstring(xml.encode('utf8'))

    def read_json(self, fname, **kw) -> typing.Union[str, list, dict]:
        return jsonlib.load(self._path(fname))

    def read_bib(self, fname='sources.bib') -> typing.List[Source]:
        bib = pybtex.database.parse_string(self.read(fname), bib_format='bibtex')
        return [Source.from_entry(k, e) for k, e in bib.entries.items()]

    def ods2csv(self, fname, outdir=None):
        """
        Dump the data from an OpenDocument Spreadsheet (suffix .ODS) file to CSV.

        .. note::

            Requires `cldfbench` to be installed with extra "odf".
        """
        if not load_odf:  # pragma: no cover
            raise EnvironmentError(
                'ods2csv is only available when cldfbench is installed with odf support\n'
                'pip install cldfbench[odf]')

        fname = self._path(fname)
        ods_data = load_odf(fname)
        tables = [
            e for e in ods_data.spreadsheet.childNodes
            if e.qname == (ODF_NS_TABLE, 'table')]

        outdir = outdir or self
        res = {}
        for table in tables:
            table_name = table.attributes[ODF_NS_TABLE, 'name']
            csv_path = outdir / '{}.{}.csv'.format(
                fname.stem,
                slug(table_name, lowercase=False))
            with dsv.UnicodeWriter(csv_path) as writer:
                writer.writerows(_ods_to_list(table))
            res[table_name] = csv_path
        return res

    def xls2csv(self, fname, outdir=None):
        """
        Dump the data from an Excel XLS file to CSV.

        .. note::

            Requires `cldfbench` to be installed with extra "excel".
        """
        if not xlrd:  # pragma: no cover
            raise EnvironmentError(
                'xls2csv is only available when cldfbench is installed with excel support\n'
                'pip install cldfbench[excel]')
        fname = self._path(fname)
        res = {}
        outdir = outdir or self
        try:
            wb = xlrd.open_workbook(str(fname))
        except xlrd.biffh.XLRDError as e:
            if 'xlsx' in str(e):
                raise ValueError('To read xlsx files, call xlsx2csv!')
            raise  # pragma: no cover
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
        """
        Dump the data from an Excel XLSX file to CSV.

        .. note::

            Requires `cldfbench` to be installed with extra "excel".
        """
        if not openpyxl:  # pragma: no cover
            raise EnvironmentError(
                'xlsx2csv is only available when cldfbench is installed with excel support\n'
                'pip install cldfbench[excel]')

        def _excel_value(x):
            if x is None:
                return ""
            if isinstance(x, float) and int(x) == x:
                # Since Excel does not have an integer type, integers are rendered as "n.0",
                # which in turn confuses type detection of tools like csvkit. Thus, we normalize
                # numbers of the form "n.0" to "n".
                return '{0}'.format(int(x))  # pragma: no cover
            return '{0}'.format(x).strip()

        fname = self._path(fname)
        res = {}
        outdir = outdir or self
        wb = openpyxl.load_workbook(str(fname), data_only=True)
        for sname in wb.sheetnames:
            sheet = wb[sname]
            path = outdir.joinpath(fname.stem + '.' + slug(sname, lowercase=False) + '.csv')
            with dsv.UnicodeWriter(path) as writer:
                for row in sheet.rows:
                    writer.writerow([_excel_value(col.value) for col in row])
            res[sname] = path
        return res

    @contextlib.contextmanager
    def temp_download(self, url, fname, log=None):
        """
        Context manager to use when downloaded data needs to be manipulated before storage \
        (e.g. to anonymize it).

        Usage:

        .. code-block:: python

            with ds.raw_dir.temp_download('http://example.org/data.txt') as p:
                ds.raw_dir.write('data.txt', p.read_text(encoding='utf8').split('##')[0])
        """
        p = None
        try:
            p = self.download(url, fname, log=log)
            yield p
        finally:
            if p and p.exists():
                p.unlink()

    def download(self, url, fname, log=None, skip_if_exists=False):
        """
        Download data from a URL to the directory.
        """
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
        """
        with self.temp_download(url, 'ds.zip', log=kw.pop('log', None)) as zipp:
            with TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(str(zipp)) as zipf:
                    for info in zipf.infolist():
                        if (not paths) or info.filename in paths:
                            zipf.extract(info, path=str(tmpdir))
                            shutil.copy(str(tmpdir.joinpath(info.filename)), str(self))
