import shlex
import shutil
import pathlib
import logging
import argparse

import pytest
from clldutils.jsonlib import load

from cldfbench import __main__ as cli
from cldfbench import ENTRY_POINT
from cldfbench.commands.media import MEDIA, ZENODO_FILE_NAME, INDEX_CSV
from cldfbench.cli_util import get_cldf_dataset


@pytest.fixture
def tmpds(fixtures_dir, tmp_path):
    for p in fixtures_dir.iterdir():
        if p.is_file():
            shutil.copy(p, tmp_path / p.name)
    return tmp_path / 'module.py'


@pytest.fixture
def tmpds_media(fixtures_dir, tmp_path):
    for p in fixtures_dir.iterdir():
        if p.is_file():
            shutil.copy(p, tmp_path / p.name)
    return tmp_path / 'module_media.py'


def _main(cmd, **kw):
    return cli.main(shlex.split('--no-config ' + cmd), **kw)


def test_get_cldf_dataset(tmp_path, tmpds, glottolog_dir):
    vals = tmp_path.joinpath('values.csv')
    vals.write_text('ID,Language_ID,Parameter_ID,Value\n1,1,1,1', encoding='utf8')
    ds = get_cldf_dataset(argparse.Namespace(glob=None, entry_point=ENTRY_POINT, dataset=str(vals)))
    assert len(list(ds['ValueTable'])) == 1
    assert ds.module == 'StructureDataset'

    _main('makecldf ' + str(tmpds) + ' --glottolog ' + str(glottolog_dir))
    ds = get_cldf_dataset(argparse.Namespace(
        glob=None,
        entry_point=ENTRY_POINT,
        dataset=tmp_path / 'cldf' / 'StructureDataset-metadata.json'))
    assert ds.module == 'StructureDataset'


def test_cldfreadme(tmp_path, tmpds, glottolog_dir):
    _main('makecldf ' + str(tmpds) + ' --with-zenodo --with-cldfreadme --glottolog ' +
          str(glottolog_dir))
    _main('cldfreadme ' + str(tmpds))
    assert '# CLDF datasets' in tmp_path.joinpath('cldf', 'README.md').read_text(encoding='utf8')


def test_help(capsys):
    _main('')
    out, _ = capsys.readouterr()
    assert 'usage' in out


def test_misc(tmp_path, mocker, glottolog_dir):
    with pytest.raises(SystemExit):
        _main('new --template=xyz')
    mocker.patch('cldfbench.metadata.input', mocker.Mock(return_value='abc'))
    _main('new --out=' + str(tmp_path))
    dsdir = tmp_path / 'abc'
    assert dsdir.is_dir()
    assert dsdir.joinpath('.gitignore').exists()
    mod = dsdir / 'cldfbench_abc.py'
    assert mod.exists()
    _main('makecldf ' + str(mod) + ' --glottolog ' + str(glottolog_dir))


def test_with_dataset_error(fixtures_dir, capsys):
    with pytest.raises(SystemExit):
        _main('info')

    with pytest.raises(SystemExit):
        _main('info abc')

    with pytest.raises(SystemExit):
        _main('run ' + str(fixtures_dir / 'module.py') + ' xyz')


def test_info(capsys, fixtures_dir):
    _main('info ' + str(fixtures_dir / 'module.py'))
    out, _ = capsys.readouterr()
    assert 'Thing' in out

    _main('info ' + str(fixtures_dir / 'module.py') + ' --cldf')
    out, _ = capsys.readouterr()
    assert 'StructureDataset-metadata.json' in out


def test_run(caplog, tmpds):
    with pytest.raises(ValueError):
        _main('run ' + str(tmpds) + ' raise')


def test_readme(tmpds, tmp_path, glottolog_dir, mocker):
    _main('readme ' + str(tmpds))
    _main('makecldf ' + str(tmpds) + ' --glottolog ' + str(glottolog_dir))
    mocker.patch('cldfbench.dataset.build_status_badge', mocker.Mock(return_value='abc'))
    _main('readme ' + str(tmpds))
    assert tmp_path.joinpath('README.md').exists()
    assert 'abc' in tmp_path.joinpath('README.md').read_text(encoding='utf8')


def test_ci(tmpds, tmp_path, capsys):
    _main('ci --test ' + str(tmpds))
    assert tmp_path.joinpath('.github').exists()


def test_zenodo(tmpds, tmp_path):
    _main('zenodo --communities clld ' + str(tmpds))
    res = load(tmp_path / '.zenodo.json')
    assert all(k in res for k in 'description creators contributors communities'.split())


def test_ls(capsys, tmpds):
    with pytest.raises(SystemExit):
        _main('ls _ --entry-point abc')

    _main('ls ' + str(tmpds))
    out, _ = capsys.readouterr()
    assert 'id ' in out

    _main('ls ' + str(tmpds) + ' --modules')
    out, _ = capsys.readouterr()
    assert 'id ' not in out


def test_download(tmpds):
    _main('download {}'.format(tmpds))
    with pytest.raises(SystemExit):
        _main('download abc')


