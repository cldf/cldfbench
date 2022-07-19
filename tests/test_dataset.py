import pathlib
import argparse

from cldfbench.dataset import *


def test_get_dataset_from_path(fixtures_dir):
    ds = get_dataset(fixtures_dir / 'module.py')
    assert ds.id == 'thing'
    assert not ds.cldf_dir.exists()
    assert not ds.etc_dir.exists()
    assert get_datasets(str(fixtures_dir.relative_to(pathlib.Path.cwd()) / '*.py'), glob=True)


def test_get_dataset_from_id(mocker, ds_cls):
    mocker.patch(
        'cldfbench.dataset.get_entrypoints',
        mocker.Mock(return_value=[mocker.Mock(load=mocker.Mock(return_value=ds_cls))]))
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
    ds.cmd_makecldf(mocker.Mock())


def test_dataset_update_submodules(mocker, tmp_path):
    mocker.patch('cldfbench.dataset.subprocess', mocker.Mock())

    class DS(Dataset):
        id = 'x'
        dir = tmp_path
        def cmd_download(self, args: argparse.Namespace):
            self.update_submodules()

    DS().cmd_download(mocker.Mock())


def test_dataset_with_custom_datadir(tmp_path):
    from cldfbench.datadir import DataDir

    class DD(DataDir):
        def hello(self):
            return 'hello'

    class DS(Dataset):
        id = 'x'
        dir = tmp_path
        datadir_cls = DD

    assert DS().raw_dir.hello() == 'hello'
