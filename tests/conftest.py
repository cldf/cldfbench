import pathlib
import shutil

import pytest

from cldfcatalog.repository import get_test_repo


@pytest.fixture
def fixtures_dir():
    return pathlib.Path(__file__).parent / 'fixtures'


@pytest.fixture
def glottolog_dir(tmpdir):
    repo = get_test_repo(str(tmpdir), tags=['v1', 'v2'])
    d = pathlib.Path(repo.working_dir)
    for dd in ['languoids', 'references']:
        shutil.copytree(str(pathlib.Path(__file__).parent / 'glottolog' / dd), str(d / dd))
    return d


@pytest.fixture
def concepticon_dir(tmpdir):
    repo = get_test_repo(str(tmpdir))
    d = pathlib.Path(repo.working_dir)
    d.joinpath('concepticondata').mkdir()
    d.joinpath('concepticondata', 'concepticon.tsv').write_text('', encoding='utf8')
    return d
