"""
Display basic info about a dataset
"""
from cldfbench.cli_util import with_dataset, add_dataset_spec, get_datasets


def register(parser):
    add_dataset_spec(parser, multiple=True)


def run(args):
    for ds in get_datasets(args):
        with_dataset(args, lambda ds, _: print(ds), dataset=ds)
