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


## Dataset specific commands

Individual datasets can be installed as Python packages as well, thanks to their `setup.py` file.
This means that you can provide custom `cldfbench` subcommands with a dataset, e.g.
commands to analyze the CLDF data created from a dataset.

To do so,
- add a Python package with a unique name (e.g. `<datasetid>commands` to your dataset, i.e. create a 
  subdirectory `<datasetid>commands`, containing
  - an empty file `__init__.py`,
  - python modules as specified above implementing the commands,
- make this package known to `cldfbench` via an entry point in `setup.py`:
  ```python
  entry_points={
      'cldfbench.commands': [
          'dsid=<datasetid>commands',
      ],
  }
  ```
- install the dataset running `pip install -e .`
- check the availability of your custom commands running `cldfbench -h`.

Note: Since the package containing the commands is imported as top-level Python, it is important to give it a name that does not clash with any other Python package you may want to use! Python packages and modules are singletons identified by name, so only one will be imported!
