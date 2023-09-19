"""
`cldfbench` tries to make using (known) reference catalogs while creating CLDF data as simple as
possible. See `BUILTIN_CATALOGS` for a list of "known" catalogs.

For these catalogs, `cldfbench` provides
- support to require (specific versions of) these catalogs in custom `cldfbench` commands,
- support to access the Python API for each catalog from the `Catalog` object,
- automatic registration of catalogs as provenance information when writing CLDF.
"""
import typing

from cldfcatalog import Catalog
from clldutils.misc import lazyproperty

try:  # pragma: no cover
    import pyglottolog
    from pyglottolog.languoids import Languoid
    from pyglottolog.config import Macroarea

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
        def cached_languoids(self) -> typing.Dict[str, Languoid]:
            return {lang.id: lang for lang in self.languoids()}

        @lazyproperty
        def languoid_details(self) -> typing.Dict[str, typing.Tuple]:
            return {lid: (l.iso, l.macroareas, l.name) for lid, l in self.cached_languoids.items()}

        @lazyproperty
        def glottocode_by_name(self) -> typing.Dict[str, str]:
            return {l[2]: lid for lid, l in self.languoid_details.items()}

        @lazyproperty
        def glottocode_by_iso(self) -> typing.Dict[str, str]:
            return {l[0]: lid for lid, l in self.languoid_details.items() if l[0]}

        @lazyproperty
        def macroareas_by_glottocode(self) -> typing.Dict[str, typing.List[Macroarea]]:
            return {lid: l[1] for lid, l in self.languoid_details.items()}

        def get_language(self, languoid: typing.Union[str, Languoid]) \
                -> typing.Union[Languoid, None]:
            """
            :param languoid: A languoid specified via Glottocode or passed as `Languoid` instance.
            :return: Language-level languoid associated with `languoid` or `None` if `languoid` is \
            a family.
            """
            if isinstance(languoid, str):
                languoid = self.cached_languoids[languoid]
            if languoid.level == self.languoid_levels.family:
                return
            if languoid.level == self.languoid_levels.language:
                return languoid
            for _, gc, _ in reversed(languoid.lineage):
                parent = self.cached_languoids[gc]
                if parent.level == self.languoid_levels.language:
                    return parent


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
    """
    - Name: `"glottolog"`
    - Data repository: `glottolog/glottolog <https://github.com/glottolog/glottolog>`_
    - Python API: `pyglottolog <https://pypi.org/project/pyglottolog>`_
    """
    __github__ = "glottolog/glottolog"
    __api__ = CachingGlottologAPI
    __api_pkg__ = pyglottolog


class CLTS(Catalog):
    """
    - Name: `"clts"`
    - Data repository: `cldf-clts/clts <https://github.com/cldf-clts/clts>`_
    - Python API: `pyclts <https://pypi.org/project/pyclts>`_
    """
    __github__ = "cldf-clts/clts"
    __api__ = CLTSAPI
    __api_pkg__ = pyclts


class Concepticon(Catalog):
    """
    - Name: `"concepticon"`
    - Data repository: \
      `concepticon/concepticon-data <https://github.com/concepticon/concepticon-data>`_
    - Python API: `pyconcepticon <https://pypi.org/project/pyconcepticon>`_
    """
    __github__ = "concepticon/concepticon-data"
    __api__ = CachingConcepticonAPI
    __api_pkg__ = pyconcepticon


BUILTIN_CATALOGS = [Glottolog, Concepticon, CLTS]
