
`cldfbench` Datasets
====================

While most of `cldfbench`'s functionality is invoked from the command line
via `cldfbench` subcommands, most of this functionality is implemented in
the :class:`cldfbench.Dataset` class - and derived classes for specific datasets.


.. autoclass:: cldfbench.dataset.Dataset
   :members: repo


Metadata
~~~~~~~~

.. autoclass:: cldfbench.metadata.Metadata



`cldfbench` Dataset vs CLDF Dataset
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A `cldfbench` Dataset wraps "raw" source data, conversion code and generated
CLDF data into a package. It's possible for one `cldfbench` Dataset to create
more than one CLDF Dataset. Access to the CLDF Datasets maintained in a `cldfbench`
Dataset is provided as follows:

.. automethod:: cldfbench.Dataset.cldf_specs

.. autoattribute:: cldfbench.Dataset.cldf_specs_dict

.. automethod:: cldfbench.Dataset.cldf_writer

.. automethod:: cldfbench.Dataset.cldf_reader


Configuring CLDF writing
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: cldfbench.CLDFSpec

.. autoclass:: cldfbench.CLDFWriter
   :members:



Accessing data
~~~~~~~~~~~~~~

The three "data" directories can be accessed a :class:`cldfbench.DataDir` instances:

.. autoattribute:: cldfbench.Dataset.raw_dir

.. autoattribute:: cldfbench.Dataset.etc_dir

.. autoattribute:: cldfbench.Dataset.cldf_dir

.. autoclass:: cldfbench.datadir.DataDir
   :members:


Curation workflow
~~~~~~~~~~~~~~~~~

Workflow commands are implemented with two methods for each command:

- `cmd_<command>`: The implementation of the command, typically overwritten by datasets.
- `_cmd_<command>`: An (optional) wrapper providing setup and teardown functionality, calling `cmd_<command>` in between.

Workflow commands must accept an `argparse.Namespace` as sole positional argument.


.. automethod:: cldfbench.Dataset.cmd_download

.. automethod:: cldfbench.Dataset.cmd_makecldf

.. automethod:: cldfbench.Dataset.cmd_readme

.. automethod:: cldfbench.Dataset.update_submodules


Dataset discovery
~~~~~~~~~~~~~~~~~

`cldfbench` Datasets may be packaged as installable Pyhthon packages. In this case
they may advertise an `entry point <https://packaging.python.org/specifications/entry-points/>` pointing to their `cldfbench.Dataset` subclass. Such entry points may be
used to discover datasets.

.. autofunction:: cldfbench.dataset.iter_datasets

.. autofunction:: cldfbench.dataset.get_dataset

.. autofunction:: cldfbench.dataset.get_datasets

