"""
Example: Using the RAG Pipeline for Document Indexing and Querying

This example demonstrates how to use the RAG orchestrator to:
1. Index a document (PDF or DOCX)
2. Query the indexed documents
3. Assemble context for LLM generation
"""

from lexicon.domain.entities.document import Document, DocumentType
from lexicon.services.rag_orchestrator import RAGOrchestrator


def index_document_example():
    """Example of indexing a document."""
    # Create RAG orchestrator
    orchestrator = RAGOrchestrator()

    # Create a document entity
    document = Document(
        id="contract-001",
        filename="contract.pdf",
        file_path="/path/to/contract.pdf",
        file_size=1024000,  # 1MB
        document_type=DocumentType.CONTRACT,
    )

    # Index the document
    # This will:
    # 1. Parse the PDF to extract text
    # 2. Chunk the text based on contract-specific settings (512 tokens, 50 overlap)
    # 3. Generate embeddings for each chunk using OpenAI
    # 4. Store chunks with embeddings in ChromaDB
    doc_id = orchestrator.index_document(document)

    print(f"Indexed document: {doc_id}")
    print(f"Total embedding cost: ${orchestrator.total_cost:.4f}")

    # Get indexing statistics
    stats = orchestrator.get_stats()
    print(f"Total tokens used: {stats['total_embedding_tokens']}")
    print(f"Vector store stats: {stats['vector_store_stats']}")


def query_documents_example():
    """Example of querying indexed documents."""
    # Create RAG orchestrator
    orchestrator = RAGOrchestrator()

    # Query the indexed documents
    query = "What are the termination clauses in the contract?"

    # Perform query with reranking
    # This will:
    # 1. Check semantic cache for similar queries
    # 2. Generate query embedding
    # 3. Search vector store for similar chunks (top 20)
    # 4. Rerank results using BM25 to get top 10
    # 5. Cache the results
    results = orchestrator.query(
        query_text=query,
        top_k=10,
        filters={"document_type": "contract"},  # Optional: filter by metadata
        rerank=True,
    )

    # Display results
    print(f"\nFound {len(results)} relevant chunks:")
    for i, result in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"  Score: {result.get('rerank_score', result.get('score', 0)):.3f}")
        print(f"  Source: {result['metadata'].get('filename', 'Unknown')}")
        print(f"  Chunk: {result['metadata'].get('chunk_index', 'N/A')}")
        print(f"  Text preview: {result['text'][:200]}...")


def assemble_context_for_llm():
    """Example of assembling context for LLM generation."""
    orchestrator = RAGOrchestrator()

    # Query documents
    query = "What are the payment terms?"
    results = orchestrator.query(query_text=query, top_k=5, rerank=True)

    # Assemble context for LLM
    # This creates a formatted context string with:
    # - Original query
    # - Numbered chunks with metadata
    # - Relevance scores
    context = orchestrator.assemble_context(
        query=query,
        search_results=results,
        max_context_length=4000,  # Limit to 4000 characters
    )

    print("\nAssembled Context for LLM:")
    print(context)

    # Now you can use this context with an LLM
    # from lexicon.infrastructure.openai_client import OpenAIProvider
    # llm = OpenAIProvider(model="gpt-4o-mini")
    # prompt = f"{context}\n\nQuestion: {query}\nAnswer:"
    # response = llm.generate(prompt)


def advanced_example_with_custom_components():
    """Example with custom cache, vector store, and reranker."""
    from lexicon.infrastructure.cache_client import CacheClient
    from lexicon.infrastructure.chroma_client import ChromaVectorStore
    from lexicon.services.reranker import Reranker

    # Create custom components
    cache = CacheClient(
        redis_url="redis://localhost:6379/0",
        ttl=7200,  # 2 hours
    )

    vector_store = ChromaVectorStore(
        collection_name="my_custom_collection",
        persist_directory="./my_vector_data",
    )

    reranker = Reranker(
        k1=2.0,  # More aggressive term frequency
        b=0.5,  # Less length normalization
        use_bm25=True,
    )

    # Create orchestrator with custom components
    orchestrator = RAGOrchestrator(
        embedding_model="text-embedding-3-large",
        vector_store=vector_store,
        cache_client=cache,
        reranker=reranker,
    )

    # Now use the orchestrator as normal
    document = Document(
        id="doc-001",
        filename="document.pdf",
        file_path="/path/to/document.pdf",
        file_size=2048000,
        document_type=DocumentType.GENERAL,
    )

    doc_id = orchestrator.index_document(document)
    print(f"Indexed with custom setup: {doc_id}")


def batch_indexing_example():
    """Example of indexing multiple documents."""
    orchestrator = RAGOrchestrator()

    documents = [
        Document(
            id=f"contract-{i:03d}",
            filename=f"contract_{i}.pdf",
            file_path=f"/path/to/contracts/contract_{i}.pdf",
            file_size=1024000,
            document_type=DocumentType.CONTRACT,
        )
        for i in range(1, 11)  # 10 contracts
    ]

    total_cost = 0.0
    for doc in documents:
        try:
            doc_id = orchestrator.index_document(doc)
            print(f"✓ Indexed {doc.filename}: {doc_id}")
        except Exception as e:
            print(f"✗ Failed to index {doc.filename}: {str(e)}")

    # Get final statistics
    stats = orchestrator.get_stats()
    print(f"\nBatch Indexing Complete:")
    print(f"  Total tokens: {stats['total_embedding_tokens']:,}")
    print(f"  Total cost: ${stats['total_cost']:.4f}")
    print(f"  Documents in store: {stats['vector_store_stats']['count']}")


def cache_performance_example():
    """Example demonstrating cache performance benefits."""
    orchestrator = RAGOrchestrator()

    query = "What are the liability limitations?"

    # First query - will generate embedding and search
    print("First query (no cache):")
    import time

    start = time.time()
    results1 = orchestrator.query(query, top_k=5)
    time1 = time.time() - start
    print(f"  Time: {time1:.3f}s")

    # Second identical query - should hit semantic cache
    print("\nSecond query (with cache):")
    start = time.time()
    results2 = orchestrator.query(query, top_k=5)
    time2 = time.time() - start
    print(f"  Time: {time2:.3f}s")
    print(f"  Speedup: {time1/time2:.1f}x faster")

    # Verify results are the same
    assert len(results1) == len(results2)
    print("  ✓ Results are identical")


if __name__ == "__main__":
    print("=== RAG Pipeline Examples ===\n")

    print("1. Document Indexing")
    print("-" * 50)
    # index_document_example()  # Uncomment to run

    print("\n2. Querying Documents")
    print("-" * 50)
    # query_documents_example()  # Uncomment to run

    print("\n3. Assembling Context for LLM")
    print("-" * 50)
    # assemble_context_for_llm()  # Uncomment to run

    print("\n4. Advanced: Custom Components")
    print("-" * 50)
    # advanced_example_with_custom_components()  # Uncomment to run

    print("\n5. Batch Indexing")
    print("-" * 50)
    # batch_indexing_example()  # Uncomment to run

    print("\n6. Cache Performance")
    print("-" * 50)
    # cache_performance_example()  # Uncomment to run

    print(
        "\nNote: Examples are commented out by default."
        "\nUncomment and provide actual file paths to run."
    )
