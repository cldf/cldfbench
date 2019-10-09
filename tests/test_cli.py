import pathlib
import shlex

import pytest

from cldfbench import __main__ as cli
from cldfbench.cli_util import DatasetNotFoundException


def _main(cmd):
    cli.main(shlex.split(cmd))


def test_new(tmpdir, mocker):
    with pytest.raises(SystemExit):
        _main('new --template=xyz')
    mocker.patch('cldfbench.scaffold.input', mocker.Mock(return_value='abc'))
    _main('new --out=' + str(tmpdir))
    assert pathlib.Path(str(tmpdir)).joinpath('abc').is_dir()


def test_with_dataset_error(fixtures_dir, capsys):
    with pytest.raises(SystemExit):
        _main('info')

    with pytest.raises(DatasetNotFoundException):
        _main('info abc')

    _main('run ' + str(fixtures_dir / 'module.py') + ' xyz')
    out, _ = capsys.readouterr()
    assert 'no xyz command' in out


def test_info(capsys, fixtures_dir):
    _main('info ' + str(fixtures_dir / 'module.py'))
    out, _ = capsys.readouterr()
    assert 'Thing' in out


def test_run(caplog, fixtures_dir):
    _main('run ' + str(fixtures_dir / 'module.py') + ' download')


def test_download(fixtures_dir):
    _main('download ' + str(fixtures_dir / 'module.py'))


def test_makecldf(fixtures_dir):
    _main('makecldf ' + str(fixtures_dir / 'module.py'))
