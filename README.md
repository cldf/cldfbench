# cldfbench
Tooling to create CLDF datasets from existing data


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
