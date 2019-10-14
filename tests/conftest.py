import pathlib

import pytest

from cldfbench.repository import Repository


@pytest.fixture()
def fixtures_dir():
    return pathlib.Path(__file__).parent / 'fixtures'


@pytest.fixture
def repository(mocker, fixtures_dir):
    """
    Turns `fixtures_dir` into a git repository.
    """
    class Repo:
        git = mocker.Mock(
            tag=mocker.Mock(return_value='v1\nv2'),
            describe=mocker.Mock(return_value='v1'),
        )
        active_branch = mocker.PropertyMock(side_effect=TypeError)
        remotes = mocker.Mock(origin=mocker.Mock(url='https://github.com/org/repo.git'))

        def __init__(self, p):
            self.p = p

        @property
        def working_dir(self):
            return self.p

    mocker.patch('cldfbench.repository.git', mocker.Mock(Repo=Repo))
    return Repository(fixtures_dir)
