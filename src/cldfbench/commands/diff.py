"""
Compute "essential" changes of the data in the cldf directory of a dataset's git repository.

Returns 2 if essential differences are detected, 0 otherwise.

If there are differences, this means current HEAD of the repository at GitHub **cannot** be
released, but changes must be commited and pushed to GitHub first.
"""
import json
import difflib
import pathlib

import git
from clldutils import jsonlib

from cldfbench.cli_util import with_dataset, add_dataset_spec


def register(parser):
    add_dataset_spec(parser)
    parser.add_argument('--verbose', action='store_true', default=False)


def run(args):
    res = with_dataset(args, diff)
    if res == 2:
        args.log.info('----------------------------------------------------------------------')
        args.log.info('Please commit and push changes to GitHub before releasing the dataset!')
        args.log.info('----------------------------------------------------------------------')
    return res


def print_diff(diff, d):  # pragma: no cover
    a = diff.a_blob.data_stream.read().decode('utf-8').splitlines()
    b = d.joinpath(diff.a_path).read_text(encoding='utf8').splitlines()
    print('\n'.join(difflib.unified_diff(a, b, fromfile=diff.a_path, lineterm='', n=1)))


def diff(ds, args):
    try:
        repo = git.Repo(str(ds.dir))
    except git.InvalidGitRepositoryError:  # pragma: no cover
        args.log.warning('{} is not a git repository. Cannot diff'.format(ds.dir))
        return

    md_changed = None
    print(repo.git.status('cldf'))

    diff = repo.index.diff(None)

    if args.verbose:  # pragma: no cover
        for diff_item in diff.iter_change_type('M'):
            print_diff(diff_item, ds.dir)

    for item in diff:
        if item.a_path.startswith('cldf/'):
            p = pathlib.Path(item.a_path)
            if (not p.name.startswith('.')) and p.name != 'requirements.txt':
                if p.name.endswith('metadata.json'):
                    md_changed = item.a_path
                else:  # pragma: no cover
                    args.log.warning('Data file {} changed!'.format(p))
                    return 2

    def log_diff(dold, dnew, thing='metadata'):
        diff = False
        for k, v in dnew.items():
            if k not in dold:
                args.log.warning('New {}: {}: {}'.format(thing, k, v))
                diff = True
            elif v != dold[k]:
                args.log.warning('Changed {}: {}: {} -> {}'.format(thing, k, dold[k], v))
                diff = True
        return diff

    def derived_to_dict(d):
        return {
            o['dc:title']: o['dc:created'] for o in d.get('prov:wasDerivedFrom', [])
            if not ds.repo or (o.get('rdf:about') != ds.repo.url)
        }

    if md_changed:
        exclude = {'tables', 'prov:wasGeneratedBy', 'prov:wasDerivedFrom'}
        old = json.loads(repo.git.show('HEAD:{0}'.format(md_changed)))
        new = jsonlib.load(ds.dir / md_changed)

        diff = any([
            log_diff(derived_to_dict(old), derived_to_dict(new), thing='repository version'),
            log_diff(
                {k: v for k, v in old.items() if k not in exclude},
                {k: v for k, v in new.items() if k not in exclude},
            )])
        return 2 if diff else 0
