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
        python-version: [3.12]

    steps:
    - uses: actions/checkout@v6
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v6
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
            repo_url = f"https://github.com/{dataset.repo.github_repo}"
            return f"[![CLDF validation]" \
                f"({repo_url}/workflows/CLDF-validation/badge.svg)]" \
                f"({repo_url}/actions?query=workflow%3ACLDF-validation)"
    return ''


def setup(dataset, force=False) -> bool:
    """Tries to write a CLDF test workflow to the .github directory."""
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
        rel_md_path = dataset.cldf_dir.relative_to(dataset.dir) / spec.metadata_fname
        tests.append(f'        pytest --cldf-metadata={rel_md_path} test.py')

    yml.write_text(CONFIG_YML % (branch, branch, '\n'.join(tests)), encoding='utf8')
    return True
