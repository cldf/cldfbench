# cldfbench
Tooling to create CLDF datasets from existing data

[![Build Status](https://travis-ci.org/cldf/cldfbench.svg?branch=master)](https://travis-ci.org/cldf/cldfbench)
[![codecov](https://codecov.io/gh/cldf/cldfbench/branch/master/graph/badge.svg)](https://codecov.io/gh/cldf/cldfbench)
[![PyPI](https://img.shields.io/pypi/v/cldfbench.svg)](https://pypi.org/project/cldfbench)


## Overview

This package provides tools to curate cross-linguistic data, with the goal of
packaging it as [CLDF](https://cldf.clld.org) datasets.

In particular, it supports a workflow where 
- "raw" source data is downloaded to a `raw/` subdirectory,
- and subsequently converted to one or more CLDF datasets in a `cldf/` subdirectory, with the help of
  - configuration data in a `etc/` directory and
  - custom Python code (a subclass of [`cldfbench.Dataset`](src/cldfbench/dataset.py) which implements the workflow actions).

This workflow is supported via
- a commandline interface `cldfbench` which calls the workflow actions as [subcommands](src/cldfbench/commands),
- a `cldfbench.Dataset` base class, which must be overwritten in a custom module
  to hook custom code into the workflow.

With this workflow and the separation of the data into three directories we want
to provide a workbench for transparently deriving CLDF data from data that has been
published before. In particular we want to delineate clearly
- what's part of the original or source data (`raw`), 
- what kind of information is added (`etc`)
- to the derived data (`cldf`).


## Install

`cldfbench` can be installed via `pip` - preferably in a 
[virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/) - running
```bash
pip install cldfbench[excel]
```

Note: The `[excel]` extra specification will also install support for reading spreadsheet data.


## The command line interface `cldfbench`

Installing the python package will also install a command `cldfbench` available on
the command line:
```bash
$ cldfbench -h
usage: cldfbench [-h] [--log-level LOG_LEVEL] COMMAND ...

optional arguments:
  -h, --help            show this help message and exit
  --log-level LOG_LEVEL
                        log level [ERROR|WARN|INFO|DEBUG] (default: 20)

available commands:
  Run "COMAMND -h" to get help for a specific command.

  COMMAND
    check               Run generic CLDF checks
    ...
```

As shown above, run `cldfbench -h` to get help, and `cldfbench COMMAND -h` to get
help on individual subcommands, e.g. `cldfbench new -h` to read about the usage
of the `new` subcommand.


### Dataset discovery

Most `cldfbench` commands operate on an existing dataset (unlike `new`, which
creates a new one). Datasets can be discovered in two ways:

1. Via the python module (i.e. the `*.py` file, containing the `Dataset` subclass).
   To use this mode of discovery, pass the path to the python module
   as `DATASET` argument, when required by a command.

2. Via [entry point](https://packaging.python.org/specifications/entry-points/) and
   dataset ID. To use this mode, specify the name of the entry point as value of
   the `--entry-point` option (or use the default name `cldfbench.dataset`) and
   the `Dataset.id` as `DATASET` argument.

Discovery via entry point is particularly useful for commands that can operate
on multiple datasets. To select **all** datasets advertising a given entry point,
pass `"_"` (i.e. an underscore) as `DATASET` argument.


## Workflow

For a full example of the `cldfbench` curation workflow, see [the tutorial](doc/tutorial.md).


### Creating a skeleton for a new dataset directory

A directory containing stub entries for a dataset can be created running

```bash
cldfbench new
```

This will create the following layout (where `<ID>` stands for the chosen dataset ID):
```
<ID>/
├── cldf               # A stub directory for the CLDF data
│   └── README.md
├── cldfbench_<ID>.py  # The python module, providing the Dataset subclass
├── etc                # A stub directory for the configuration data
│   └── README.md
├── metadata.json      # The metadata provided to the subcommand serialized as JSON
├── raw                # A stub directory for the raw data
│   └── README.md
├── setup.cfg          # Python setup config, providing defaults for test integration
├── setup.py           # Python setup file, making the dataset "installable" 
├── test.py            # The python code to run for dataset validation
└── .travis.yml        # Integrate the validation with Travis-CI
```


### Implementing CLDF creation

`cldfbench` provides tools to make CLDF creation simple. Still, each dataset is
different, and so each dataset will have to provide its own custom code to do so.
This custom code goes into the `cmd_makecldf` method of the `Dataset` subclass in
the dataset's python module.

Typically, this code will make use of one or more
[`cldfbench.CLDFSpec`](src/cldfbench/cldf.py) instances, which describes what kind of CLDF to create. A `CLDFSpec` also gives access to a
[`cldfbench.CLDFWriter`](src/cldfbench/cldf.py) instance, which wraps a `pycldf.Dataset`.

The main interfaces to these objects are
- `cldfbench.Dataset.cldf_specs`: a method returning specifications of all CLDF datasets
  that are created by the dataset,
- `cldfbench.Dataset.cldf_writer`: a method returning an initialized `CLDFWriter` 
  associated with a particular `CLDFSpec`.

`cldfbench` supports several scenarios of CLDF creation:
- The typical use case is turning raw data into a single CLDF dataset. This would
  require instantiating one `CLDFWriter` writer in the `cmd_makecldf` method, and
  the defaults of `CLDFSpec` will probably be ok. Since this is the most common and
  simplest case, it is supported with some extra "sugar": The initialized `CLDFWriter`
  is available as `args.writer` when `cmd_makecldf` is called.
- But it is also possible to create multiple CLDF datasets:
  - For a dataset containing both, lexical and typological data, it may be appropriate
    to create a `Ẁordlist` and a `StructureDataset`. To do so, one would have to
    call `cldf_writer` twice, passing in an approriate `CLDFSpec`. Note that if
    both CLDF datasets are created in the same directory, they can share the
    `LanguageTable` - but would have to specify distinct file names for the
    `ParameterTable`, passing distinct values to `CLDFSpec.data_fnames`.
  - When creating multiple datasets of the same CLDF module, e.g. to split a large  dataset into smaller chunks, care must be taken to also disambiguate the name
    of the metadata file, passing distinct values to `CLDFSpec.metadata_fname`.

When creating CLDF, it is also often useful to have standard reference catalogs
accessible, in particular Glottolog. See the section on [Catalogs](#catalogs) for
a description of how this is supported by `cldfbench`.


### Catalogs

Linking data to reference catalogs is a major goal of CLDF dataset, thus `cldfbench`
provides tools to make catalog access and maintenance easier. Catalog data must be
accessible in local clones of the data repository. `cldfbench` provides commands
- `catconfig` to create the clones and make them known through a configuration file,
- `catinfo` to get an overview of the installed catalogs and their versions,
- `catupdate` to update local clones from the upstream repositories.


### Curating a dataset on GitHub

One of the design goals of CLDF was to specify a data format that plays well with
version control. Thus, it's natural - and actually recommended - to curate a CLDF
dataset in a version controled repository. The most popular way to do this in a
collaborative fashion is by using a [git](https://git-scm.com/) repository hosted on 
[GitHub](https://github.com).

The directory layout supported by `cldfbench` caters to this use case in several ways:
- Each directory contains a file `README.md`, which will be rendered as human readable
  description when browsing the repository at GitHub.
- The file `.travis.yml` contains the configuration for hooking up a repository with
  [Travis CI](https://www.travis-ci.org/), to provide continuous consistency checking
  of the data.


### Archiving a dataset with Zenodo

Curating a dataset on GitHub also provides a simple way to archiving and publishing
released versions of the data. You can hook up your repository with [Zenodo](https://zenodo.org) (following [this guide](https://guides.github.com/activities/citable-code/)). Then, Zenodo will pick up any released package, assign a DOI to it, archive it and
make it accessible in the long-term.

Some notes:
- Hook-up with Zenodo requires the repository to be public (not private).
- You should consider using an institutional account on GitHub and Zenodo to associate the repository with. Currently, only the user account registering a repository on Zenodo can change any metadata of releases lateron.
- Once released and archived with Zenodo, it's a good idea to add the DOI assigned by Zenodo to the release description on GitHub.
- To make sure a release is picked up by Zenodo, the version number must start with a letter, e.g. "v1.0" - **not** "1.0".

Thus, with a setup as described here, you can make sure you create [FAIR data](https://en.wikipedia.org/wiki/FAIR_data).


## Extending `cldfbench`

`cldfbench` can be extended or built-upon in various ways - typically by customizing
core functionality in new python packages. To support particular types of raw data,
 you might want a custom `Dataset` class, or to support a particular type of CLDF data,
  you would customize `CLDFWriter`.

In addition to extending `cldfbench` using the standard methods of object-oriented
programming, there are two more ways of extending `cldfbench`:


### Commands

A python package (or a dataset) can provide additional subcommands to be run from `cldfbench`.
For more info see the [`commands.README`](src/cldfbench/commands/README.md).


### Custom dataset templates

A python package can provide alternative dataset templates to be run with `cldfbench new`.
Such templates are implemented by
- a subclass of `cldfbench.Template`,
- which is advertised using an entry point `cldfbench.scaffold`:

```python
    entry_points={
        'cldfbench.scaffold': [
            'template_name=mypackage.scaffold:DerivedTemplate',
        ],
    },
```
