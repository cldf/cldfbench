"""
Reference catalogs
"""
from cldfcatalog import Catalog

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


class Glottolog(Catalog):
    __api__ = GlottologAPI


class CLTS(Catalog):
    __api__ = CLTSAPI


class Concepticon(Catalog):
    __api__ = ConcepticonAPI


BUILTIN_CATALOGS = [Glottolog, Concepticon, CLTS]
