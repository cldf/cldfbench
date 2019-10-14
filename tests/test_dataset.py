import pathlib
import argparse
import shutil

import pytest

from cldfbench.dataset import *
from cldfbench.catalogs import Catalog


@pytest.fixture()
def ds_cls(tmpdir):
    class Thing(Dataset):
        id = 'this'
        dir = pathlib.Path(str(tmpdir))
    return Thing


@pytest.fixture()
def ds(ds_cls, fixtures_dir, tmpdir):
    raw = pathlib.Path(str(tmpdir)) / 'raw'
    raw.mkdir()
    for p in fixtures_dir.glob('test.*'):
        shutil.copy(str(p), str(raw / p.name))
    shutil.copy(str(fixtures_dir / 'metadata.json'), str(tmpdir.join('metadata.json')))
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


def test_cldf(ds, repository):
    with ds.cldf_writer(argparse.Namespace(cat=Catalog(repository.dir))) as writer:
        writer.cldf.add_component('ValueTable')
        writer['ValueTable', 'value'].separator = '|'
        writer.objects['ValueTable'].append(
            dict(ID=1, Language_ID='l', Parameter_ID='p', Value=[1, 2]))
    assert ds.cldf_dir.joinpath('Generic-metadata.json').exists()
    assert ds.cldf_dir.read_csv('values.csv', dicts=True)[0]['Value'] == '1|2'
    assert ds.cldf_reader().validate()
    ds.cmd_makecldf(None)
