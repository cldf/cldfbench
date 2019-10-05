"""
Functionality to create a skeleton of a directory layout for the curation of a CLDF dataset.

Customized templates can be registered (to be used with the `cldfbench new` command) by providing
the path to the class as `cldfbench.scaffold` entry point.
"""
import pathlib
import re
import shutil
import json
import pkg_resources

import attr

import cldfbench


def iter_scaffolds():
    for ep in pkg_resources.iter_entry_points('cldfbench.scaffold'):
        yield ep.load()


@attr.s
class Metadata(object):
    """
    An instance of this class will be provided as template variables when the template is
    rendered.

    To add more variables,
    - inherit from `Metadata`
    - add attribs
    - assign the derived class to your template's `metadata` attribute.

    E.g.
    >>> @attr.s
    ... class CustomMetadata(Metadata):
    ...     custom_var = attr.ib()
    ...
    >>> class CustomTemplate(Template):
    ...     metadata = CustomMetadata
    """
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
            if (not res) and field.default is not attr.NOTHING:
                res = field.default
            kw[field.name] = res
        return cls(**kw)


class Template(object):
    """A CLDF dataset suitable for curation in a GitHub repository"""
    prefix = cldfbench.__name__
    package = cldfbench.__name__

    # To overwite individual template files, provide a secondary template directory which
    # contains only the specialized template files.
    dirs = [pathlib.Path(cldfbench.__file__).parent / 'dataset_template']

    id_pattern = re.compile('[a-z_0-9]+$')
    metadata = Metadata
    with_metadata_json = True

    def render(self, outdir, metadata):
        # The cli will have used the class in `self.metadata` to elicit info from the user,
        # and pass `self.metadata(...)` as `metadata`

        metadata = attr.asdict(metadata)
        metadata.update(prefix=self.prefix, package=self.package)
        if outdir.name != metadata['id']:
            outdir = outdir / metadata['id']
        if not outdir.exists():
            outdir.mkdir()

        for dir_ in self.dirs:
            for path in dir_.iterdir():
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
        if self.with_metadata_json:
            with (outdir / 'metadata.json').open('w', encoding='utf-8') as fp:
                return json.dump(metadata, fp, indent=4)
