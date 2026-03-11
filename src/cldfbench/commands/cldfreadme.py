"""
Write markdown versions of the CLDF datasets to cldf/README.md
"""
from clldutils.misc import slug
from pycldf.markdown import metadata2markdown
from cldfbench.cli_util import add_dataset_spec, get_dataset


def register(parser):  # pylint: disable=C0116
    add_dataset_spec(parser)


def run(args):  # pylint: disable=C0116
    ds = get_dataset(args)
    ds.cldf_dir.joinpath('README.md').write_text('\n'.join(_iter_markdown(ds)), encoding='utf8')


def _iter_markdown(ds):
    cldfs = list(ds.cldf_specs_dict.values())
    if len(cldfs) > 1:
        # We write a short table-of-contents.
        def label(spec):
            res = spec.module
            dataset = spec.get_dataset()
            if dataset.properties.get('dc:title'):
                res += f": {dataset.properties['dc:title']}"
            return res

        yield "# CLDF datasets\n"
        for cldf in cldfs:
            if cldf.metadata_path.exists():
                yield f'- [{label(cldf)}](#ds-{slug(cldf.metadata_fname)})'
        yield ''

    for cldf in cldfs:
        if cldf.metadata_path.exists():
            kw = {}
            if cldf.metadata_path.parent != ds.cldf_dir:  # pragma: no cover
                kw['rel_path'] = f'{cldf.metadata_path.parent.relative_to(ds.cldf_dir)}/'
            yield f'<a name="ds-{slug(cldf.metadata_fname)}"> </a>\n'
            res = metadata2markdown(cldf.get_dataset(), cldf.metadata_path, **kw)
            yield res.replace('# ', f'# {cldf.module} ', 1) + '\n'
