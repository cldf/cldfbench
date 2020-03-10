"""
Create a "releasable" version of a cldfbench curated dataset.
"""
import os
import shutil
import pathlib
import argparse
import tempfile
import subprocess
import contextlib

CATALOGS = ['glottolog', 'concepticon', 'clts']


@contextlib.contextmanager
def cwd(d):
    old = pathlib.Path.cwd()
    os.chdir(str(d))
    try:
        yield
    finally:
        os.chdir(str(old))


def repos_ok(d):
    res = False
    with cwd(d):
        subprocess.check_output(['git', 'fetch', 'origin', 'master'])
        status = subprocess.check_output(['git', 'status']).decode('utf8')
        if 'Changes not staged for commit' in status:
            return False
        if 'Untracked files' in status:
            return False
        if ("Your branch is up-to-date with 'origin/master'" in status) and \
                ('Changes not staged for commit' not in status) and \
                ('Changes not staged for commit' not in status):
            res = TypeError
        if not res:
            print('\n"git status" for {}:\n\n{}'.format(d, status))
        return res


def main(args):
    dsdir = pathlib.Path(args.repository)
    assert dsdir.exists()

    if not repos_ok(dsdir):
        print('ERROR: The dataset repository must not have local changes and be fully updated with '
              'origin/master\n')
        return 1

    tmpdir = pathlib.Path(tempfile.gettempdir())

    # We create a fresh virtualenv:
    venv = tmpdir / 'venv'
    if venv.exists():
        shutil.rmtree(str(venv))
    subprocess.check_call(['python3', '-m', 'venv', str(venv)])

    def cmd(name):
        return str(venv.joinpath('bin', name).resolve())

    with cwd(dsdir):
        # Then update install and build tools:
        subprocess.check_call([cmd('pip'), 'install', '-U', 'wheel', 'setuptools', 'pip'])
        # Followed by the dataset and its dependencies:
        subprocess.check_call([cmd('pip'), 'install', '-e', '.'])
        # Now we lookup the dataset ID using the entry point:
        eps = eval(subprocess.check_output([
            cmd('python'),
            '-c',
            "import pkg_resources as pr; "
            "print([e.name for e in pr.iter_entry_points('{}')])".format(args.entry_point),
        ]))
        assert len(eps) == 1
        dsid = eps[0]
        arg = [
            cmd('cldfbench'),
            args.makecldf_prefix + 'makecldf',
            dsid,
            '--entry-point',
            args.entry_point,
        ]
        for cat in CATALOGS:
            if getattr(args, cat + '_version'):
                arg.extend(['--{}-version'.format(cat), getattr(args, cat + '_version')])
        subprocess.check_call(arg)
        subprocess.check_call([cmd('cldfbench'), 'diff', dsid, '--entry-point', args.entry_point])
        print('OK: Commit and push changes in {} and release via GitHub UI!'.format(dsdir))


if __name__ == '__main__':
    import sys

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('repository')
    for cat in CATALOGS:
        parser.add_argument('--{}-version'.format(cat), default=None)
    parser.add_argument('--makecldf-prefix', default='', help='Prefix for the makecldf subcommand')
    parser.add_argument(
        '--entry-point', default='cldfbench.dataset', help='Entry point group to discover dataset')
    sys.exit(main(parser.parse_args()) or 0)
