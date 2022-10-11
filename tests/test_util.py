from cldfbench.util import iter_requirements


def test_iter_requirements():
    res = [
        spec.split('==')[0] if '==' in spec else spec.split('=')[-1]
        for spec in iter_requirements()]
    assert 'pycldf' in res
