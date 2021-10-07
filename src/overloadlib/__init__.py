# type: ignore[attr-defined]
"""A python package to implement overloading of functions in python."""

import sys

from overloadlib.overloadlib import func_versions_info
from overloadlib.overloadlib import overload
from overloadlib.overloadlib import override

__all__ = ["overload", "override", "func_versions_info"]


if sys.version_info >= (3, 8):
    from importlib import metadata as importlib_metadata
else:  # pragma: no cover
    import importlib_metadata


def get_version() -> str:
    """Returns the version of the package.

    Returns:
        str: The version of the package.
    """
    try:
        return str(importlib_metadata.version(__name__))
    except importlib_metadata.PackageNotFoundError:  # pragma: no cover
        return "unknown"


version: str = get_version()
