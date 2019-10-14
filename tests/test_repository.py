from cldfbench.repository import *


def test_Repository(repository):
    assert repository.url == 'https://github.com/org/repo'
    ld = repository.json_ld(author='The Author')
    assert 'dc:author' in ld
    assert repository.github_repo == 'org/repo'

