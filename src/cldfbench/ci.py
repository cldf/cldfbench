"""
Datasets curated with `cldfbench` are often hosted on GitHub. Thus, we can make use of the
CI (Continuous Integration) support provided by GitHub actions to ensure the consistency of the
CLDF data.
"""
CONFIG_FNAME = 'cldf-validation.yml'
CONFIG_YML = """\
name: CLDF-validation

on:
  push:
    branches: [ %s ]
  pull_request:
    branches: [ %s ]

jobs:
  build:

    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.6]

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest-cldf
    - name: Test with pytest
      run: |
%s
"""


def build_status_badge(dataset):
    """
    Format a "CLDF-validation" badge, suitable for inclusion in a markdown README.

    :param dataset: `cldfbench.Dataset` instance.
    :return: badge as markdown string or `''`.
    """
    if dataset.repo and dataset.repo.github_repo:  # pragma: no cover
        if dataset.dir.joinpath('.github/workflows', CONFIG_FNAME).exists():
            return "[![CLDF validation]" \
                "(https://github.com/{0}/workflows/CLDF-validation/badge.svg)]" \
                "(https://github.com/{0}/actions?query=workflow%3ACLDF-validation)".format(
                    dataset.repo.github_repo)
    return ''


def setup(dataset, force=False):
    yml = dataset.dir / '.github' / 'workflows' / CONFIG_FNAME
    if ((not dataset.repo) or (not dataset.repo.github_repo) or yml.exists()) and not force:
        return False  # pragma: no cover
    yml.parent.mkdir(exist_ok=True, parents=True)

    # Detect name of default branch
    try:  # pragma: no cover
        branch = 'main' if 'main' in [b.name for b in dataset.repo.repo.branches] else 'master'
    except AttributeError:
        assert force
        branch = 'master'

    tests = []
    for spec in dataset.cldf_specs_dict.values():
        tests.append('        pytest --cldf-metadata={} test.py'.format(
            dataset.cldf_dir.relative_to(dataset.dir) / spec.metadata_fname))

    yml.write_text(CONFIG_YML % (branch, branch, '\n'.join(tests)), encoding='utf8')
    return True
