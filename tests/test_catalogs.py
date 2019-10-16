from cldfbench.catalogs import *


def test_Glottolog(glottolog_dir):
    cat = Glottolog(glottolog_dir)
    assert cat.api.languoids(ids=['abcd1234'])
    l = cat.api.languoids()
    assert cat.api.languoids() is l
    assert 'abcd1234' in cat.api.cached_languoids
    assert 'abcd1234' in cat.api.languoid_details
    assert 'Bookkeeping' in cat.api.glottocode_by_name
    assert 'abc' in cat.api.glottocode_by_iso
    assert 'abcd1234' in cat.api.macroareas_by_glottocode


def testConcepticon(concepticon_dir):
    cat = Concepticon(concepticon_dir)
    _ = cat.api.cached_glosses
