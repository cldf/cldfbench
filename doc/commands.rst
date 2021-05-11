
`cldfbench` Commands
====================

The "bench" in `cldfbench` means that it can be used to apply tools to CLDF data.
Now, being software, the ultimate tool that can be applied with `cldfbench` is
custom code, provided by the user - rather than "off-the-shelve" tools like
`cldfbench makecldf`.

The basics of custom `cldfbench` commands is described in
<this README <https://github.com/cldf/cldfbench/blob/master/src/cldfbench/commands/README.md>`_

The following utilities to be used in commands are available:


Register arguments
~~~~~~~~~~~~~~~~~~

These functions are typically called in a command's `register` function.

.. automodule:: cldfbench.cli_util
   :members: add_dataset_spec, add_catalog_spec


Access objects
~~~~~~~~~~~~~~

These functions are typically called in a command's `run` function.

.. automodule:: cldfbench.cli_util
   :noindex:
   :members: get_dataset, get_datasets, get_cldf_dataset, with_dataset, with_datasets

