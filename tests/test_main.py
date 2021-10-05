"""Test cases for the __main__ module."""
from overloadlib import __main__
from overloadlib import version  # type: ignore[attr-defined]


def test_main() -> None:
    """Returns the version of the package."""
    assert __main__.version_callback() == version
