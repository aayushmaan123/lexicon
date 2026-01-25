"""Contract review command for Lexicon CLI."""

import json
from pathlib import Path
from typing import Annotated

import typer

from lexicon.domain.entities.document import Document, DocumentType
from lexicon.services.contract_review import ContractReviewService
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


def get_risk_color(severity: str) -> str:
    """Get color for risk severity level."""
    severity_lower = severity.lower()
    if severity_lower == "high":
        return "red"
    elif severity_lower == "medium":
        return "yellow"
    elif severity_lower == "low":
        return "green"
    else:
        return "white"


def review_command(
    file_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the contract to review (PDF or DOCX)",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    focus: Annotated[
        str,
        typer.Option(
            "--focus",
            "-f",
            help="Focus area: all, risks, clauses, or obligations",
        ),
    ] = "all",
    output_format: Annotated[
        str,
        typer.Option(
            "--output-format",
            "-o",
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
):
    """
    Review a contract using AI.

    Performs comprehensive contract review including:
    - Risk assessment (legal, financial, operational)
    - Clause extraction and analysis
    - Unusual clause detection
    - Party and obligation identification

    Example:
        lexicon review contract.pdf
        lexicon review contract.pdf --focus risks
        lexicon review contract.pdf --output-format json --save-to review.json
    """
    try:
        # Validate file extension
        if file_path.suffix.lower() not in [".pdf", ".docx", ".doc"]:
            print_error(
                f"Unsupported file format: {file_path.suffix}. Only PDF and DOCX are supported."
            )
            raise typer.Exit(code=1)

        # Validate focus
        if focus not in ["all", "risks", "clauses", "obligations"]:
            print_error(f"Invalid focus: {focus}. Use 'all', 'risks', 'clauses', or 'obligations'.")
            raise typer.Exit(code=1)

        # Validate output format
        if output_format not in ["text", "json"]:
            print_error(f"Invalid output format: {output_format}. Use 'text' or 'json'.")
            raise typer.Exit(code=1)

        print_info(f"Reviewing contract: {file_path.name}")

        # Create document entity
        document = Document(
            filename=file_path.name,
            file_path=str(file_path.absolute()),
            file_size=file_path.stat().st_size,
            document_type=DocumentType.CONTRACT,
        )

        # Initialize service and review
        service = ContractReviewService()
        contract = service.review_contract(document)

        if output_format == "json":
            # JSON output
            result = {
                "filename": document.filename,
                "contract_type": contract.contract_type,
                "parties": [
                    {
                        "name": p.name,
                        "type": p.type,
                        "role": p.role,
                    }
                    for p in contract.parties
                ],
                "risks": [
                    {
                        "severity": r.severity,
                        "category": r.category,
                        "description": r.description,
                        "recommendation": r.recommendation,
                    }
                    for r in contract.risks
                ]
                if focus in ["all", "risks"]
                else [],
                "clauses": [
                    {
                        "type": c.type,
                        "title": c.title,
                        "content": c.content,
                        "unusual": c.unusual,
                        "obligations": c.obligations,
                    }
                    for c in contract.clauses
                ]
                if focus in ["all", "clauses", "obligations"]
                else [],
                "effective_date": contract.effective_date.isoformat()
                if contract.effective_date
                else None,
                "expiration_date": contract.expiration_date.isoformat()
                if contract.expiration_date
                else None,
                "jurisdiction": contract.jurisdiction,
                "governing_law": contract.governing_law,
                "overall_assessment": contract.overall_assessment,
            }

            output_text = json.dumps(result, indent=2, ensure_ascii=False)

            if save_to_file:
                save_to_file.write_text(output_text, encoding="utf-8")
                print_success(f"Review saved to: {save_to_file}")
            else:
                print(output_text)

        else:
            # Text output with rich formatting if available
            if RICH_AVAILABLE:
                # Create beautiful output with Rich
                console.print(
                    Panel.fit(
                        f"[bold cyan]Contract Review: {document.filename}[/bold cyan]",
                        border_style="cyan",
                    )
                )

                # Contract info
                console.print("\n[bold yellow]Contract Information[/bold yellow]")
                info_table = Table(show_header=False, box=None, padding=(0, 2))
                info_table.add_row("Type:", contract.contract_type)
                if contract.jurisdiction:
                    info_table.add_row("Jurisdiction:", contract.jurisdiction)
                if contract.governing_law:
                    info_table.add_row("Governing Law:", contract.governing_law)
                if contract.effective_date:
                    info_table.add_row(
                        "Effective Date:", contract.effective_date.strftime("%Y-%m-%d")
                    )
                if contract.expiration_date:
                    info_table.add_row(
                        "Expiration Date:", contract.expiration_date.strftime("%Y-%m-%d")
                    )
                console.print(info_table)

                # Parties
                if contract.parties:
                    console.print("\n[bold yellow]Parties[/bold yellow]")
                    parties_table = Table(show_header=True)
                    parties_table.add_column("Name", style="cyan")
                    parties_table.add_column("Type", style="magenta")
                    parties_table.add_column("Role", style="green")
                    for party in contract.parties:
                        parties_table.add_row(party.name, party.type, party.role)
                    console.print(parties_table)

                # Overall assessment
                console.print("\n[bold yellow]Overall Assessment[/bold yellow]")
                console.print(Panel(contract.overall_assessment, border_style="dim"))

                # Risks
                if focus in ["all", "risks"] and contract.risks:
                    console.print("\n[bold yellow]Risk Assessment[/bold yellow]")
                    risks_table = Table(show_header=True)
                    risks_table.add_column("Severity", style="bold")
                    risks_table.add_column("Category", style="cyan")
                    risks_table.add_column("Description", style="white")
                    risks_table.add_column("Recommendation", style="green")

                    for risk in sorted(
                        contract.risks,
                        key=lambda r: {"high": 0, "medium": 1, "low": 2}.get(r.severity.lower(), 3),
                    ):
                        color = get_risk_color(risk.severity)
                        risks_table.add_row(
                            f"[{color}]{risk.severity.upper()}[/{color}]",
                            risk.category,
                            risk.description[:100] + "..."
                            if len(risk.description) > 100
                            else risk.description,
                            risk.recommendation[:100] + "..."
                            if len(risk.recommendation) > 100
                            else risk.recommendation,
                        )
                    console.print(risks_table)

                # Clauses
                if focus in ["all", "clauses"]:
                    console.print("\n[bold yellow]Contract Clauses[/bold yellow]")
                    console.print(f"Total clauses: {len(contract.clauses)}")

                    # Show unusual clauses
                    unusual_clauses = [c for c in contract.clauses if c.unusual]
                    if unusual_clauses:
                        console.print(
                            f"\n[bold red]⚠ Unusual Clauses Detected: {len(unusual_clauses)}[/bold red]"
                        )
                        for clause in unusual_clauses:
                            console.print(
                                Panel(
                                    f"[bold]{clause.title}[/bold]\n\n{clause.content[:300]}{'...' if len(clause.content) > 300 else ''}",
                                    title=f"[red]{clause.type}[/red]",
                                    border_style="red",
                                )
                            )

                    # Show sample of clauses
                    if len(contract.clauses) <= 5:
                        console.print("\n[bold]All Clauses:[/bold]")
                        for clause in contract.clauses:
                            style = "red" if clause.unusual else "dim"
                            console.print(
                                Panel(
                                    f"[bold]{clause.title}[/bold]\n\n{clause.content[:200]}{'...' if len(clause.content) > 200 else ''}",
                                    title=f"[{style}]{clause.type}[/{style}]",
                                    border_style=style,
                                )
                            )
                    else:
                        console.print(
                            f"\n[dim]({len(contract.clauses)} clauses found - use --focus clauses for full list)[/dim]"
                        )

                # Obligations
                if focus in ["all", "obligations"]:
                    all_obligations = []
                    for clause in contract.clauses:
                        if clause.obligations:
                            all_obligations.extend(clause.obligations)

                    if all_obligations:
                        console.print(
                            f"\n[bold yellow]Key Obligations ({len(all_obligations)})[/bold yellow]"
                        )
                        for i, obligation in enumerate(all_obligations[:10], 1):
                            console.print(f"  {i}. {obligation}")
                        if len(all_obligations) > 10:
                            console.print(f"  [dim]... and {len(all_obligations) - 10} more[/dim]")

                console.print("\n[bold green]✓ Review complete[/bold green]\n")

            else:
                # Plain text output
                output_lines = [
                    "=" * 70,
                    f"CONTRACT REVIEW: {document.filename}",
                    "=" * 70,
                    "",
                    "CONTRACT INFORMATION",
                    "-" * 70,
                    f"Type: {contract.contract_type}",
                ]

                if contract.jurisdiction:
                    output_lines.append(f"Jurisdiction: {contract.jurisdiction}")
                if contract.governing_law:
                    output_lines.append(f"Governing Law: {contract.governing_law}")
                if contract.effective_date:
                    output_lines.append(
                        f"Effective Date: {contract.effective_date.strftime('%Y-%m-%d')}"
                    )
                if contract.expiration_date:
                    output_lines.append(
                        f"Expiration Date: {contract.expiration_date.strftime('%Y-%m-%d')}"
                    )

                output_lines.extend(["", "PARTIES", "-" * 70])
                for party in contract.parties:
                    output_lines.append(f"- {party.name} ({party.type}): {party.role}")

                output_lines.extend(
                    ["", "OVERALL ASSESSMENT", "-" * 70, contract.overall_assessment, ""]
                )

                if focus in ["all", "risks"] and contract.risks:
                    output_lines.extend(["RISK ASSESSMENT", "-" * 70])
                    for risk in sorted(
                        contract.risks,
                        key=lambda r: {"high": 0, "medium": 1, "low": 2}.get(r.severity.lower(), 3),
                    ):
                        risk_marker = (
                            "!!!"
                            if risk.severity.lower() == "high"
                            else "!!"
                            if risk.severity.lower() == "medium"
                            else "!"
                        )
                        output_lines.extend(
                            [
                                f"\n[{risk_marker} {risk.severity.upper()} - {risk.category}]",
                                f"Description: {risk.description}",
                                f"Recommendation: {risk.recommendation}",
                            ]
                        )
                    output_lines.append("")

                if focus in ["all", "clauses"]:
                    unusual_clauses = [c for c in contract.clauses if c.unusual]
                    output_lines.extend(
                        [
                            "CONTRACT CLAUSES",
                            "-" * 70,
                            f"Total clauses: {len(contract.clauses)}",
                            f"Unusual clauses: {len(unusual_clauses)}",
                            "",
                        ]
                    )

                    if unusual_clauses:
                        output_lines.append("UNUSUAL CLAUSES:")
                        for clause in unusual_clauses:
                            output_lines.extend(
                                [
                                    f"\n⚠ {clause.title} ({clause.type})",
                                    f"   {clause.content[:200]}{'...' if len(clause.content) > 200 else ''}",
                                ]
                            )
                        output_lines.append("")

                if focus in ["all", "obligations"]:
                    all_obligations = []
                    for clause in contract.clauses:
                        if clause.obligations:
                            all_obligations.extend(clause.obligations)

                    if all_obligations:
                        output_lines.extend(
                            [
                                "KEY OBLIGATIONS",
                                "-" * 70,
                            ]
                        )
                        for i, obligation in enumerate(all_obligations[:10], 1):
                            output_lines.append(f"{i}. {obligation}")
                        if len(all_obligations) > 10:
                            output_lines.append(f"... and {len(all_obligations) - 10} more")
                        output_lines.append("")

                output_lines.extend(
                    [
                        "=" * 70,
                        "✓ Review complete",
                        "=" * 70,
                    ]
                )

                output_text = "\n".join(output_lines)

                if save_to_file:
                    save_to_file.write_text(output_text, encoding="utf-8")
                    print_success(f"Review saved to: {save_to_file}")
                else:
                    print(output_text)

    except FileNotFoundError:
        print_error(f"File not found: {file_path}")
        raise typer.Exit(code=1)

    except ValueError as e:
        print_error(f"Validation error: {e}")
        raise typer.Exit(code=1)

    except Exception as e:
        print_error(f"Review failed: {e}")
        if settings.log_level == "DEBUG":
            import traceback

            traceback.print_exc()
        raise typer.Exit(code=1)
