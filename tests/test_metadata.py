from cldfbench.metadata import *


def test_Metadata_read_write(tmp_path):
    fname = tmp_path / 'md.json'
    md = Metadata()
    md.write(fname)
    assert Metadata.from_file(fname) == md


def test_md(mocker):
    mocker.patch('cldfbench.metadata.input', mocker.Mock(return_value='x'))
    md = Metadata.elicit()
    md.license = 'CC-BY-4.0'
    md.description = 'x'
    assert md.common_props()['dc:title'] == 'x'
    assert 'creativecommons' in md.common_props()['dc:license']
    md.license = 'some license'
    assert md.common_props()['dc:license'] == 'some license'


def test_get_creators_and_contributors():
    thead = 'n|role\n---|---\n'
    text, creators, contributors = 'x|author\ny|other', [{'n': 'x'}], [{'n': 'y', 'type': 'Other'}]
    res = get_creators_and_contributors(thead + text)
    assert creators, contributors == res

    res = get_creators_and_contributors(thead + text.replace('other', 'unknown'), strict=False)
    assert creators, contributors == res
