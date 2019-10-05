import pathlib

import pytest
from clldutils.clilib import ParserError

from cldfbench import __main__ as cli


def test_help(capsys):
    with pytest.raises(SystemExit):
        cli.main(['-h'])
    out, _ = capsys.readouterr()
    assert 'cldfbench' in out


def test_list(capsys, mocker):
    cli.list_(mocker.Mock(args=[]))
    out, _ = capsys.readouterr()
    assert 'cldfbench' in out


def test_new(tmpdir, mocker):
    with pytest.raises(ParserError):
        cli.new(mocker.Mock(args=[]))
    with pytest.raises(ParserError):
        cli.new(mocker.Mock(args=['xyz', '.']))
    mocker.patch('cldfbench.scaffold.input', mocker.Mock(return_value='abc'))
    cli.new(mocker.Mock(args=['cldfbench', str(tmpdir)]))
    assert pathlib.Path(str(tmpdir)).joinpath('abc').is_dir()
