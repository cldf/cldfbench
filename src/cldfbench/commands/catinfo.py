"""
Display information about catalogs in the system
"""
import termcolor

from cldfcatalog import Config

from cldfbench.cli_util import add_catalog_spec
from cldfbench.catalogs import BUILTIN_CATALOGS
from cldfbench.util import iter_aligned


def register(parser):
    for cat in BUILTIN_CATALOGS:
        add_catalog_spec(parser, cat.cli_name(), with_version=False)
    parser.add_argument(
        '--max-versions',
        default=5,
        help='Maximal number of versions to display',
        type=int)
    parser.set_defaults(no_catalogs=True)


def print_kv(k, v=''):
    print('{0} {1}'.format(termcolor.colored('{0}:'.format(k), attrs=['bold']), v))


def run(args):
    cfg = Config.from_file()
    for cat in BUILTIN_CATALOGS:
        name = cat.cli_name()

        print()
        print(termcolor.colored(
            '{0} - https://github.com/{1}'.format(name, cat.__github__),
            attrs=['bold', 'underline']))
        print()

        path, from_cfg = getattr(args, name), False
        if (not path) and (not args.no_config):
            try:
                path, from_cfg = cfg.get_clone(name), True
            except KeyError as e:
                args.log.warning(str(e))
                continue

        try:
            cat = cat(path)
        except ValueError as e:  # pragma: no cover
            args.log.warning(str(e))
            continue

        print_kv('local clone', cat.dir.resolve())
        if from_cfg:
            print_kv('config at', cfg.fname())
        print_kv('versions')
        for i, version in enumerate(iter_aligned(cat.iter_versions(), prefix='  ')):
            if i < args.max_versions:
                print(version)
        if cat.__api__:
            print_kv('API', '{0.__name__} {0.__version__}'.format(cat.__api_pkg__))
        print()
