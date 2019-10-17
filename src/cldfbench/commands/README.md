# `cldfbench` commands

Code to be run as subcommand in the `cldfbench` cli must comply with the following spec:

1. It must be provided in a python module, the name of which will serve as the command name.
2. The module must provide a function `run`, accepting the `argparse.Namespace` as only positional
   argument. This function should implement the command's functionality.
3. The module may provide a function `register`, accepting a `argparse.Parser` instance, to add
   custom cli parser functionality.
4. The module must be part of an installed Python package, which is published via an entry point
   ```python
    'cldfbench.commands': [
        'commands=path.to.package',
    ],
   ```

A command's `register` function can use packaged functionality from `cldfbench.cli_util`, e.g.
to add options for standard reference catalogs (see `cldfbench.catalogs`), or for dataset discovery.
