"""
`cldfbench` tries to make using (known) reference catalogs while creating CLDF data as simple as
possible. See `BUILTIN_CATALOGS` for a list of "known" catalogs.

For these catalogs, `cldfbench` provides
- support to require (specific versions of) these catalogs in custom `cldfbench` commands,
- support to access the Python API for each catalog from the `Catalog` object,
- automatic registration of catalogs as provenance information when writing CLDF.
"""
from typing import Union, Optional
import functools

from cldfcatalog import Catalog

try:  # pragma: no cover
    import pyglottolog
    from pyglottolog.languoids import Languoid
    from pyglottolog.config import Macroarea

    class CachingGlottologAPI(pyglottolog.Glottolog):
        """Wraps Glottolog to avoid expensive lookups."""
        def __init__(self, p):
            super().__init__(p)
            self.__languoids = None

        def languoids(self, *args, **kw):  # pylint: disable=C0116
            if not kw:
                if not self.__languoids:
                    self.__languoids = list(super().languoids())
                return self.__languoids
            return super().languoids(*args, **kw)

        @functools.cached_property
        def cached_languoids(self) -> dict[str, Languoid]:  # pylint: disable=C0116
            return {lang.id: lang for lang in self.languoids()}

        @functools.cached_property
        def languoid_details(self) -> dict[str, tuple[str, list, str]]:  # pylint: disable=C0116
            return {lid: (l.iso, l.macroareas, l.name) for lid, l in self.cached_languoids.items()}

        @functools.cached_property
        def glottocode_by_name(self) -> dict[str, str]:  # pylint: disable=C0116
            return {l[2]: lid for lid, l in self.languoid_details.items()}

        @functools.cached_property
        def glottocode_by_iso(self) -> dict[str, str]:  # pylint: disable=C0116
            return {l[0]: lid for lid, l in self.languoid_details.items() if l[0]}

        @functools.cached_property
        def macroareas_by_glottocode(self) -> dict[str, list[Macroarea]]:  # pylint: disable=C0116
            return {lid: l[1] for lid, l in self.languoid_details.items()}

        def get_language(self, languoid: Union[str, Languoid]) -> Optional[Languoid]:
            """
            :param languoid: A languoid specified via Glottocode or passed as `Languoid` instance.
            :return: Language-level languoid associated with `languoid` or `None` if `languoid` is \
            a family.
            """
            if isinstance(languoid, str):
                languoid = self.cached_languoids[languoid]
            if languoid.level == self.languoid_levels.family:
                return None
            if languoid.level == self.languoid_levels.language:
                return languoid
            for _, gc, _ in reversed(languoid.lineage):
                parent = self.cached_languoids[gc]
                if parent.level == self.languoid_levels.language:
                    return parent
            return None


except ImportError:  # pragma: no cover
    CachingGlottologAPI = pyglottolog = 'pyglottolog'  # pylint: disable=invalid-name

try:  # pragma: no cover
    import pyconcepticon

    class CachingConcepticonAPI(pyconcepticon.Concepticon):
        """Wraps Concepticon to avoid expensive file reads."""
        @functools.cached_property
        def cached_glosses(self) -> dict[int, str]:  # pylint: disable=C0116
            return {int(cs.id): cs.gloss for cs in self.conceptsets.values()}

except ImportError:  # pragma: no cover
    CachingConcepticonAPI = pyconcepticon = 'pyconcepticon'  # pylint: disable=invalid-name

try:  # pragma: no cover
    import pyclts

    class CLTSAPI(pyclts.api.CLTS):
        """Cross-Linguistic Transcription Systems API."""

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
