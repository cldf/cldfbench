"""
Display basic info about a dataset
"""
from cldfbench.cli_util import with_datasets, add_dataset_spec


def register(parser):
    add_dataset_spec(parser, multiple=True)
    parser.add_argument(
        '--cldf',
        help="Print all CLDF metadata file paths curated by a dataset.",
        action='store_true',
        default=False)


def run(args):
    def _print(ds, args):
        if args.cldf:
            for cldf in ds.cldf_specs_dict.values():
                print(cldf.metadata_path)
        else:
            print(ds)
    with_datasets(args, _print)
