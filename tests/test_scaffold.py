import attr

from cldfbench.scaffold import Template, Metadata


def test_custom_template(tmp_path, mocker, fixtures_dir):
    @attr.s
    class CustomMetadata(Metadata):
        id = attr.ib(default='abc', metadata=dict(elicit=True))
        custom_var = attr.ib(default='xyz', metadata=dict(elicit=True))

    class Custom(Template):
        package = 'pylexibank'
        prefix = 'lexibank'
        metadata = CustomMetadata
        dirs = Template.dirs + [fixtures_dir]

    mocker.patch('cldfbench.metadata.input', mocker.Mock(return_value=''))
    md = Custom.metadata.elicit()
    Custom().render(tmp_path, md)
    assert tmp_path.joinpath('abc').exists()
    assert tmp_path.joinpath('abc', 'lexibank_abc.py').exists()
    assert 'from pylexibank' in tmp_path.joinpath('abc', 'lexibank_abc.py').read_text(encoding='utf-8')

    # Content from the second template directory was copied as well:
    assert tmp_path.joinpath('abc', 'module.py').exists()

    test_file = (tmp_path / 'abc' / 'raw' / 'test')
    test_file.write_text('abc', encoding='utf-8')
    # Re-running will recreate sub-directories:
    Custom().render(tmp_path, md)
    assert not test_file.exists()
