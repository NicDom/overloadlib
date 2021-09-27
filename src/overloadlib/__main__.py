# type: ignore[attr-defined]
"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """overloadlib."""


if __name__ == "__main__":
    main(prog_name="overloadlib")  # pragma: no cover
