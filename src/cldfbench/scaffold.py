import pathlib
import re
import shutil
import pkg_resources

import attr

import cldfbench


def iter_scaffolds():
    for ep in pkg_resources.iter_entry_points('cldfbench.scaffold'):
        yield ep.load()


@attr.s
class Metadata(object):
    id = attr.ib()
    title = attr.ib()
    license = attr.ib()
    url = attr.ib()
    citation = attr.ib()

    @classmethod
    def elicit(cls):
        kw = {}
        for field in attr.fields(cls):
            res = input('{0}: '.format(field.name))
            if (not res) and field.default:
                res = field.default
            kw[field.name] = res
        return cls(**kw)


class Template(object):
    """A CLDF dataset suitable for curation in a GitHub repository"""
    prefix = cldfbench.__name__
    dir = pathlib.Path(cldfbench.__file__).parent / 'dataset_template'
    id_pattern = re.compile('[a-z_0-9]+$')
    metadata = Metadata

    def render(self, outdir, metadata):
        # The cli will have used the class in `self.metadata` to elicit info from the user,
        # and pass `self.metadata(...)` as `metadata`

        metadata = attr.asdict(metadata)
        metadata['prefix'] = self.prefix
        if outdir.name != metadata['id']:
            outdir = outdir / metadata['id']
        if not outdir.exists():
            outdir.mkdir()

        for path in self.dir.iterdir():
            if path.is_file():
                if path.suffix in ['.pyc']:
                    continue  # pragma: no cover
                target = path.name
                content = path.read_text(encoding='utf-8')
                if '+' in path.name:
                    target = re.sub(
                        '\+([a-z]+)\+',
                        lambda m: '{' + m.groups()[0] + '}',
                        path.name
                    ).format(**metadata)
                if target.endswith('_tmpl'):
                    target = target[:-5]
                    content = content.format(**metadata)
                (outdir / target).write_text(content, encoding='utf-8')
            else:
                target = outdir / path.name
                if target.exists():
                    shutil.rmtree(str(target))
                shutil.copytree(str(path), str(target))
        #del md['id']
        #jsonlib.dump(md, outdir / 'metadata.json', indent=4)
