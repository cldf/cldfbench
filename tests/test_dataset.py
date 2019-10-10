import pathlib
import shutil

import pytest

from cldfbench.dataset import get_dataset, get_url, Dataset


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


def test_get_url(mocker):
    mocker.patch('cldfbench.dataset.requests', mocker.Mock(get=mocker.Mock()))
    get_url(None, log=mocker.Mock(warn=mocker.Mock()))


def test_datadir(ds):
    ds.raw_dir.write('fname', '{"a": 2}')
    assert ds.raw_dir.read('fname')
    assert ds.raw_dir.read_json('fname')['a'] == 2
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
    ds.raw_dir.download(None, 'fname')
    ds.raw_dir.download(None, 'fname', skip_if_exists=True)


def test_cldf(ds):
    with ds.cldf_writer() as writer:
        writer.cldf.add_component('ValueTable')
        writer['ValueTable', 'value'].separator = '|'
        writer.objects['ValueTable'].append(
            dict(ID=1, Language_ID='l', Parameter_ID='p', Value=[1, 2]))
    assert ds.cldf_dir.joinpath('Generic-metadata.json').exists()
    assert ds.cldf_dir.read_csv('values.csv', dicts=True)[0]['Value'] == '1|2'
    assert ds.cldf_writer().validate()
    ds.cmd_makecldf()
