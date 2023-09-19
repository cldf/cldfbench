# Changes

## [Unreleased]

- Added method to Glottolog API to retrieve language-level languoids, e.g.
  to supplement coordinates for dialects.
- Bugfix: Handle multi-line citations properly when creating README.md
- Drop Python 3.7 compatibility.

### Backwards incompatibility

`DataDir.download` treated its `fname` argument inconsistently. This is
fixed now, resulting in changed behaviour when `fname` was of type `str` and
contained a `/`. In this case, `fname` is now assumed to be an absolute
path or a path relative to `cwd` and **not** relative to the `DataDir` instance.

Thus, `DataDir.download` now interprets `fname` in the same way as all other
`DataDir` methods accepting a `fname` argument.


## [1.13.0] - 2022-10-29

- Add support for writing zipped data tables (requirs pycldf >= 1.29).


## [1.12.0] - 2022-07-19

- Don't use `pkg_resources` to access entry points.
- Compatibility with `csvw` v3.


## [1.11.0] - 2022-05-26

- Drop py3.6 compat.
- Extend `add_catalog_spec` to allow for optional catalog instantiation.


## [1.10.0] - 2022-03-25

- Add option to set random seed to `cldfbench` command.


## [1.9.0] - 2021-11-25

- py 3.10 support

