"""__main__ of overloadlib."""
from typing import Any

from overloadlib import version  # type: ignore[attr-defined]


def version_callback() -> Any:
    """Print the version of the package."""
    print(f"version: {version}")
    return version


if __name__ == "__main__":  # pragma: no cover
    version_callback()
