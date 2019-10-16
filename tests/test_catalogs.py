from cldfbench.catalogs import *


def test_Glottolog(glottolog_dir):
    cat = Glottolog(glottolog_dir)
    assert cat.api.languoids(ids=['abcd1234'])
    l = cat.api.languoids()
    assert cat.api.languoids() is l
