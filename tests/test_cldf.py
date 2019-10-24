import pathlib

import pytest

from pycldf import Wordlist, Dataset

from cldfbench.cldf import *


def test_cldf_spec_invalid():
    with pytest.raises(TypeError):
        _ = CLDFSpec()

    with pytest.raises(ValueError):
        _ = CLDFSpec(dir='.', module='invalid')


def test_cldf_spec(tmpdir):
    md = pathlib.Path(str(tmpdir)) / 'md.json'
    md.write_text('abc', encoding='utf8')
    with pytest.raises(ValueError):
        _ = CLDFSpec(module=Wordlist, default_metadata_path=md, dir=str(tmpdir))
    md.write_text('{}', encoding='utf8')
    spec = CLDFSpec(module=Wordlist, default_metadata_path=md, dir=str(tmpdir))
    assert issubclass(spec.cls, Dataset)


def test_cldf(tmpdir):
    with pytest.raises(AttributeError):
        _ = CLDFWriter().cldf

    outdir = pathlib.Path(str(tmpdir))
    with CLDFWriter(CLDFSpec(dir=outdir)):
        pass
    # The metadata was copied:
    assert outdir.glob('*-metadata.json')

    with CLDFWriter(CLDFSpec(dir=outdir, data_fnames=dict(ValueTable='data.csv'))) as writer:
        assert writer.cldf['ValueTable']
        writer['ValueTable', 'value'].separator = '|'
        writer.objects['ValueTable'].append(
            dict(ID=1, Language_ID='l', Parameter_ID='p', Value=[1, 2]))
    ds = Dataset.from_metadata(outdir / 'Generic-metadata.json')
    values = list(ds['ValueTable'])
    assert len(values) == 1
    assert values[0]['Value'] == ['1', '2']

    with pytest.raises(AttributeError):
        CLDFWriter(outdir).validate()
