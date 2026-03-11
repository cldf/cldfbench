"""
Display information about catalogs in the system
"""
import functools

from cldfcatalog import Config

from cldfbench.cli_util import add_catalog_spec, instantiate_catalog
from cldfbench.catalogs import BUILTIN_CATALOGS
from cldfbench.util import iter_aligned, colored


bold = functools.partial(colored, 'black', attrs=['bold'])
bold_underlined = functools.partial(colored, 'black', attrs=['bold', 'underline'])


def register(parser):  # pylint: disable=C0116
    for cat in BUILTIN_CATALOGS:
        add_catalog_spec(parser, cat.cli_name(), with_version=False)
    parser.add_argument(
        '--max-versions',
        default=5,
        help='Maximal number of versions to display',
        type=int)
    parser.set_defaults(no_catalogs=True)


def run(args):  # pylint: disable=C0116
    def print_kv(k: str, v: str = ''):
        print(f'{bold(str(k))}\t{v}')

    cfg = Config.from_file()
    for cat in BUILTIN_CATALOGS:
        name = cat.cli_name()

        print()
        print(bold_underlined(f'{name} - https://github.com/{cat.__github__}'))
        print()

        path, from_cfg = getattr(args, name), False
        if (not path) and (not args.no_config):
            try:
                path, from_cfg = cfg.get_clone(name), True
            except KeyError as e:
                args.log.warning(str(e))
                continue

        catinst = instantiate_catalog(cat, path, args.log)
        if not catinst:
            continue

        print_kv('local clone', str(catinst.dir.resolve()))
        if from_cfg:
            print_kv('config at', str(cfg.fname()))
        print_kv('versions')
        versions = [v for i, v in enumerate(catinst.iter_versions()) if i < args.max_versions]
        for version in iter_aligned(versions, prefix='  ', minspace=4):
            print(version)
        if cat.__api__:
            print_kv('API', f'{cat.__api_pkg__.__name__} {cat.__api_pkg__.__version__}')
        print()
