import os
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
    cli.main(shlex.split(cmd), **kw)


def test_help(capsys):
    _main('')
    out, _ = capsys.readouterr()
    assert 'usage' in out


def test_new(tmpdir, mocker, glottolog_dir):
    with pytest.raises(SystemExit):
        _main('new --template=xyz')
    mocker.patch('cldfbench.metadata.input', mocker.Mock(return_value='abc'))
    _main('new --out=' + str(tmpdir))
    dsdir = pathlib.Path(str(tmpdir)).joinpath('abc')
    assert dsdir.is_dir()
    _main('makecldf ' + str(dsdir / 'cldfbench_abc.py') + ' ' + str(glottolog_dir))


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


def test_makecldf(fixtures_dir, tmpds):
    with pytest.raises(SystemExit):
        _main('makecldf ' + tmpds + ' ' + str(fixtures_dir))


def test_check(tmpds, glottolog_dir):
    _main('makecldf ' + tmpds + ' ' + str(glottolog_dir))
    _main('check ' + tmpds + ' ' + str(glottolog_dir))
