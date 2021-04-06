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
        md.append("# CLDF datasets\n")
        md.extend([
            '- [{}](#ds-{})'.format(cldf.module, slug(cldf.metadata_fname)) for cldf in cldfs])
        md.append('')
    for cldf in cldfs:
        if cldf.metadata_path.exists():
            md.append('<a name="ds-{}"> </a>\n'.format(slug(cldf.metadata_fname)))
            res = metadata2markdown(cldf.get_dataset(), cldf.metadata_path)
            md.append(res.replace('# ', '# {} '.format(cldf.module), 1))
            md.append('\n')

    ds.cldf_dir.joinpath('README.md').write_text('\n'.join(md), encoding='utf8')
