"""Test cases for the __main__ module."""
from overloadlib import __main__
from overloadlib import version


def test_main():
    """Returns the version of the package."""
    assert __main__.version_callback() == version
