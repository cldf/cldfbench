"""
Update local clones of catalog repositories.

Note: This only *fetches* from the origin repository, i.e. the checked
out branch will *not* be updated (like with `git pull`).
"""
from cldfcatalog import Config

from cldfbench.cli_util import add_catalog_spec
from cldfbench.catalogs import BUILTIN_CATALOGS


def register(parser):
    for cat in BUILTIN_CATALOGS:
        add_catalog_spec(parser, cat.cli_name(), with_version=False)
    parser.set_defaults(no_catalogs=True)


def run(args):
    cfg = Config.from_file()
    for cat in BUILTIN_CATALOGS:
        name = cat.cli_name()
        path = getattr(args, name)
        if (not path) and (not args.no_config):  # pragma: no cover
            try:
                path = cfg.get_clone(name)
            except KeyError as e:
                args.log.warning(str(e))
                continue

        if path:
            try:
                cat = cat(path)
            except ValueError as e:  # pragma: no cover
                args.log.warning(str(e))
                continue
            for fetch_info in cat.update():  # pragma: no cover
                args.log.info('{0}: fetch {1.ref} {1.note}'.format(name, fetch_info))