def test_catinfo(capsys, glottolog_dir):
    _main('catinfo --glottolog {0}'.format(glottolog_dir))
    out, _ = capsys.readouterr()
    assert 'versions' in out


def test_catupdate(glottolog_dir):
    _main('catupdate --glottolog {0}'.format(glottolog_dir))


def test_invalid_catalog(fixtures_dir, tmpds):
    with pytest.raises(SystemExit):
        _main('makecldf ' + str(tmpds) + ' --glottolog ' + str(fixtures_dir))


def test_catalog_from_config(glottolog_dir, tmpds, mocker, tmp_path, fixtures_dir):
    from cldfcatalog import Config

    # First case: get a "good" value from comfig:
    mocker.patch(
        'cldfcatalog.config.appdirs',
        mocker.Mock(user_config_dir=mocker.Mock(return_value=str(tmp_path))))
    mocker.patch('cldfbench.commands.catconfig.confirm', mocker.Mock(return_value=False))
    cli.main(['catconfig', '--glottolog', str(glottolog_dir)])
    cli.main(['catinfo'])

    # Second case: get an invalid path from config:
    with Config.from_file() as cfg:
        cfg.add_clone('glottolog', fixtures_dir)
    with pytest.raises(SystemExit):
        cli.main(['makecldf', str(tmpds)])


def test_workflow(tmpds, glottolog_dir):
    _main('makecldf ' + str(tmpds) + ' --glottolog ' + str(glottolog_dir))
    assert _main('check ' + str(tmpds) + ' --with-validation', log=logging.getLogger(__name__)) == 1
    _main('geojson ' + str(tmpds))


def test_diff(tmpds, mocker, caplog, glottolog_dir, csvw3):
    class Item:
        def __init__(self, p):
            self.a_path = 'cldf/' + p

    class git:
        def Repo(self, *args):
            return mocker.Mock(
                git=mocker.Mock(
                    show=lambda _: '{"dc:title": "x"}',
                    status=lambda _: 'abc'
                ),
                index=mocker.Mock(
                    diff=lambda _: [
                        Item('.gitattributes'), Item('StructureDataset-metadata.json')]))
    mocker.patch('cldfbench.commands.diff.git', git())
    _main('makecldf ' + str(tmpds) + ' --glottolog ' + str(glottolog_dir))
    assert _main('diff ' + str(tmpds), log=logging.getLogger(__name__)) == 2
    assert len(caplog.records) == 10 if csvw3 else 11


def test_check(tmpds, tmp_path):
    tmp_path.joinpath('metadata.json').write_text("""{
      "title": "",
      "citation": "Author Year",
      "description": "Some text - possibly markdown",
      "url":  "http://example.org",
      "license": "CC-BY-4.0"
    }
    """, encoding='utf8')
    # Required metadata is missing:
    assert _main('check ' + str(tmpds), log=logging.getLogger(__name__)) == 2

    tmp_path.joinpath('metadata.json').write_text("""{
  "title": "stuff",
  "citation": "cit",
  "description": "",
  "url":  "http://example.org",
  "license": "CC-BY-4.0"
}
""", encoding='utf8')
    # Optional metadata is missing:
    assert _main('check ' + str(tmpds), log=logging.getLogger(__name__)) == 0


def test_media(tmpds_media, tmp_path, glottolog_dir, capsys, mocker):
    releasedir = pathlib.Path('thing_{}'.format(MEDIA))
    zipfile_name = pathlib.Path('{}.zip'.format(MEDIA))
    wav_name = '12345.wav'

    def urlretrieve(*args):
        d = tmp_path / MEDIA
        # due to threading
        d.mkdir(exist_ok=True)
        (d / wav_name[:2]).mkdir(exist_ok=True)
        shutil.copy(tmp_path / 'test.zip', d / wav_name[:2] / wav_name)

    mocker.patch('cldfbench.commands.media.urlretrieve', urlretrieve)

    _main('makecldf ' + str(tmpds_media) + ' --glottolog ' + str(glottolog_dir))

    _main('media -l ' + str(tmpds_media))
    capturedout = capsys.readouterr().out
    assert 'application/pdf' in capturedout and 'audio/x-wav' in capturedout

    _main('media -l -m wav ' + str(tmpds_media))
    capturedout = capsys.readouterr().out
    assert 'application/pdf' not in capturedout

    with pytest.raises(SystemExit):
        _main('media -m wav --create-release -p 10.5072/zenodo.710757 ' + str(tmpds_media))
    with pytest.raises(SystemExit):
        _main('media --create-release --update-zendo ' + str(tmpds_media))
    with pytest.raises(SystemExit):
        _main('media --create-release ' + str(tmpds_media))

    _main('media -o ' + str(tmp_path) + ' -m wav --create-release -p 10.5281/zenodo.4350882 ' + str(tmpds_media))
    assert (tmp_path / MEDIA / INDEX_CSV).exists()
    assert (tmp_path / MEDIA / wav_name[:2] / wav_name).exists()
    assert (tmp_path / releasedir / zipfile_name).exists()
    assert (tmp_path / releasedir / 'README.md').exists()
    assert (tmp_path / releasedir / ZENODO_FILE_NAME).exists()
