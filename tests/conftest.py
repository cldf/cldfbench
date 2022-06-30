import pathlib
import shutil

import pytest
import csvw
import packaging.version

from cldfcatalog.repository import get_test_repo
from cldfbench import Dataset


@pytest.fixture(scope='session')
def csvw3():
    return packaging.version.parse(csvw.__version__) > packaging.version.parse('2.0.0')


@pytest.fixture
def fixtures_dir():
    return pathlib.Path(__file__).parent / 'fixtures'


@pytest.fixture
def glottolog_dir(tmp_path):
    repo = get_test_repo(tmp_path, tags=['v1', 'v2'])
    d = pathlib.Path(repo.working_dir)
    for dd in ['languoids', 'references']:
        shutil.copytree(str(pathlib.Path(__file__).parent / 'glottolog' / dd), str(d / dd))
    return d


@pytest.fixture
def concepticon_dir(tmp_path):
    repo = get_test_repo(tmp_path)
    d = pathlib.Path(repo.working_dir)
    d.joinpath('concepticondata').mkdir()
    d.joinpath('concepticondata', 'concepticon.tsv').write_text('', encoding='utf8')
    return d


@pytest.fixture()
def ds_cls(tmp_path):
    class Thing(Dataset):
        id = 'this'
        dir = pathlib.Path(
            get_test_repo(tmp_path, remote_url='https://github.com/org/repo.git').working_dir)
    return Thing


@pytest.fixture()
def ds(ds_cls, fixtures_dir):
    raw = ds_cls.dir / 'raw'
    raw.mkdir()
    for p in fixtures_dir.glob('test.*'):
        shutil.copy(str(p), str(raw / p.name))
    get_test_repo(raw, remote_url='http://example.org/raw')
    raw.joinpath('non-repo').mkdir()
    shutil.copy(str(fixtures_dir / 'metadata.json'), str(ds_cls.dir.joinpath('metadata.json')))
    res = ds_cls()
    return res
