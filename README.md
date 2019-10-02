# cldfbench
Tooling to create CLDF datasets from existing data

[![Build Status](https://travis-ci.org/cldf/cldfbench.svg?branch=master)](https://travis-ci.org/cldf/cldfbench)
[![codecov](https://codecov.io/gh/cldf/cldfbench/branch/master/graph/badge.svg)](https://codecov.io/gh/cldf/cldfbench)
[![PyPI](https://img.shields.io/pypi/v/cldfbench.svg)](https://pypi.org/project/cldfbench)


## Overview

With `pylexibank` we have a tool to create CLDF Wordlists from existing data
- hooking in data from Glottolog and Concepticon
- allowing for tight quality control.

it would be useful to extract functionality that can also be used to create other
types of CLDF data, in particular StructureDatasets.


## Specification

Generally, partitioning that data of a lexibank dataset into
- `raw/`
- `etc/`
- `cldf/`
seems to work well and should be kept for a more generic tool as well.
