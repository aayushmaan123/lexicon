"""End-to-end tests for complete pipeline scenarios."""

from unittest.mock import Mock, patch

import pytest


class TestFullPipeline:
    """Test suite for complete end-to-end workflows."""

    def test_complete_document_analysis_pipeline(
        self, sample_pdf_path, mock_openai_client, mock_chroma_client
    ):
        """Test complete pipeline: upload -> parse -> analyze -> index -> query."""
        from lexicon.domain.entities.document import Document, DocumentType
        from lexicon.services.document_analysis import DocumentAnalysisService
        from lexicon.services.rag_orchestrator import RAGOrchestrator
        
        # Step 1: Create document
        document = Document(
            document_id="e2e-doc-1",
            filename="sample.pdf",
            file_path=str(sample_pdf_path),
            document_type=DocumentType.GENERAL,
            uploaded_at=None,
            file_size=1024,
        )
        
        # Step 2: Analyze document
        with patch("lexicon.services.document_analysis.OpenAIProvider") as mock_provider:
            mock_instance = Mock()
            mock_instance.generate.return_value = "Analysis result"
            mock_instance.generate_structured.return_value = Mock(
                parties=[],
                dates=[]
            )
            mock_provider.return_value = mock_instance
            
            analysis_service = DocumentAnalysisService()
            parsed_doc = analysis_service.analyze_document(document)
        
        assert parsed_doc is not None
        assert parsed_doc.full_text is not None
        
        # Step 3: Index for RAG
        with patch("openai.OpenAI"):
            rag = RAGOrchestrator(openai_api_key="test-key")
            doc_id = rag.index_document(document)
        
        assert doc_id is not None

    def test_complete_contract_review_pipeline(
        self, sample_pdf_path, mock_openai_client
    ):
        """Test complete contract review pipeline."""
        from lexicon.domain.entities.document import Document, DocumentType
        from lexicon.domain.parsers.pdf_parser import PDFParser
        from lexicon.services.contract_review import ContractReviewService, ContractReviewResponse, ClauseInfo
        
        # Step 1: Parse contract
        parser = PDFParser()
        parsed_doc = parser.parse(str(sample_pdf_path))
        parsed_doc.document_type = DocumentType.CONTRACT
        
        # Step 2: Review contract
        with patch("lexicon.services.contract_review.OpenAIProvider") as mock_provider:
            mock_instance = Mock()
            mock_response = ContractReviewResponse(
                title="Test Contract",
                contract_type="Service Agreement",
                parties=["Party A", "Party B"],
                effective_date="2024-01-01",
                expiration_date=None,
                clauses=[],
                overall_risk_score=0.2,
                key_obligations=[],
                recommendations=[]
            )
            mock_instance.generate_structured.return_value = mock_response
            mock_provider.return_value = mock_instance
            
            review_service = ContractReviewService()
            contract = review_service.review_contract(parsed_doc)
        
        assert contract is not None
        assert contract.title == "Test Contract"
        assert len(contract.parties) == 2

    def test_complete_legal_research_pipeline(self, mock_openai_client):
        """Test complete legal research pipeline."""
        from datetime import datetime
        from lexicon.domain.entities.legal_research import LegalQuery
        from lexicon.services.legal_research import LegalResearchService, LegalResearchResponse
        
        # Step 1: Create research query
        query = LegalQuery(
            query_id="e2e-query-1",
            query_text="What are the elements of breach of contract?",
            jurisdiction="United States",
            legal_area="Contract Law",
            created_at=datetime.now()
        )
        
        # Step 2: Conduct research
        with patch("lexicon.services.legal_research.OpenAIProvider") as mock_provider:
            mock_instance = Mock()
            mock_response = LegalResearchResponse(
                query_summary="Elements of breach",
                relevant_cases=[],
                relevant_statutes=[],
                analysis="Breach requires duty, breach, causation, damages",
                recommendations=[]
            )
            mock_instance.generate_structured.return_value = mock_response
            mock_provider.return_value = mock_instance
            
            research_service = LegalResearchService()
            results = research_service.research_query(query)
        
        assert results is not None
        assert "analysis" in results

    def test_complete_rag_pipeline_with_query(
        self, sample_pdf_path, mock_openai_embeddings, mock_chroma_client
    ):
        """Test complete RAG pipeline: index multiple docs -> query -> rerank."""
        from lexicon.domain.entities.document import Document, DocumentType
        from lexicon.services.rag_orchestrator import RAGOrchestrator
        
        # Create multiple documents
        documents = [
            Document(
                document_id=f"rag-doc-{i}",
                filename=f"doc{i}.pdf",
                file_path=str(sample_pdf_path),
                document_type=DocumentType.GENERAL,
                uploaded_at=None,
                file_size=1024,
            )
            for i in range(3)
        ]
        
        with patch("openai.OpenAI"):
            rag = RAGOrchestrator(openai_api_key="test-key")
            
            # Index all documents
            doc_ids = []
            for doc in documents:
                doc_id = rag.index_document(doc)
                doc_ids.append(doc_id)
            
            # Query the knowledge base
            results = rag.query("test query", top_k=5, rerank=True)
        
        assert len(doc_ids) == 3
        assert isinstance(results, list)

    def test_api_to_cli_integration(
        self, sample_pdf_path, mock_openai_client, tmp_path
    ):
        """Test that API and CLI can work with same document."""
        from typer.testing import CliRunner
        from fastapi.testclient import TestClient
        from lexicon.cli import app as cli_app
        from lexicon.api.main import app as api_app
        
        runner = CliRunner()
        client = TestClient(api_app)
        
        # Use CLI to analyze document
        with patch("lexicon.cli.analyze.DocumentAnalysisService") as mock_service:
            mock_instance = Mock()
            mock_parsed = Mock()
            mock_parsed.metadata = {"summary": "CLI summary"}
            mock_instance.analyze_document.return_value = mock_parsed
            mock_service.return_value = mock_instance
            
            cli_result = runner.invoke(cli_app, ["analyze", str(sample_pdf_path)])
        
        assert cli_result.exit_code == 0
        
        # Use API to analyze same document
        with open(sample_pdf_path, "rb") as f:
            files = {"file": ("sample.pdf", f, "application/pdf")}
            
            with patch("lexicon.api.routes.documents.DocumentAnalysisService") as mock_service:
                mock_instance = Mock()
                mock_parsed = Mock()
                mock_parsed.metadata = {"summary": "API summary"}
                mock_instance.analyze_document.return_value = mock_parsed
                mock_service.return_value = mock_instance
                
                api_response = client.post("/api/v1/documents/analyze", files=files)
        
        assert api_response.status_code == 200

    def test_multi_format_document_processing(
        self, sample_pdf_path, sample_docx_path, mock_openai_client
    ):
        """Test processing both PDF and DOCX formats."""
        from lexicon.domain.entities.document import Document, DocumentType
        from lexicon.services.document_analysis import DocumentAnalysisService
        
        documents = [
            (sample_pdf_path, "sample.pdf"),
            (sample_docx_path, "sample.docx"),
        ]
        
        with patch("lexicon.services.document_analysis.OpenAIProvider") as mock_provider:
            mock_instance = Mock()
            mock_instance.generate.return_value = "Analysis"
            mock_instance.generate_structured.return_value = Mock(parties=[], dates=[])
            mock_provider.return_value = mock_instance
            
            service = DocumentAnalysisService()
            
            for file_path, filename in documents:
                doc = Document(
                    document_id=f"multi-{filename}",
                    filename=filename,
                    file_path=str(file_path),
                    document_type=DocumentType.GENERAL,
                    uploaded_at=None,
                    file_size=1024,
                )
                
                result = service.analyze_document(doc)
                assert result is not None
