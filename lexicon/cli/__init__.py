"""Lexicon CLI - Command-line interface for legal document analysis."""

from typing import Annotated

import typer

from lexicon import __version__
from lexicon.cli.admin import index_command
from lexicon.cli.analyze import analyze_command
from lexicon.cli.research import research_command
from lexicon.cli.review import review_command

# Create main Typer app
app = typer.Typer(
    name="lexicon",
    help=(
        "Lexicon - AI-powered document analysis toolkit.\n\n"
        "⚠️  All outputs are informational only, not legal advice. "
        "Consult qualified professionals for legal matters."
    ),
    no_args_is_help=True,
    add_completion=False,
)


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        typer.echo(f"Lexicon CLI version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = False,
):
    """
    Lexicon - AI-powered document analysis toolkit.

    Provides AI-assisted document analysis, contract review, and research
    over your indexed documents. All outputs are informational only.

    ⚠️  DISCLAIMER: Not legal advice. Always consult qualified professionals.
    """
    pass


# Register commands
app.command(name="analyze")(analyze_command)
app.command(name="review")(review_command)
app.command(name="research")(research_command)
app.command(name="index")(index_command)


if __name__ == "__main__":
    app()
