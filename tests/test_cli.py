import shlex
import shutil
import pathlib
import logging

import pytest
from clldutils.jsonlib import load

from cldfbench import __main__ as cli


@pytest.fixture
def tmpds(fixtures_dir, tmpdir):
    for p in fixtures_dir.iterdir():
        if p.is_file():
            shutil.copy(str(p), str(tmpdir.join(p.name)))
    return str(tmpdir.join('module.py'))


def _main(cmd, **kw):
    return cli.main(shlex.split('--no-config ' + cmd), **kw)


def test_help(capsys):
    _main('')
    out, _ = capsys.readouterr()
    assert 'usage' in out


def test_misc(tmpdir, mocker, glottolog_dir):
    with pytest.raises(SystemExit):
        _main('new --template=xyz')
    mocker.patch('cldfbench.metadata.input', mocker.Mock(return_value='abc'))
    _main('new --out=' + str(tmpdir))
    dsdir = pathlib.Path(str(tmpdir)).joinpath('abc')
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
        _main('run ' + tmpds + ' raise')


def test_readme(tmpds, tmpdir):
    _main('readme ' + tmpds)
    assert pathlib.Path(str(tmpdir)).joinpath('README.md').exists()


def test_ci(tmpds, tmpdir, capsys):
    _main('ci --test ' + tmpds)
    assert pathlib.Path(str(tmpdir)).joinpath('.github').exists()


def test_zenodo(tmpds, tmpdir):
    _main('zenodo --communities clld ' + tmpds)
    res = load(pathlib.Path(str(tmpdir)).joinpath('.zenodo.json'))
    assert all(k in res for k in 'description creators contributors communities'.split())


def test_ls(capsys, tmpds):
    with pytest.raises(SystemExit):
        _main('ls _ --entry-point abc')

    _main('ls ' + tmpds)
    out, _ = capsys.readouterr()
    assert 'id ' in out

    _main('ls ' + tmpds + ' --modules')
    out, _ = capsys.readouterr()
    assert 'id ' not in out


def test_download(tmpds):
    _main('download ' + tmpds)
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
        _main('makecldf ' + tmpds + ' --glottolog ' + str(fixtures_dir))


def test_catalog_from_config(glottolog_dir, tmpds, mocker, tmpdir, fixtures_dir):
    from cldfcatalog import Config

    # First case: get a "good" value from comfig:
    mocker.patch(
        'cldfcatalog.config.appdirs',
        mocker.Mock(user_config_dir=mocker.Mock(return_value=str(tmpdir))))
    mocker.patch('cldfbench.commands.catconfig.confirm', mocker.Mock(return_value=False))
    cli.main(['catconfig', '--glottolog', str(glottolog_dir)])
    cli.main(['catinfo'])

    # Second case: get an invalid path from config:
    with Config.from_file() as cfg:
        cfg.add_clone('glottolog', fixtures_dir)
    with pytest.raises(SystemExit):
        cli.main(['makecldf', tmpds])


def test_workflow(tmpds, glottolog_dir):
    _main('makecldf ' + tmpds + ' --glottolog ' + str(glottolog_dir))
    assert _main('check ' + tmpds + ' --with-validation', log=logging.getLogger(__name__)) == 1
    _main('geojson ' + tmpds)


def test_diff(tmpds, tmpdir, mocker, caplog, glottolog_dir):
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
    _main('makecldf ' + tmpds + ' --glottolog ' + str(glottolog_dir))
    assert _main('diff ' + tmpds, log=logging.getLogger(__name__)) == 2
    assert len(caplog.records) == 11


def test_check(tmpds, tmpdir):
    tmpdir.join('metadata.json').write_text("""{
      "title": "",
      "citation": "Author Year",
      "description": "Some text - possibly markdown",
      "url":  "http://example.org",
      "license": "CC-BY-4.0"
    }
    """, encoding='utf8')
    # Required metadata is missing:
    assert _main('check ' + tmpds, log=logging.getLogger(__name__)) == 2

    tmpdir.join('metadata.json').write_text("""{
  "title": "stuff",
  "citation": "cit",
  "description": "",
  "url":  "http://example.org",
  "license": "CC-BY-4.0"
}
""", encoding='utf8')
    # Optional metadata is missing:
    assert _main('check ' + tmpds, log=logging.getLogger(__name__)) == 0
