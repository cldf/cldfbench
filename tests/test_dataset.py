import pathlib
import argparse
import shutil

import pytest
from cldfcatalog.repository import get_test_repo

from cldfbench.dataset import *


@pytest.fixture()
def ds_cls(tmpdir):
    class Thing(Dataset):
        id = 'this'
        dir = pathlib.Path(
            get_test_repo(str(tmpdir), remote_url='https://github.com/org/repo.git').working_dir)
    return Thing


@pytest.fixture()
def ds(ds_cls, fixtures_dir):
    raw = ds_cls.dir / 'raw'
    raw.mkdir()
    for p in fixtures_dir.glob('test.*'):
        shutil.copy(str(p), str(raw / p.name))
    shutil.copy(str(fixtures_dir / 'metadata.json'), str(ds_cls.dir.joinpath('metadata.json')))
    res = ds_cls()
    return res


def test_get_dataset_from_path():
    ds = get_dataset(pathlib.Path(__file__).parent / 'fixtures' / 'module.py')
    assert ds.id == 'thing'
    assert not ds.cldf_dir.exists()
    assert not ds.etc_dir.exists()


def test_get_dataset_from_id(mocker, ds_cls):
    mocker.patch(
        'cldfbench.dataset.pkg_resources',
        mocker.Mock(iter_entry_points=mocker.Mock(
            return_value=[mocker.Mock(load=mocker.Mock(return_value=ds_cls))])))
    assert isinstance(get_dataset('this'), ds_cls)


def test_cldf(ds, mocker):
    class Catalog:
        def json_ld(self):
            return {}

    mocker.patch('cldfbench.cldf.Catalog', Catalog)

    with ds.cldf_writer(argparse.Namespace(cat=Catalog())) as writer:
        writer.cldf.add_component('ValueTable')
        writer['ValueTable', 'value'].separator = '|'
        writer.objects['ValueTable'].append(
            dict(ID=1, Language_ID='l', Parameter_ID='p', Value=[1, 2]))
    assert ds.cldf_dir.joinpath('Generic-metadata.json').exists()
    assert ds.cldf_dir.read_csv('values.csv', dicts=True)[0]['Value'] == '1|2'
    assert ds.cldf_reader().validate()
    ds.cmd_makecldf(None)
