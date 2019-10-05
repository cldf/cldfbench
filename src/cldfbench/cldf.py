import collections
import shutil

from pycldf.dataset import get_modules, MD_SUFFIX
from pycldf.util import pkg_path


class Writer(object):
    """
    An object mediating writing data as proper CLDF dataset.

    In particular, this class
    - implements a context manager which upon exiting will write all objects acquired within the
      context to disk,
    - provides a facade for most of the relevant attributes of a `pycldf.Dataset`.

    Usage:
    >>> with Writer(ds) as writer:
    ...     writer.objects['ValueTable'].append(...)
    """
    def __init__(self, dataset):
        self.dataset = dataset
        self.objects = collections.defaultdict(list)

        mid = getattr(self.dataset.cldf_spec.module, '__name__', self.dataset.cldf_spec.module)
        for mod in get_modules():
            if mod.id == mid:
                break
        else:
            raise ValueError('Unknown CLDF module: {0}'.format(mid))

        if not self.dataset.cldf_dir.exists():
            self.dataset.cldf_dir.mkdir()

        md = self.dataset.cldf_spec.metadata
        if not md:
            md = pkg_path('modules', '{0}{1}'.format(mod.id, MD_SUFFIX))

        mdname = self.dataset.cldf_spec.metadata_name
        if not mdname:
            mdname = 'cldf{0}'.format(MD_SUFFIX)

        shutil.copy(str(md), str(self.dataset.cldf_dir / mdname))
        self.cldf = mod.cls.from_metadata(self.dataset.cldf_dir / mdname)

    def validate(self, log=None):
        return self.cldf.validate(log)

    def __getitem__(self, type_):
        return self.cldf[type_]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.write(**self.objects)

    def write(self, **kw):
        # self.cldf.properties.update(self.dataset.metadata.common_props)
        self.cldf.properties['rdf:ID'] = self.dataset.id
        self.cldf.properties['rdf:type'] = 'http://www.w3.org/ns/dcat#Distribution'
        # if self.dataset.github_repo:
        #    self.cldf.properties['dcat:accessURL'] = 'https://github.com/{0}'.format(
        #        self.dataset.github_repo)

        # self.cldf.add_provenance()

        # self.cldf.tablegroup.notes.append(collections.OrderedDict([
        #    ('dc:title', 'environment'),
        #    ('properties', collections.OrderedDict([
        #        ('glottolog_version', self.dataset.glottolog.version),
        #        ('concepticon_version', self.dataset.concepticon.version),
        #    ]))
        # ]))
        self.cldf.write(**kw)
