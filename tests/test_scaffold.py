import pathlib

import attr

from cldfbench.scaffold import Template, Metadata


def test_custom_template(tmpdir, mocker):
    @attr.s
    class CustomMetadata(Metadata):
        id = attr.ib(default='abc')
        custom_var = attr.ib(default='xyz')

    class Custom(Template):
        package = 'pylexibank'
        prefix = 'lexibank'
        metadata = CustomMetadata

    d = pathlib.Path(str(tmpdir))
    mocker.patch('cldfbench.scaffold.input', mocker.Mock(return_value=''))
    md = Custom.metadata.elicit()
    Custom().render(d, md)
    assert d.joinpath('abc').exists()
    assert d.joinpath('abc', 'lexibank_abc.py').exists()
    assert 'from pylexibank' in d.joinpath('abc', 'lexibank_abc.py').read_text(encoding='utf-8')

    test_file = (d / 'abc' / 'raw' / 'test')
    test_file.write_text('abc', encoding='utf-8')
    # Re-running will recreate sub-directories:
    Custom().render(d, md)
    assert not test_file.exists()
