import pathlib

from cldfbench.metadata import *


def test_Metadata_read_write(tmpdir):
    fname = pathlib.Path(str(tmpdir)) / 'md.json'
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
