"""
Run generic CLDF checks

Returns 1 on validation error, else 2 if there are warnings or 0.
"""
import attr
import pytest
from cldfbench.cli_util import add_dataset_spec, with_datasets


def register(parser):
    add_dataset_spec(parser, multiple=True)
    parser.add_argument('--with-tests', action='store_true', default=False)
    parser.add_argument('--with-validation', action='store_true', default=False)


def run(args):
    res = with_datasets(args, check)
    return 1 if 1 in res else (2 if 2 in res else 0)


def check(ds, args):
    success, warnings = True, []

    if args.with_tests:  # pragma: no cover
        testfile = ds.dir / "test.py"
        if testfile.is_file():
            args.log.info("Running tests...")
            pytest.main([
                '--cldf-metadata=%s' % ds.default_cldf_spec.metadata_path,
                testfile
            ])
        else:
            args.log.warning("No tests found")

    if args.with_validation:
        args.log.info("Validating CLDF...")
        for key, cldf_spec in ds.cldf_specs_dict.items():
            cldf = cldf_spec.get_dataset()
            success = success and cldf.validate(log=args.log)

    for field in attr.fields(ds.metadata.__class__):
        if field.metadata.get('required', False) and not getattr(ds.metadata, field.name):
            args.log.warning('Empty field "{0}" in metadata'.format(field.name))
            warnings.append(field.name)
    return (2 if warnings else 0) if success else 1
