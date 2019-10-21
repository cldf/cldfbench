"""
Reference catalogs
"""
from cldfcatalog import Catalog
from clldutils.misc import lazyproperty

try:  # pragma: no cover
    import pyglottolog

    class CachingGlottologAPI(pyglottolog.Glottolog):
        def __init__(self, p):
            super().__init__(p)
            self.__languoids = None

        def languoids(self, **kw):
            if not kw:
                if not self.__languoids:
                    self.__languoids = list(super().languoids())
                return self.__languoids
            return super().languoids(**kw)

        @lazyproperty
        def cached_languoids(self):
            return {l.id: l for l in self.languoids()}

        @lazyproperty
        def languoid_details(self):
            return {lid: (l.iso, l.macroareas, l.name) for lid, l in self.cached_languoids.items()}

        @lazyproperty
        def glottocode_by_name(self):
            return {l[2]: lid for lid, l in self.languoid_details.items()}

        @lazyproperty
        def glottocode_by_iso(self):
            return {l[0]: lid for lid, l in self.languoid_details.items() if l[0]}

        @lazyproperty
        def macroareas_by_glottocode(self):
            return {lid: l[1] for lid, l in self.languoid_details.items()}

except ImportError:  # pragma: no cover
    CachingGlottologAPI = pyglottolog = 'pyglottolog'

try:  # pragma: no cover
    import pyconcepticon

    class CachingConcepticonAPI(pyconcepticon.Concepticon):
        @lazyproperty
        def cached_glosses(self):
            return {int(cs.id): cs.gloss for cs in self.conceptsets.values()}

except ImportError:  # pragma: no cover
    CachingConcepticonAPI = pyconcepticon = 'pyconcepticon'

try:  # pragma: no cover
    import pyclts

    class CLTSAPI(pyclts.api.CLTS):
        pass

except ImportError:  # pragma: no cover
    CLTSAPI = pyclts = 'pyclts'

__all__ = ['Catalog', 'Glottolog', 'Concepticon', 'CLTS', 'BUILTIN_CATALOGS']


class Glottolog(Catalog):
    __github__ = "glottolog/glottolog"
    __api__ = CachingGlottologAPI
    __api_pkg__ = pyglottolog


class CLTS(Catalog):
    __github__ = "cldf-clts/clts"
    __api__ = CLTSAPI
    __api_pkg__ = pyclts


class Concepticon(Catalog):
    __github__ = "concepticon/concepticon-data"
    __api__ = CachingConcepticonAPI
    __api_pkg__ = pyconcepticon


BUILTIN_CATALOGS = [Glottolog, Concepticon, CLTS]
