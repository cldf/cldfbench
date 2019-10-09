"""
Run a custom dataset command
"""
import argparse

from cldfbench.cli_util import with_dataset, add_dataset_spec


def register(parser):
    add_dataset_spec(parser)
    parser.add_argument('cmd', help='command to run on the dataset')
    parser.add_argument('args', nargs=argparse.REMAINDER)


def run(args):
    with_dataset(args, args.cmd)
