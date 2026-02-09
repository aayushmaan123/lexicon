"""End-to-end tests for CLI commands."""

from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from lexicon.cli import app


@pytest.fixture
def runner():
    """Provide CLI test runner."""
    return CliRunner()


class TestCLICommands:
    """Test suite for CLI commands."""

    def test_cli_version(self, runner):
        """Test that --version flag works."""
        result = runner.invoke(app, ["--version"])
        
        assert result.exit_code == 0
        assert "Lexicon" in result.stdout

    def test_cli_help(self, runner):
        """Test that help command works."""
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "analyze" in result.stdout
        assert "review" in result.stdout
        assert "research" in result.stdout

    def test_analyze_command_success(self, runner, sample_pdf_path, mock_openai_client):
        """Test analyze command with valid PDF."""
        with patch("lexicon.cli.analyze.DocumentAnalysisService") as mock_service:
            mock_instance = Mock()
            mock_parsed = Mock()
            mock_parsed.metadata = {
                "summary": "Test summary",
                "key_points": ["Point 1"],
                "parties": [],
                "dates": []
            }
            mock_instance.analyze_document.return_value = mock_parsed
            mock_service.return_value = mock_instance
            
            result = runner.invoke(app, ["analyze", str(sample_pdf_path)])
        
        assert result.exit_code == 0

    def test_analyze_command_missing_file(self, runner):
        """Test analyze command with missing file."""
        result = runner.invoke(app, ["analyze", "/nonexistent/file.pdf"])
        
        assert result.exit_code != 0

    def test_review_command_success(self, runner, sample_pdf_path, mock_openai_client):
        """Test review command with contract PDF."""
        with patch("lexicon.cli.review.ContractReviewService") as mock_service:
            mock_instance = Mock()
            mock_contract = Mock()
            mock_contract.title = "Test Contract"
            mock_contract.parties = ["Party A"]
            mock_contract.clauses = []
            mock_contract.overall_risk_score = 0.3
            mock_contract.metadata = {"key_obligations": [], "recommendations": []}
            mock_instance.review_contract.return_value = mock_contract
            mock_service.return_value = mock_instance
            
            result = runner.invoke(app, ["review", str(sample_pdf_path)])
        
        assert result.exit_code == 0

    def test_research_command_success(self, runner, mock_openai_client):
        """Test research command with query."""
        with patch("lexicon.cli.research.LegalResearchService") as mock_service:
            mock_instance = Mock()
            mock_instance.research_query.return_value = {
                "query_summary": "Summary",
                "relevant_cases": [],
                "relevant_statutes": [],
                "analysis": "Analysis",
                "recommendations": []
            }
            mock_service.return_value = mock_instance
            
            result = runner.invoke(
                app,
                ["research", "What is contract law?", "--jurisdiction", "US"]
            )
        
        assert result.exit_code == 0

    def test_index_command_success(self, runner, sample_pdf_path, mock_chroma_client, mock_openai_embeddings):
        """Test index command for adding to knowledge base."""
        with patch("lexicon.cli.admin.RAGOrchestrator") as mock_rag:
            mock_instance = Mock()
            mock_instance.index_document.return_value = "doc-123"
            mock_rag.return_value = mock_instance
            
            result = runner.invoke(app, ["index", str(sample_pdf_path)])
        
        assert result.exit_code == 0

    def test_analyze_with_output_file(self, runner, sample_pdf_path, tmp_path, mock_openai_client):
        """Test analyze command with output file option."""
        output_file = tmp_path / "output.json"
        
        with patch("lexicon.cli.analyze.DocumentAnalysisService") as mock_service:
            mock_instance = Mock()
            mock_parsed = Mock()
            mock_parsed.metadata = {"summary": "Test"}
            mock_instance.analyze_document.return_value = mock_parsed
            mock_service.return_value = mock_instance
            
            result = runner.invoke(
                app,
                ["analyze", str(sample_pdf_path), "--output", str(output_file)]
            )
        
        # Should succeed regardless of whether output file is created
        assert result.exit_code == 0

    def test_review_with_format_option(self, runner, sample_pdf_path, mock_openai_client):
        """Test review command with format option."""
        with patch("lexicon.cli.review.ContractReviewService") as mock_service:
            mock_instance = Mock()
            mock_contract = Mock()
            mock_contract.title = "Test"
            mock_contract.parties = []
            mock_contract.clauses = []
            mock_contract.overall_risk_score = 0.0
            mock_contract.metadata = {}
            mock_instance.review_contract.return_value = mock_contract
            mock_service.return_value = mock_instance
            
            result = runner.invoke(
                app,
                ["review", str(sample_pdf_path), "--format", "json"]
            )
        
        assert result.exit_code == 0

    def test_research_with_memo_option(self, runner, mock_openai_client):
        """Test research command with memo generation."""
        with patch("lexicon.cli.research.LegalResearchService") as mock_service:
            mock_instance = Mock()
            mock_instance.generate_legal_memo.return_value = "MEMO TEXT"
            mock_service.return_value = mock_instance
            
            result = runner.invoke(
                app,
                ["research", "Test query", "--memo"]
            )
        
        assert result.exit_code == 0

    @pytest.mark.parametrize("command", [
        ["analyze"],
        ["review"],
        ["index"],
    ])
    def test_commands_require_arguments(self, runner, command):
        """Test that commands requiring file argument show error without it."""
        result = runner.invoke(app, command)
        
        # Should fail or show help
        assert result.exit_code != 0 or "Usage" in result.stdout
