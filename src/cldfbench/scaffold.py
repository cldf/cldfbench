"""
Functionality to create a skeleton of a directory layout for the curation of a CLDF dataset.

Customized templates can be registered (to be used with the `cldfbench new` command) by providing
the path to the class as `cldfbench.scaffold` entry point.

Templates can be customized by
- providing additional (or entirely different) template files, by overwriting `Template.dirs`
- providing more metadata as template variables, by overwriting `Template.metadata` with a
  custom subclass of `cldfbench.metadata.Metadata`.
"""
import pathlib
import re
import shutil
import warnings
import pkg_resources

import attr

import cldfbench
from cldfbench.metadata import Metadata

__all__ = ['Template']


def iter_scaffolds():
    yield 'cldfbench', Template
    for ep in pkg_resources.iter_entry_points('cldfbench.scaffold'):
        try:
            yield ep.name, ep.load()
        except Exception as e:  # pragma: no cover
            warnings.warn(
                '{0} loading cldfbench.scaffold {1}'.format(e.__class__.__name__, ep.name))


class Template(object):
    """A CLDF dataset suitable for curation in a GitHub repository"""
    prefix = cldfbench.__name__
    package = cldfbench.__name__

    # To overwite individual template files, provide a secondary template directory which
    # contains only the specialized template files.
    dirs = [pathlib.Path(cldfbench.__file__).parent / 'dataset_template']

    id_pattern = re.compile('[a-z_0-9]+$')
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
    ...     custom_var = attr.ib(default=None, metadata=dict(elicit=True))
    ...
    >>> class CustomTemplate(Template):
    ...     metadata = CustomMetadata
    """
    metadata = Metadata

    def render(self, outdir, metadata):
        # The cli will have used the class in `self.metadata` to elicit info from the user,
        # and pass `self.metadata(...)` as `metadata`

        ctx = attr.asdict(metadata)
        ctx.update(prefix=self.prefix, package=self.package)
        if outdir.name != ctx['id']:
            outdir = outdir / ctx['id']
        if not outdir.exists():
            outdir.mkdir()

        for dir_ in self.dirs:
            for path in dir_.iterdir():
                if path.is_file():
                    if path.suffix in ['.pyc']:
                        continue  # pragma: no cover
                    target = path.name
                    if '+' in path.name:
                        target = re.sub(
                            '\+([a-z]+)\+',
                            lambda m: '{' + m.groups()[0] + '}',
                            path.name
                        ).format(**ctx)
                    if target.endswith('_tmpl'):
                        content = path.read_text(encoding='utf-8')
                        target = target[:-5]
                        (outdir / target).write_text(content.format(**ctx), encoding='utf-8')
                    else:
                        shutil.copy(str(path), str(outdir / target))
                else:
                    target = outdir / path.name
                    if target.exists():
                        shutil.rmtree(str(target))
                    shutil.copytree(str(path), str(target))

        metadata.write(outdir / 'metadata.json')
