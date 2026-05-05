"""
Testing
"""
def test_valid(cldf_dataset, cldf_logger):
    """Testing"""
    assert cldf_dataset.validate(log=cldf_logger)
