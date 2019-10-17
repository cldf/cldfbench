"""
Write a config file
"""
import pathlib

from cldfbench.cli_util import add_catalog_spec, Config
from cldfbench.catalogs import BUILTIN_CATALOGS


def register(parser):
    for cat in BUILTIN_CATALOGS:
        add_catalog_spec(parser, cat.cli_name(), with_version=False)
    parser.set_defaults(no_catalogs=True)


def run(args):
    cfg = Config.from_file()
    for cat in BUILTIN_CATALOGS:
        val = getattr(args, cat.cli_name())
        if not val:
            val = input('Path to clone of https://github.com/{0}: '.format(cat.__doc__))
        val = pathlib.Path(val).resolve()
        try:
            cat(val)
        except ValueError as e:
            args.log.warning(str(e))
        cfg['catalogs'][cat.cli_name()] = str(val)

    cfg.to_file()
    args.log.info('Config written to {0}'.format(cfg.fname))
