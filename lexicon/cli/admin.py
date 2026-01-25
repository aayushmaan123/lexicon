"""Document indexing command for Lexicon CLI."""

from pathlib import Path
from typing import Annotated

import typer

from lexicon.domain.entities.document import Document, DocumentType
from lexicon.services.rag_orchestrator import RAGOrchestrator
from lexicon.shared.config import settings

# Try to import rich for better formatting
try:
    from rich import print as rprint
    from rich.console import Console
    from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn
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


def collect_files(
    path: Path,
    recursive: bool,
    file_types: list[str],
) -> list[Path]:
    """Collect files to index."""
    files = []

    if path.is_file():
        # Single file
        if path.suffix.lower().lstrip(".") in file_types or not file_types:
            files.append(path)
    elif path.is_dir():
        # Directory
        if recursive:
            for ext in file_types:
                files.extend(path.rglob(f"*.{ext}"))
        else:
            for ext in file_types:
                files.extend(path.glob(f"*.{ext}"))

    return sorted(set(files))


def index_command(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to document or directory to index",
            exists=True,
        ),
    ],
    recursive: Annotated[
        bool,
        typer.Option(
            "--recursive",
            "-r",
            help="Recursively index all files in subdirectories",
        ),
    ] = False,
    file_types: Annotated[
        str | None,
        typer.Option(
            "--file-types",
            "-t",
            help="Comma-separated list of file extensions (e.g., 'pdf,docx')",
        ),
    ] = "pdf,docx",
    document_type: Annotated[
        str,
        typer.Option(
            "--document-type",
            "-d",
            help="Document type: contract, case_law, or general",
        ),
    ] = "general",
    skip_errors: Annotated[
        bool,
        typer.Option(
            "--skip-errors/--no-skip-errors",
            help="Continue indexing even if some documents fail",
        ),
    ] = True,
):
    """
    Index documents for RAG-based search.

    Indexes documents into the vector database for later retrieval.
    Supports PDF and DOCX files.

    Example:
        lexicon index documents/
        lexicon index documents/ --recursive --file-types pdf
        lexicon index contract.pdf --document-type contract
    """
    try:
        # Validate document type
        if document_type not in ["contract", "case_law", "general"]:
            print_error(
                f"Invalid document type: {document_type}. Use 'contract', 'case_law', or 'general'."
            )
            raise typer.Exit(code=1)

        # Parse file types
        file_types_list = (
            [ft.strip().lower().lstrip(".") for ft in file_types.split(",")] if file_types else []
        )

        # Collect files
        print_info(f"Scanning for files in: {path}")
        files = collect_files(path, recursive, file_types_list)

        if not files:
            print_error("No files found to index.")
            raise typer.Exit(code=1)

        print_info(f"Found {len(files)} file(s) to index")

        # Initialize RAG orchestrator
        orchestrator = RAGOrchestrator()
        doc_type_enum = DocumentType(document_type)

        # Track statistics
        stats = {
            "total": len(files),
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "total_chunks": 0,
            "total_cost": 0.0,
        }
        failed_files = []

        # Index files with progress bar
        if RICH_AVAILABLE:
            with Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Indexing documents...", total=len(files))

                for file_path in files:
                    try:
                        # Create document entity
                        document = Document(
                            filename=file_path.name,
                            file_path=str(file_path.absolute()),
                            file_size=file_path.stat().st_size,
                            document_type=doc_type_enum,
                        )

                        # Index document
                        progress.update(task, description=f"Indexing: {file_path.name}")
                        orchestrator.index_document(document)

                        stats["success"] += 1

                        # Get updated stats
                        rag_stats = orchestrator.get_stats()
                        stats["total_cost"] = rag_stats["total_cost"]

                    except Exception as e:
                        stats["failed"] += 1
                        failed_files.append((file_path.name, str(e)))

                        if not skip_errors:
                            progress.stop()
                            print_error(f"Failed to index {file_path.name}: {e}")
                            raise typer.Exit(code=1)

                    progress.advance(task)

                progress.update(task, description="Indexing complete")
        else:
            # Simple progress without rich
            for i, file_path in enumerate(files, 1):
                print(f"Indexing {i}/{len(files)}: {file_path.name}...", end="", flush=True)

                try:
                    # Create document entity
                    document = Document(
                        filename=file_path.name,
                        file_path=str(file_path.absolute()),
                        file_size=file_path.stat().st_size,
                        document_type=doc_type_enum,
                    )

                    # Index document
                    orchestrator.index_document(document)

                    stats["success"] += 1
                    print(" ✓")

                    # Get updated stats
                    rag_stats = orchestrator.get_stats()
                    stats["total_cost"] = rag_stats["total_cost"]

                except Exception as e:
                    stats["failed"] += 1
                    failed_files.append((file_path.name, str(e)))
                    print(f" ✗ ({e})")

                    if not skip_errors:
                        print_error(f"Failed to index {file_path.name}: {e}")
                        raise typer.Exit(code=1)

        # Display summary
        print()
        if RICH_AVAILABLE:
            console.print("\n[bold yellow]Indexing Summary[/bold yellow]")

            summary_table = Table(show_header=False, box=None, padding=(0, 2))
            summary_table.add_row("Total files:", str(stats["total"]))
            summary_table.add_row("Successfully indexed:", f"[green]{stats['success']}[/green]")

            if stats["failed"] > 0:
                summary_table.add_row("Failed:", f"[red]{stats['failed']}[/red]")

            # Get final stats from orchestrator
            final_stats = orchestrator.get_stats()
            vector_stats = final_stats.get("vector_store_stats", {})

            summary_table.add_row(
                "Total chunks created:", str(vector_stats.get("total_documents", "N/A"))
            )
            summary_table.add_row(
                "Embedding tokens:", f"{final_stats.get('total_embedding_tokens', 0):,}"
            )
            summary_table.add_row(
                "Total cost:", f"[cyan]${final_stats.get('total_cost', 0):.4f}[/cyan]"
            )

            console.print(summary_table)

            # Show failed files if any
            if failed_files:
                console.print("\n[bold red]Failed Files:[/bold red]")
                for filename, error in failed_files:
                    console.print(f"  • {filename}: [red]{error}[/red]")

            if stats["success"] > 0:
                console.print("\n[bold green]✓ Indexing complete[/bold green]\n")
            else:
                console.print("\n[bold red]✗ Indexing failed[/bold red]\n")

        else:
            # Plain text summary
            print("=" * 70)
            print("INDEXING SUMMARY")
            print("=" * 70)
            print(f"Total files: {stats['total']}")
            print(f"Successfully indexed: {stats['success']}")

            if stats["failed"] > 0:
                print(f"Failed: {stats['failed']}")

            # Get final stats from orchestrator
            final_stats = orchestrator.get_stats()
            vector_stats = final_stats.get("vector_store_stats", {})

            print(f"Total chunks created: {vector_stats.get('total_documents', 'N/A')}")
            print(f"Embedding tokens: {final_stats.get('total_embedding_tokens', 0):,}")
            print(f"Total cost: ${final_stats.get('total_cost', 0):.4f}")

            # Show failed files if any
            if failed_files:
                print("\nFailed Files:")
                for filename, error in failed_files:
                    print(f"  • {filename}: {error}")

            print("=" * 70)
            if stats["success"] > 0:
                print("✓ Indexing complete")
            else:
                print("✗ Indexing failed")
            print("=" * 70)

        # Exit with error code if any files failed and not skipping errors
        if stats["failed"] > 0 and not skip_errors:
            raise typer.Exit(code=1)

    except typer.Exit:
        raise

    except Exception as e:
        print_error(f"Indexing failed: {e}")
        if settings.log_level == "DEBUG":
            import traceback

            traceback.print_exc()
        raise typer.Exit(code=1)
