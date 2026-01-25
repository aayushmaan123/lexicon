"""Legal research command for Lexicon CLI."""

import json
from pathlib import Path
from typing import Annotated

import typer

from lexicon.domain.entities.legal_research import QueryType, ResearchQuery
from lexicon.services.legal_research import LegalResearchService
from lexicon.shared.config import settings

# Try to import rich for better formatting
try:
    from rich import print as rprint
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
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


def research_command(
    query: Annotated[
        str,
        typer.Argument(
            help="Natural language legal research query",
        ),
    ],
    jurisdiction: Annotated[
        str | None,
        typer.Option(
            "--jurisdiction",
            "-j",
            help="Jurisdiction to focus on (e.g., 'California', 'Federal')",
        ),
    ] = None,
    query_type: Annotated[
        str,
        typer.Option(
            "--query-type",
            "-t",
            help="Query type: general, contract, or case_law",
        ),
    ] = "general",
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
            "--save-to",
            "-s",
            help="Save output to file",
        ),
    ] = None,
    show_sources: Annotated[
        bool,
        typer.Option(
            "--show-sources/--no-sources",
            help="Show source documents",
        ),
    ] = True,
):
    """
    Perform legal research using AI and RAG.

    Searches through indexed legal documents and provides:
    - Comprehensive answer to your query
    - Relevant citations
    - Source documents with relevance scores
    - Confidence and relevance metrics

    Example:
        lexicon research "What are the elements of breach of contract?"
        lexicon research "Statute of limitations for personal injury" --jurisdiction California
        lexicon research "Case law on fair use" --query-type case_law
    """
    try:
        # Validate query type
        if query_type not in ["general", "contract", "case_law"]:
            print_error(
                f"Invalid query type: {query_type}. Use 'general', 'contract', or 'case_law'."
            )
            raise typer.Exit(code=1)

        # Validate output format
        if output_format not in ["text", "json"]:
            print_error(f"Invalid output format: {output_format}. Use 'text' or 'json'.")
            raise typer.Exit(code=1)

        # Show progress
        if RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Researching...", total=None)

                # Create research query
                query_type_enum = QueryType.GENERAL
                if query_type == "contract":
                    query_type_enum = QueryType.CONTRACT
                elif query_type == "case_law":
                    query_type_enum = QueryType.CASE_LAW

                research_query = ResearchQuery(
                    query_text=query,
                    jurisdiction=jurisdiction,
                    query_type=query_type_enum,
                )

                # Initialize service and research
                service = LegalResearchService()
                result = service.research(research_query)

                progress.update(task, completed=True)
        else:
            print_info("Researching...")

            # Create research query
            query_type_enum = QueryType.GENERAL
            if query_type == "contract":
                query_type_enum = QueryType.CONTRACT
            elif query_type == "case_law":
                query_type_enum = QueryType.CASE_LAW

            research_query = ResearchQuery(
                query_text=query,
                jurisdiction=jurisdiction,
                query_type=query_type_enum,
            )

            # Initialize service and research
            service = LegalResearchService()
            result = service.research(research_query)

        if output_format == "json":
            # JSON output
            output_data = {
                "query": query,
                "jurisdiction": jurisdiction,
                "query_type": query_type,
                "answer": result.answer,
                "confidence_score": result.confidence_score,
                "relevance_score": result.relevance_score,
                "citations": result.citations,
                "sources": [
                    {
                        "text": s.get("text", ""),
                        "score": s.get("score", 0),
                        "relevance_score": s.get("relevance_score", 0),
                        "metadata": s.get("metadata", {}),
                    }
                    for s in result.sources
                ]
                if show_sources
                else [],
            }

            output_text = json.dumps(output_data, indent=2, ensure_ascii=False)

            if save_to_file:
                save_to_file.write_text(output_text, encoding="utf-8")
                print_success(f"Research results saved to: {save_to_file}")
            else:
                print(output_text)

        else:
            # Text output with rich formatting if available
            if RICH_AVAILABLE:
                # Create beautiful output with Rich
                console.print(
                    Panel.fit("[bold cyan]Legal Research Results[/bold cyan]", border_style="cyan")
                )

                # Query info
                console.print("\n[bold yellow]Query[/bold yellow]")
                console.print(f"  {query}")
                if jurisdiction:
                    console.print(f"  [dim]Jurisdiction: {jurisdiction}[/dim]")

                # Scores
                console.print("\n[bold yellow]Analysis Metrics[/bold yellow]")
                scores_table = Table(show_header=False, box=None, padding=(0, 2))

                # Color code confidence
                conf_color = (
                    "green"
                    if result.confidence_score >= 0.7
                    else "yellow"
                    if result.confidence_score >= 0.4
                    else "red"
                )
                rel_color = (
                    "green"
                    if result.relevance_score >= 0.7
                    else "yellow"
                    if result.relevance_score >= 0.4
                    else "red"
                )

                scores_table.add_row(
                    "Confidence:", f"[{conf_color}]{result.confidence_score:.1%}[/{conf_color}]"
                )
                scores_table.add_row(
                    "Relevance:", f"[{rel_color}]{result.relevance_score:.1%}[/{rel_color}]"
                )
                scores_table.add_row("Sources:", str(len(result.sources)))
                console.print(scores_table)

                # Answer
                console.print("\n[bold yellow]Answer[/bold yellow]")
                console.print(Panel(result.answer, border_style="green"))

                # Citations
                if result.citations:
                    console.print(
                        f"\n[bold yellow]Citations ({len(result.citations)})[/bold yellow]"
                    )
                    for i, citation in enumerate(result.citations[:10], 1):
                        console.print(f"  {i}. {citation}")
                    if len(result.citations) > 10:
                        console.print(f"  [dim]... and {len(result.citations) - 10} more[/dim]")

                # Sources
                if show_sources and result.sources:
                    console.print(
                        f"\n[bold yellow]Source Documents ({len(result.sources)})[/bold yellow]"
                    )
                    sources_table = Table(show_header=True)
                    sources_table.add_column("#", style="cyan", width=3)
                    sources_table.add_column("Source", style="cyan")
                    sources_table.add_column("Score", style="green", width=8)
                    sources_table.add_column("Relevance", style="yellow", width=10)
                    sources_table.add_column("Preview", style="white")

                    for i, source in enumerate(result.sources[:5], 1):
                        metadata = source.get("metadata", {})
                        filename = metadata.get("filename", "Unknown")
                        score = source.get("score", 0)
                        relevance = source.get("relevance_score", 0)
                        text = source.get("text", "")
                        preview = text[:80] + "..." if len(text) > 80 else text

                        sources_table.add_row(
                            str(i),
                            filename,
                            f"{score:.3f}",
                            f"{relevance:.1%}",
                            preview,
                        )

                    console.print(sources_table)

                    if len(result.sources) > 5:
                        console.print(
                            f"  [dim]... and {len(result.sources) - 5} more sources[/dim]"
                        )

                console.print("\n[bold green]✓ Research complete[/bold green]\n")

            else:
                # Plain text output
                output_lines = [
                    "=" * 70,
                    "LEGAL RESEARCH RESULTS",
                    "=" * 70,
                    "",
                    "QUERY",
                    "-" * 70,
                    query,
                ]

                if jurisdiction:
                    output_lines.append(f"Jurisdiction: {jurisdiction}")

                output_lines.extend(
                    [
                        "",
                        "ANALYSIS METRICS",
                        "-" * 70,
                        f"Confidence: {result.confidence_score:.1%}",
                        f"Relevance: {result.relevance_score:.1%}",
                        f"Sources: {len(result.sources)}",
                        "",
                        "ANSWER",
                        "-" * 70,
                        result.answer,
                        "",
                    ]
                )

                if result.citations:
                    output_lines.extend(["CITATIONS", "-" * 70])
                    for i, citation in enumerate(result.citations[:10], 1):
                        output_lines.append(f"{i}. {citation}")
                    if len(result.citations) > 10:
                        output_lines.append(f"... and {len(result.citations) - 10} more")
                    output_lines.append("")

                if show_sources and result.sources:
                    output_lines.extend(
                        [
                            "SOURCE DOCUMENTS",
                            "-" * 70,
                        ]
                    )
                    for i, source in enumerate(result.sources[:5], 1):
                        metadata = source.get("metadata", {})
                        filename = metadata.get("filename", "Unknown")
                        score = source.get("score", 0)
                        relevance = source.get("relevance_score", 0)
                        text = source.get("text", "")
                        preview = text[:100] + "..." if len(text) > 100 else text

                        output_lines.extend(
                            [
                                f"\n{i}. {filename}",
                                f"   Score: {score:.3f} | Relevance: {relevance:.1%}",
                                f"   {preview}",
                            ]
                        )

                    if len(result.sources) > 5:
                        output_lines.append(f"\n... and {len(result.sources) - 5} more sources")
                    output_lines.append("")

                output_lines.extend(
                    [
                        "=" * 70,
                        "✓ Research complete",
                        "=" * 70,
                    ]
                )

                output_text = "\n".join(output_lines)

                if save_to_file:
                    save_to_file.write_text(output_text, encoding="utf-8")
                    print_success(f"Research results saved to: {save_to_file}")
                else:
                    print(output_text)

    except ValueError as e:
        print_error(f"Validation error: {e}")
        raise typer.Exit(code=1)

    except Exception as e:
        print_error(f"Research failed: {e}")
        if settings.log_level == "DEBUG":
            import traceback

            traceback.print_exc()
        raise typer.Exit(code=1)
