"""
Write markdown versions of the CLDF datasets to cldf/README.md
"""
from clldutils.misc import slug
from pycldf.util import metadata2markdown
from cldfbench.cli_util import add_dataset_spec, get_dataset


def register(parser):
    add_dataset_spec(parser)


def run(args):
    ds = get_dataset(args)
    md = []
    cldfs = list(ds.cldf_specs_dict.values())
    if len(cldfs) > 1:
        def label(spec):
            res = spec.module
            dataset = spec.get_dataset()
            if dataset.properties.get('dc:title'):
                res += ': {}'.format(dataset.properties['dc:title'])
            return res
        md.append("# CLDF datasets\n")
        md.extend([
            '- [{}](#ds-{})'.format(label(cldf), slug(cldf.metadata_fname)) for cldf in cldfs])
        md.append('')
    for cldf in cldfs:
        if cldf.metadata_path.exists():
            kw = {}
            if cldf.metadata_path.parent != ds.cldf_dir:  # pragma: no cover
                kw['rel_path'] = '{}/'.format(cldf.metadata_path.parent.relative_to(ds.cldf_dir))
            md.append('<a name="ds-{}"> </a>\n'.format(slug(cldf.metadata_fname)))
            res = metadata2markdown(cldf.get_dataset(), cldf.metadata_path, **kw)
            md.append(res.replace('# ', '# {} '.format(cldf.module), 1))
            md.append('\n')

    ds.cldf_dir.joinpath('README.md').write_text('\n'.join(md), encoding='utf8')
