"""__main__ of overloadlib."""
# type: ignore[attr-defined]
from overloadlib import version


def version_callback() -> str:
    """Print the version of the package."""
    print(f"version: {version}")
    return version


if __name__ == "__main__":
    version_callback()
