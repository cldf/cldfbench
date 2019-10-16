"""
Dataset metadata
"""
import json
import collections

import attr
from clldutils import licenses

__all__ = ['Metadata']


@attr.s
class Metadata(object):
    """
    Dataset metadata is used as follows:
    - it is (partly) elicited when creating a new dataset directory ...
    - ... and subsequently written to the directory ...
    - ... where it may be edited ("by hand") ...
    - ... and from where it is read when initializing a `Dataset` object.
    """
    id = attr.ib(
        default=None,
        metadata=dict(elicit=True))
    title = attr.ib(
        default=None,
        metadata=dict(elicit=True))
    description = attr.ib(
        default=None)
    license = attr.ib(
        default=None,
        metadata=dict(elicit=True))
    url = attr.ib(
        default=None,
        metadata=dict(elicit=True))
    citation = attr.ib(
        default=None,
        metadata=dict(elicit=True))

    @classmethod
    def elicit(cls):
        """
        Factory method, called when creating a new dataset directory.
        """
        kw = {}
        for field in attr.fields(cls):
            if field.metadata.get('elicit', False):
                res = input('{0}: '.format(field.name))
                if (not res) and field.default is not attr.NOTHING:
                    res = field.default
                kw[field.name] = res
        return cls(**kw)

    @classmethod
    def from_file(cls, fname):
        """
        Factory method, called when instantiating a `Dataset` object.
        """
        with fname.open('r', encoding='utf-8') as fp:
            return cls(**json.load(fp))

    def write(self, fname):
        with fname.open('w', encoding='utf-8') as fp:
            return json.dump(attr.asdict(self), fp, indent=4)

    @property
    def known_license(self):
        if self.license:
            return licenses.find(self.license)

    def common_props(self):
        """
        The metadata as JSON-LD object suitable for inclusion in CLDF metadata.
        """
        res = collections.OrderedDict()
        if self.title:
            res["dc:title"] = self.title
        if self.description:
            res["dc:description"] = self.description
        if self.citation:
            res["dc:bibliographicCitation"] = self.citation
        if self.url:
            res["dc:identifier"] = self.url
        if self.known_license:
            res['dc:license'] = self.known_license.url
        elif self.license:
            res['dc:license'] = self.license
        return res

    def markdown(self):
        lines = ['# {0}\n'.format(self.title or 'Dataset {0}'.format(self.id))]
        if self.citation:
            lines.extend([
                'Cite the source dataset as\n',
                '> %s\n' % self.citation,
            ])

        if self.description:
            lines.append('\n{0}\n'.format(self.description))

        if self.license:
            lines.append('This dataset is licensed under a %s license\n' % self.license)

        if self.url:
            lines.append('Available online at %s\n' % self.url)

        return '\n'.join(lines)
