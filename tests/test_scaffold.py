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
    Custom().render(d, Custom.metadata.elicit())
    assert d.joinpath('abc').exists()
    assert d.joinpath('abc', 'lexibank_abc.py').exists()
    assert 'from pylexibank' in d.joinpath('abc', 'lexibank_abc.py').read_text(encoding='utf-8')
