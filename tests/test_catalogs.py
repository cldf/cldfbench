import pytest

from cldfbench.catalogs import *


@pytest.fixture
def catalog(repository, fixtures_dir):
    return Catalog(fixtures_dir, 'tag')


def test_init_noapi():
    class Cat(Catalog):
        __api__ = 'nope'

    with pytest.raises(ValueError):
        _ = Cat('')


def test_init_api(mocker):
    api = mocker.Mock

    class Cat(Catalog):
        __api__ = api

    _ = Cat('').api
    assert api.called


def test_init_norepos(fixtures_dir):
    with pytest.raises(ValueError):
        _ = Catalog(fixtures_dir)


def test_context_manager(catalog):
    with catalog as cat:
        assert cat.describe()
        assert len(cat.tags) == 2
        assert cat.dir
        cat._prev_branch = 'master'
