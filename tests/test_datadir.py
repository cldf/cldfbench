import sys
import shutil

import pytest

from cldfbench.datadir import *


@pytest.fixture
def datadir(tmp_path, fixtures_dir):
    for p in fixtures_dir.iterdir():
        if p.is_file():
            shutil.copy(p, tmp_path / p.name)
    return DataDir(tmp_path)


def test_get_url(mocker):
    mocker.patch('cldfbench.datadir.requests', mocker.Mock(get=mocker.Mock()))
    get_url(None, log=mocker.Mock(warn=mocker.Mock()))


def test_datadir(datadir):
    datadir.write('fname', '{"a": 2}')
    assert datadir.read('fname')
    assert datadir.read('fname', normalize='NFC')
    assert datadir.read_json('fname')['a'] == 2
    datadir.write('sources.bib', '@article{id,\ntitle={the title}\n}')
    assert len(datadir.read_bib()) == 1


def test_datadir_csv(datadir):
    rows = [['a', 'b'], ['c', 'd']]
    datadir.write_csv('test.csv', rows)
    assert datadir.read_csv('test.csv') == rows
    assert datadir.read_csv('test.csv', normalize='NFC') == rows
    assert datadir.read_csv(
            'test.csv', normalize='NFC', dicts=True)[0]['a'] =='c'



def test_datadir_xml(datadir):
    assert datadir.read_xml('test.xml').find('b').text == 'b'


def test_datadir_excel(datadir):
    res = datadir.xls2csv(datadir / 'test.xls')
    assert res['Sheet2'].stem == 'test.Sheet2'

    if sys.version_info >= (3, 6):
        with pytest.raises(ValueError):
            datadir.xls2csv(datadir / 'test.xlsx')

    datadir.xlsx2csv(datadir / 'test.xlsx')
    data = datadir.read_csv('test.Sheet2.csv')
    assert data[1] == ['1.01']
    assert data[2] == ['2']


def test_datadir_download_and_unpack(datadir, mocker):
    mocker.patch(
        'cldfbench.datadir.get_url',
        mocker.Mock(
            return_value=mocker.Mock(
                iter_content=mocker.Mock(
                    return_value=[datadir.joinpath('test.zip').open('rb').read()]))))
    datadir.download_and_unpack(None)
    assert datadir.joinpath('setup.py').exists()
    datadir.download(None, 'fname')
    datadir.download(None, 'fname', skip_if_exists=True)
