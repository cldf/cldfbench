import pytest
from git.exc import NoSuchPathError

from cldfbench.catalogs import *


@pytest.fixture
def catalog(mocker, fixtures_dir):
    class Repo:
        git = mocker.Mock(
            tag=mocker.Mock(return_value='v1\nv2'),
            describe=mocker.Mock(return_value='v1'),
        )
        active_branch = mocker.PropertyMock(side_effect=TypeError)

        def __init__(self, p):
            self.p = p

        @property
        def working_dir(self):
            return self.p

    mocker.patch('cldfbench.catalogs.Repo', Repo)
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


def test_init_norepos(mocker, fixtures_dir):
    mocker.patch('cldfbench.catalogs.Repo', mocker.Mock(side_effect=NoSuchPathError))
    with pytest.raises(ValueError):
        _ = Catalog(fixtures_dir)


def test_context_manager(catalog):
    with catalog as cat:
        assert cat.describe()
        assert len(cat.tags) == 2
        assert cat.dir
        cat._prev_branch = 'master'
