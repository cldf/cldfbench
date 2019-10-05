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
