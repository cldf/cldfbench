import pathlib
import shutil

import pytest

from cldfbench.dataset import get_dataset, Dataset, get_url


@pytest.fixture()
def ds_cls(tmpdir):
    class Thing(Dataset):
        id = 'this'
        dir = pathlib.Path(str(tmpdir))
    return Thing


@pytest.fixture()
def ds(ds_cls, fixtures_dir, tmpdir):
    res = ds_cls()
    res.raw_dir.mkdir()
    for p in fixtures_dir.glob('test.*'):
        shutil.copy(str(p), str(tmpdir.join('raw', p.name)))
    return res


def test_get_dataset_from_path():
    assert get_dataset(pathlib.Path(__file__).parent / 'fixtures' / 'module.py').id == 'thing'


def test_get_dataset_from_id(mocker, ds_cls):
    mocker.patch(
        'cldfbench.dataset.pkg_resources',
        mocker.Mock(iter_entry_points=mocker.Mock(
            return_value=[mocker.Mock(load=mocker.Mock(return_value=ds_cls))])))
    assert isinstance(get_dataset('this'), ds_cls)


def test_get_url(mocker):
    mocker.patch('cldfbench.dataset.requests', mocker.Mock(get=mocker.Mock()))
    get_url(None, log=mocker.Mock(warn=mocker.Mock()))


def test_datadir(ds):
    ds.raw_dir.write('fname', 'stuff')
    assert ds.raw_dir.read('fname') == 'stuff'
    ds.raw_dir.write('sources.bib', '@article{id,\ntitle={the title}\n}')
    assert len(ds.raw_dir.read_bib()) == 1


def test_datadir_xml(ds):
    assert ds.raw_dir.read_xml('test.xml').find('b').text == 'b'


def test_datadir_excel(ds):
    res = ds.raw_dir.xls2csv(ds.raw_dir / 'test.xls')
    assert res['Sheet2'].stem == 'test.Sheet2'

    ds.raw_dir.xlsx2csv(ds.raw_dir / 'test.xlsx')
    data = ds.raw_dir.read_csv('test.Sheet2.csv')
    assert data[1] == ['1']


def test_datadir_download_and_unpack(ds, mocker):
    mocker.patch(
        'cldfbench.dataset.get_url',
        mocker.Mock(
            return_value=mocker.Mock(
                iter_content=mocker.Mock(
                    return_value=[ds.raw_dir.joinpath('test.zip').open('rb').read()]))))
    ds.raw_dir.download_and_unpack(None)
    assert ds.raw_dir.joinpath('setup.py').exists()
