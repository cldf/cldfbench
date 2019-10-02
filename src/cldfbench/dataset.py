import inspect
import pathlib
import pkg_resources
from xml.etree import ElementTree as et

from clldutils.path import import_module
from clldutils.misc import xmlchars, lazyproperty
from clldutils import jsonlib
from csvw import dsv


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

    Dataset discovery via entry_point:
    TODO
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


class DataDir(type(pathlib.Path())):
    def read(self, fname, encoding='utf8'):
        return self.joinpath(fname).read_text(encoding=encoding)

    def write(self, fname, text, encoding='utf8'):
        self.joinpath(fname).write_text(text, encoding=encoding)
        return fname

    def read_csv(self, fname, **kw):
        return list(dsv.reader(self.joinpath(fname), **kw))

    def read_xml(self, fname, wrap=True):
        xml = xmlchars(self.read(fname))
        if wrap:
            xml = '<r>{0}</r>'.format(xml)
        return et.fromstring(xml.encode('utf8'))

    def read_json(self, fname, **kw):
        return jsonlib.load(fname)

    #def read_bib(self, fname='sources.bib'):
    #    bib = database.parse_string(self.read(fname), bib_format='bibtex')
    #    return [Source.from_entry(k, e) for k, e in bib.entries.items()]
