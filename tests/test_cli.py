import logging
import pathlib
import shutil
import shlex

import pytest

from cldfbench import __main__ as cli


@pytest.fixture
def tmpds(fixtures_dir, tmpdir):
    for p in fixtures_dir.iterdir():
        if p.is_file():
            shutil.copy(str(p), str(tmpdir.join(p.name)))
    return str(tmpdir.join('module.py'))


def _main(cmd, **kw):
    cli.main(shlex.split('--no-config ' + cmd), **kw)


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


def test_run(caplog, tmpds):
    with pytest.raises(ValueError):
        _main('run ' + tmpds + ' raise')


def test_readme(tmpds, tmpdir):
    _main('readme ' + tmpds)
    assert pathlib.Path(str(tmpdir)).joinpath('README.md').exists()


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
    from cldfbench.cli_util import Config

    # First case: get a "good" value from comfig:
    mocker.patch(
        'cldfbench.cli_util.appdirs',
        mocker.Mock(user_config_dir=mocker.Mock(return_value=str(tmpdir))))
    mocker.patch(
        'cldfbench.commands.config.input',
        mocker.Mock(return_value=str(glottolog_dir)))
    cli.main(['config'])
    cli.main(['catinfo'])
    cli.main(['makecldf', tmpds])

    # Second case: get an invalid path from config:
    cfg = Config.from_file()
    cfg['catalogs']['glottolog'] = str(fixtures_dir)
    cfg.to_file()
    with pytest.raises(SystemExit):
        cli.main(['makecldf', tmpds])


def test_workflow(tmpds, glottolog_dir):
    _main('makecldf ' + tmpds + ' --glottolog ' + str(glottolog_dir))
    _main('check ' + tmpds + ' --glottolog ' + str(glottolog_dir))
    _main('geojson ' + tmpds)
