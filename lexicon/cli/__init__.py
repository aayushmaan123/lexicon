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
    help="Lexicon - AI-powered legal document analysis and research system",
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
    Lexicon - AI-powered legal document analysis and research system.

    Provides intelligent analysis of legal documents, contract review,
    legal research capabilities, and document indexing.
    """
    pass


# Register commands
app.command(name="analyze")(analyze_command)
app.command(name="review")(review_command)
app.command(name="research")(research_command)
app.command(name="index")(index_command)


if __name__ == "__main__":
    app()
