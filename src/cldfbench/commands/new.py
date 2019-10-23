"""
Create a skeleton for a new dataset
"""
import pathlib
import collections

from cldfbench import scaffold

_templates = None


def get_template_dict():
    global _templates
    if _templates is None:
        _templates = collections.OrderedDict(scaffold.iter_scaffolds())
    return _templates


def register(parser):
    templates = list(get_template_dict().keys())
    parser.add_argument(
        '--template',
        help='Template type',
        default=templates[0],
        choices=templates)
    parser.add_argument(
        '--out',
        help='Directory in which to create the skeleton',
        type=pathlib.Path,
        default=pathlib.Path('.'))


def run(args):
    tmpl = get_template_dict()[args.template]()
    md = tmpl.metadata.elicit()
    tmpl.render(args.out, md)
