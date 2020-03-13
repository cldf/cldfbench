import pathlib
import contextlib
import zipfile
import shutil
from xml.etree import ElementTree as et

import requests
import termcolor

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


def get_url(url, log=None, **kw):
    res = requests.get(url, **kw)
    if log:
        level = log.info if res.status_code == 200 else log.warning
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

    def write_csv(self, fname, rows, **kw):
        with dsv.UnicodeWriter(self._path(fname), **kw) as writer:
            writer.writerows(rows)

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
        if not xlrd:  # pragma: no cover
            raise EnvironmentError(
                'xls2csv is only available when cldfbench is installed with excel support\n'
                'pip install cldfbench[excel]')
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
        if not openpyxl:  # pragma: no cover
            raise EnvironmentError(
                'xlsx2csv is only available when cldfbench is installed with excel support\n'
                'pip install cldfbench[excel]')

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
            sheet = wb[sname]
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
