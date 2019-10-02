import pathlib

import pytest

from cldfbench.dataset import get_dataset, Dataset


@pytest.fixture()
def ds(tmpdir):
    class Thing(Dataset):
        id = 'this'
        dir = pathlib.Path(str(tmpdir))
    return Thing


def test_get_dataset_from_path():
    assert get_dataset(pathlib.Path(__file__).parent / 'fixtures' / 'module.py').id == 'thing'


def test_get_dataset_from_id(mocker, ds):
    mocker.patch(
        'cldfbench.dataset.pkg_resources',
        mocker.Mock(iter_entry_points=mocker.Mock(
            return_value=[mocker.Mock(load=mocker.Mock(return_value=ds))])))
    assert isinstance(get_dataset('this'), ds)


def test_datadir(ds):
    ds = ds()
    ds.raw_dir.mkdir()
    ds.raw_dir.write('fname', 'stuff')
    assert ds.raw_dir.read('fname') == 'stuff'
