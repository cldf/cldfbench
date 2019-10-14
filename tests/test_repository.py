from cldfbench.repository import *


def test_Repository(repository):
    assert repository.url == 'http://example.org'
    ld = repository.json_ld(author='The Author')
    assert 'dc:author' in ld
