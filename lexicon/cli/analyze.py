"""Document analysis command for Lexicon CLI."""

import json
from pathlib import Path
from typing import Annotated

import typer

from lexicon.domain.entities.document import Document, DocumentType
from lexicon.services.document_analysis import DocumentAnalysisService
from lexicon.shared.config import settings

# Try to import rich for better formatting
try:
    from rich import print as rprint
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None


def print_output(text: str, style: str = ""):
    """Print output with or without rich formatting."""
    if RICH_AVAILABLE and style:
        rprint(f"[{style}]{text}[/{style}]")
    else:
        print(text)


def print_error(text: str):
    """Print error message."""
    print_output(f"Error: {text}", "bold red")


def print_success(text: str):
    """Print success message."""
    print_output(text, "bold green")


def print_info(text: str):
    """Print info message."""
    print_output(text, "bold blue")


def analyze_command(
    file_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the document to analyze (PDF or DOCX)",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    output_format: Annotated[
        str,
        typer.Option(
            "--output-format",
            "-f",
            help="Output format: text or json",
        ),
    ] = "text",
    save_to_file: Annotated[
        Path | None,
        typer.Option(
            "--save-to-file",
            "-o",
            help="Save output to file",
        ),
    ] = None,
    document_type: Annotated[
        str,
        typer.Option(
            "--type",
            "-t",
            help="Document type hint (contract/case_law/general)",
        ),
    ] = "general",
):
    """
    Analyze a legal document using AI.

    Performs comprehensive analysis including:
    - Document summarization
    - Key points extraction
    - Party and date identification
    - Document type classification

    Example:
        lexicon analyze contract.pdf
        lexicon analyze contract.pdf --output-format json --save-to-file analysis.json
    """
    try:
        # Validate file extension
        if file_path.suffix.lower() not in [".pdf", ".docx", ".doc"]:
            print_error(
                f"Unsupported file format: {file_path.suffix}. Only PDF and DOCX are supported."
            )
            raise typer.Exit(code=1)

        # Validate output format
        if output_format not in ["text", "json"]:
            print_error(f"Invalid output format: {output_format}. Use 'text' or 'json'.")
            raise typer.Exit(code=1)

        # Validate document type
        if document_type not in ["contract", "case_law", "general"]:
            print_error(
                f"Invalid document type: {document_type}. Use 'contract', 'case_law', or 'general'."
            )
            raise typer.Exit(code=1)

        print_info(f"Analyzing document: {file_path.name}")

        # Create document entity
        doc_type_enum = DocumentType(document_type)
        document = Document(
            filename=file_path.name,
            file_path=str(file_path.absolute()),
            file_size=file_path.stat().st_size,
            document_type=doc_type_enum,
        )

        # Initialize service and analyze
        service = DocumentAnalysisService()
        parsed_doc = service.analyze_document(document)

        # Extract results from metadata
        metadata = parsed_doc.metadata

        if output_format == "json":
            # JSON output
            result = {
                "filename": document.filename,
                "document_type": metadata.get("classified_type", "general"),
                "summary": metadata.get("summary", ""),
                "key_points": metadata.get("key_points", []),
                "parties": metadata.get("parties", []),
                "dates": metadata.get("dates", []),
                "page_count": len(parsed_doc.pages),
                "character_count": len(parsed_doc.full_text),
            }

            output_text = json.dumps(result, indent=2, ensure_ascii=False)

            if save_to_file:
                save_to_file.write_text(output_text, encoding="utf-8")
                print_success(f"Analysis saved to: {save_to_file}")
            else:
                print(output_text)

        else:
            # Text output with rich formatting if available
            if RICH_AVAILABLE:
                # Create beautiful output with Rich
                console.print(
                    Panel.fit(
                        f"[bold cyan]Document Analysis: {document.filename}[/bold cyan]",
                        border_style="cyan",
                    )
                )

                # Document info
                console.print("\n[bold yellow]Document Information[/bold yellow]")
                info_table = Table(show_header=False, box=None, padding=(0, 2))
                info_table.add_row("Type:", metadata.get("classified_type", "general"))
                info_table.add_row("Pages:", str(len(parsed_doc.pages)))
                info_table.add_row("Characters:", f"{len(parsed_doc.full_text):,}")
                console.print(info_table)

                # Summary
                console.print("\n[bold yellow]Summary[/bold yellow]")
                console.print(
                    Panel(metadata.get("summary", "No summary available"), border_style="dim")
                )

                # Key Points
                key_points = metadata.get("key_points", [])
                if key_points:
                    console.print("\n[bold yellow]Key Points[/bold yellow]")
                    for i, point in enumerate(key_points, 1):
                        console.print(f"  {i}. {point}")

                # Parties
                parties = metadata.get("parties", [])
                if parties:
                    console.print("\n[bold yellow]Parties[/bold yellow]")
                    parties_table = Table(show_header=True)
                    parties_table.add_column("Name", style="cyan")
                    parties_table.add_column("Role", style="green")
                    for party in parties:
                        parties_table.add_row(
                            party.get("name", "Unknown"), party.get("role", "Unknown")
                        )
                    console.print(parties_table)

                # Dates
                dates = metadata.get("dates", [])
                if dates:
                    console.print("\n[bold yellow]Important Dates[/bold yellow]")
                    dates_table = Table(show_header=True)
                    dates_table.add_column("Date", style="cyan")
                    dates_table.add_column("Description", style="green")
                    for date in dates:
                        dates_table.add_row(
                            date.get("date", "Unknown"), date.get("description", "Unknown")
                        )
                    console.print(dates_table)

                console.print("\n[bold green]✓ Analysis complete[/bold green]\n")

            else:
                # Plain text output
                output_lines = [
                    "=" * 70,
                    f"DOCUMENT ANALYSIS: {document.filename}",
                    "=" * 70,
                    "",
                    "DOCUMENT INFORMATION",
                    "-" * 70,
                    f"Type: {metadata.get('classified_type', 'general')}",
                    f"Pages: {len(parsed_doc.pages)}",
                    f"Characters: {len(parsed_doc.full_text):,}",
                    "",
                    "SUMMARY",
                    "-" * 70,
                    metadata.get("summary", "No summary available"),
                    "",
                ]

                key_points = metadata.get("key_points", [])
                if key_points:
                    output_lines.extend(
                        [
                            "KEY POINTS",
                            "-" * 70,
                        ]
                    )
                    for i, point in enumerate(key_points, 1):
                        output_lines.append(f"{i}. {point}")
                    output_lines.append("")

                parties = metadata.get("parties", [])
                if parties:
                    output_lines.extend(
                        [
                            "PARTIES",
                            "-" * 70,
                        ]
                    )
                    for party in parties:
                        output_lines.append(
                            f"- {party.get('name', 'Unknown')} ({party.get('role', 'Unknown')})"
                        )
                    output_lines.append("")

                dates = metadata.get("dates", [])
                if dates:
                    output_lines.extend(
                        [
                            "IMPORTANT DATES",
                            "-" * 70,
                        ]
                    )
                    for date in dates:
                        output_lines.append(
                            f"- {date.get('date', 'Unknown')}: {date.get('description', 'Unknown')}"
                        )
                    output_lines.append("")

                output_lines.extend(
                    [
                        "=" * 70,
                        "✓ Analysis complete",
                        "=" * 70,
                    ]
                )

                output_text = "\n".join(output_lines)

                if save_to_file:
                    save_to_file.write_text(output_text, encoding="utf-8")
                    print_success(f"Analysis saved to: {save_to_file}")
                else:
                    print(output_text)

    except FileNotFoundError:
        print_error(f"File not found: {file_path}")
        raise typer.Exit(code=1)

    except ValueError as e:
        print_error(f"Validation error: {e}")
        raise typer.Exit(code=1)

    except Exception as e:
        print_error(f"Analysis failed: {e}")
        if settings.log_level == "DEBUG":
            import traceback

            traceback.print_exc()
        raise typer.Exit(code=1)
