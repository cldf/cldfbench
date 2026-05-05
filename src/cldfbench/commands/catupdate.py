"""
Update local clones of catalog repositories.

Note: This only *fetches* from the origin repository, i.e. the checked
out branch will *not* be updated (like with `git pull`).
"""
from cldfcatalog import Config

from cldfbench.cli_util import add_catalog_spec, instantiate_catalog
from cldfbench.catalogs import BUILTIN_CATALOGS


def register(parser):  # pylint: disable=C0116
    for cat in BUILTIN_CATALOGS:
        add_catalog_spec(parser, cat.cli_name(), with_version=False)
    parser.set_defaults(no_catalogs=True)


def run(args):  # pylint: disable=C0116
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
            catinst = instantiate_catalog(cat, path, args.log)
            if not catinst:
                continue  # pragma: no cover

            for fetch_info in catinst.update():  # pragma: no cover
                args.log.info('%s: fetch %s %s', name, fetch_info.ref, fetch_info.note)
