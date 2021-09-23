"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """pyoverload."""


if __name__ == "__main__":
    main(prog_name="pyoverload")  # pragma: no cover
