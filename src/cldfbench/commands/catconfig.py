"""
Write a config file containing the local paths of clones of Catalogs.

Paths of existing clones can be specified as cli options, or, if confirmed, the repositories
will be freshly cloned from GitHub.
"""
from clldutils.clilib import confirm
from cldfcatalog import Config

from cldfbench.cli_util import add_catalog_spec
from cldfbench.catalogs import BUILTIN_CATALOGS


def register(parser):
    for cat in BUILTIN_CATALOGS:
        add_catalog_spec(parser, cat.cli_name(), with_version=False)
    parser.add_argument(
        '-q', '--quiet',
        help="run quietly, don't prompt for input",
        action='store_true',
        default=False,
    )
    parser.set_defaults(no_catalogs=True)


def run(args):
    with Config.from_file() as cfg:
        for cat in BUILTIN_CATALOGS:
            val = getattr(args, cat.cli_name())
            if not val:
                if cat.default_location().exists():  # pragma: no cover
                    val = cat(cat.default_location()).dir
                    args.log.info('CLone of {0} exists at {1} - skipping'.format(
                        cat.__github__, cat.default_location()))
                elif args.quiet or confirm(
                        'clone {0}?'.format(cat.__github__), default=False):  # pragma: no cover
                    url = 'https://github.com/{0}.git'.format(cat.__github__)
                    args.log.info('Cloning {0} into {1} ...'.format(url, cat.default_location()))
                    val = cat.clone(url).dir
                    args.log.info('... done')
            else:
                try:
                    cat(val)
                except ValueError as e:  # pragma: no cover
                    args.log.warning(str(e))
            if val:
                cfg.add_clone(cat.cli_name(), val)

    args.log.info('Config written to {0}'.format(cfg.fname()))
