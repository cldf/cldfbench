"""
Reference catalogs
"""
from cldfcatalog import Catalog
from clldutils.misc import lazyproperty

try:  # pragma: no cover
    from pyglottolog import Glottolog as GlottologAPI
except ImportError:  # pragma: no cover
    GlottologAPI = 'pyglottolog'

try:  # pragma: no cover
    from pyconcepticon import Concepticon as ConcepticonAPI
except ImportError:  # pragma: no cover
    ConcepticonAPI = 'pyconcepticon'

try:  # pragma: no cover
    from pyclts.api import CLTS as CLTSAPI
except ImportError:  # pragma: no cover
    CLTSAPI = 'pyclts'

__all__ = ['Catalog', 'Glottolog', 'Concepticon', 'CLTS', 'BUILTIN_CATALOGS']


class CachingGlottologAPI(GlottologAPI):
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


class Glottolog(Catalog):
    __api__ = CachingGlottologAPI


class CLTS(Catalog):
    __api__ = CLTSAPI


class CachingConcepticonAPI(ConcepticonAPI):
    @lazyproperty
    def cached_glosses(self):
        return {int(cs.id): cs.gloss for cs in self.conceptsets.values()}


class Concepticon(Catalog):
    __api__ = CachingConcepticonAPI


BUILTIN_CATALOGS = [Glottolog, Concepticon, CLTS]
