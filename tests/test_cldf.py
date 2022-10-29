import pytest

from pycldf import Wordlist, Dataset

from cldfbench.cldf import *


def test_cldf_spec_invalid():
    with pytest.raises(TypeError):
        _ = CLDFSpec()

    with pytest.raises(ValueError):
        _ = CLDFSpec(dir='.', module='invalid')


def test_cldf_spec(tmp_path):
    md = tmp_path / 'md.json'
    md.write_text('abc', encoding='utf8')
    with pytest.raises(ValueError):
        _ = CLDFSpec(module=Wordlist, default_metadata_path=md, dir=tmp_path)
    md.write_text('{}', encoding='utf8')
    spec = CLDFSpec(module=Wordlist, default_metadata_path=md, dir=tmp_path)
    assert issubclass(spec.cls, Dataset)


def test_cldf(tmp_path):
    from cldfbench.cldf import WITH_ZIPPED

    with pytest.raises(AttributeError):
        _ = CLDFWriter().cldf

    with CLDFWriter(CLDFSpec(dir=tmp_path)):
        pass
    # The metadata was copied:
    assert tmp_path.glob('*-metadata.json')

    with CLDFWriter(CLDFSpec(
        module='StructureDataset',
        dir=tmp_path,
        data_fnames=dict(ValueTable='data.csv', ExampleTable='igt.csv'),
        zipped=['ValueTable'],
    )) as writer:
        assert writer.cldf['ValueTable'] and writer.cldf['ExampleTable']
        writer['ValueTable', 'value'].separator = '|'
        writer.objects['ValueTable'].append(
            dict(ID=1, Language_ID='l', Parameter_ID='p', Value=[1, 2]))
    assert (not WITH_ZIPPED) or tmp_path.joinpath('data.csv.zip').exists()
    ds = Dataset.from_metadata(tmp_path / 'StructureDataset-metadata.json')
    values = list(ds['ValueTable'])
    assert len(values) == 1
    assert values[0]['Value'] == ['1', '2']

    with pytest.raises(AttributeError):
        CLDFWriter(tmp_path).validate()


def test_cldf_with_dataset(ds):
    with CLDFWriter(CLDFSpec(dir=ds.cldf_dir), dataset=ds):
        pass
    cldf = Dataset.from_metadata(ds.cldf_dir.joinpath('Generic-metadata.json'))
    assert 'http://example.org/raw' in [
        p['rdf:about'] for p in cldf.properties['prov:wasDerivedFrom']]
