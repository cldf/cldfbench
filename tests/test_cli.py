import pytest

from cldfbench import __main__ as cli


def test_help(capsys):
    with pytest.raises(SystemExit):
        cli.main(['-h'])
    out, _ = capsys.readouterr()
    assert 'cldfbench' in out
