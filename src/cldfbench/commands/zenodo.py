"""
Write metadata for Zenodo to .zenodo.json
"""
import html
import collections

from clldutils.jsonlib import update
from clldutils.misc import nfilter

from cldfbench.cli_util import add_dataset_spec, get_dataset, set_creators_and_contributors


def register(parser):  # pylint: disable=C0116
    add_dataset_spec(parser, multiple=True)
    parser.add_argument(
        '--communities',
        default='',
        help='Comma-separated list of communities to which the dataset should be submitted',
    )


def run(args):  # pylint: disable=C0116
    dataset = get_dataset(args)
    with update(dataset.dir / '.zenodo.json', indent=4, default=collections.OrderedDict()) as md:
        modules = ['cldf:' + spec.module for spec in dataset.cldf_specs_dict.values()]
        set_creators_and_contributors(dataset, md)
        communities = [r["identifier"] for r in md.get("communities", [])] + \
                      [c.strip() for c in nfilter(args.communities.split(','))]
        if communities:
            md['communities'] = [
                {"identifier": community_id} for community_id in sorted(set(communities))]
        md.update(
            {
                "title": dataset.metadata.title,
                "access_right": "open",
                "keywords": sorted(set(md.get("keywords", []) + ["linguistics"] + modules)),
                "upload_type": "dataset",
            }
        )
        if dataset.metadata.citation:
            md['description'] = \
                f"<p>Cite the source of the dataset as:</p>\n\n" \
                f"<blockquote>\n<p>{html.escape(dataset.metadata.citation)}</p>\n</blockquote>"
        if dataset.metadata.zenodo_license:
            md['license'] = {'id': dataset.metadata.zenodo_license}
