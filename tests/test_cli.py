import pathlib
import shutil
import shlex
import importlib

import pytest

from cldfbench import __main__ as cli
from cldfbench.cli_util import DatasetNotFoundException


@pytest.fixture
def tmpds(fixtures_dir, tmpdir):
    for p in fixtures_dir.iterdir():
        if p.is_file():
            shutil.copy(str(p), str(tmpdir.join(p.name)))
    return str(tmpdir.join('module.py'))


def _main(cmd):
    cli.main(shlex.split(cmd))


def test_help(capsys):
    _main('')
    out, _ = capsys.readouterr()
    assert 'usage' in out


def test_new(tmpdir, mocker):
    with pytest.raises(SystemExit):
        _main('new --template=xyz')
    mocker.patch('cldfbench.metadata.input', mocker.Mock(return_value='abc'))
    _main('new --out=' + str(tmpdir))
    assert pathlib.Path(str(tmpdir)).joinpath('abc').is_dir()


def test_with_dataset_error(fixtures_dir, capsys):
    with pytest.raises(SystemExit):
        _main('info')

    with pytest.raises(DatasetNotFoundException):
        _main('info abc')

    with pytest.raises(SystemExit):
        _main('run ' + str(fixtures_dir / 'module.py') + ' xyz')


def test_info(capsys, fixtures_dir):
    _main('info ' + str(fixtures_dir / 'module.py'))
    out, _ = capsys.readouterr()
    assert 'Thing' in out


def test_run(caplog, tmpds):
    _main('run ' + tmpds + ' download')


def test_download(tmpds):
    _main('download ' + tmpds)


def test_makecldf(fixtures_dir, tmpds):
    with pytest.raises(SystemExit):
        _main('makecldf ' + tmpds + ' ' + str(fixtures_dir))
