# cldfbench
Tooling to create CLDF datasets from existing data

[![Build Status](https://travis-ci.org/cldf/cldfbench.svg?branch=master)](https://travis-ci.org/cldf/cldfbench)
[![codecov](https://codecov.io/gh/cldf/cldfbench/branch/master/graph/badge.svg)](https://codecov.io/gh/cldf/cldfbench)
[![PyPI](https://img.shields.io/pypi/v/cldfbench.svg)](https://pypi.org/project/cldfbench)


## Overview

This package provides tools to curate cross-linguistic data, with the goal of
packaging it as [CLDF](https://cldf.clld.org) dataset.

In particular, it supports a workflow where 
- "raw" source data is downloaded to a `raw` subdirectory,
- and subsequently converted to a CLDF dataset in a `cldf` subdirectory, with the help of
  - configuration data in a `etc` directory
  - custom Python code (a subclass of `cldfbench.Dataset` which implements the workflow actions)

This workflow is supported via
- a commandline interface `cldfbench` which calls the workflow actions via subcommands,
- a `cldfbench.Dataset` base class, which must be overwritten in a custom module
  to hook custom code into the workflow.


### Creating a skeleton for a new dataset directory

A directory containing stub entries for a dataset can be created running

```bash
cldfbench new cldfbench OUTDIR
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


## Curating a dataset on GitHub

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


## Archiving a dataset with Zenodo

Curating a dataset on GitHub also provides a simple way to archiving and publishing
released versions of the data. You can hook up your repository with [Zenodo](https://zenodo.org) (following [this guide](https://guides.github.com/activities/citable-code/)). Then, Zenodo will pick up any released package, assign a DOI to it, archive it and
make it accessible in the long-term.

Some notes:
- Hook-up with Zenodo requires the repository to be public (not private).
- You should consider using an institutional account on GitHub and Zenodo to associate the repository with. Currently, only the user account registering a repository on Zenodo can change any metadata of releases lateron.
- Once released and archived with Zenodo, it's a good idea to add the DOI assigned by Zenodo to the release description on GitHub.
- To make sure a release is picked up by Zenodo, the version number must start with a letter, e.g. "v1.0" - **not** "1.0".

Thus, with a setup as described here, you can make sure you create [FAIR data](https://en.wikipedia.org/wiki/FAIR_data).

