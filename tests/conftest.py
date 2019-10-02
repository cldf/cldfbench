import pathlib

import pytest


@pytest.fixture()
def fixtures_dir():
    return pathlib.Path(__file__).parent / 'fixtures'
