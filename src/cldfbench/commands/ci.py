"""
Setup CLDF validation as CI service via GitHub actions.
"""
import argparse

import git

from cldfbench.cli_util import add_dataset_spec, get_dataset
from cldfbench.ci import setup, build_status_badge


def register(parser):
    add_dataset_spec(parser, multiple=True)
    parser.add_argument('--test', help=argparse.SUPPRESS, action='store_true', default=False)


def run(args):
    dataset = get_dataset(args)
    if setup(dataset, force=args.test):
        if not args.test:  # pragma: no cover
            print(git.cmd.Git(str(dataset.dir)).status())
    print('You may include the following status badge in any markdown file in the repos:\n')
    print(build_status_badge(dataset))
