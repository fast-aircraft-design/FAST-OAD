"""
Just checking that Pelix framework is automatically started
"""

from pelix.framework import FrameworkFactory


def test_pelix_framework_is_started():
    """
    Tests that Pelix framework is automatically started
    """

    assert FrameworkFactory.is_framework_running()
