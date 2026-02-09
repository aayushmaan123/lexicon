#!/usr/bin/env python
"""Demo script showcasing the RAG-based memory system for Phase 2.2."""

import tempfile
from datetime import datetime

from lexicon.memory import (
    ChromaMemoryStore,
    MemoryMetadata,
    MemoryRetriever,
    chunk_code,
    chunk_documentation,
)


def simple_embedding(text: str) -> list[float]:
    """Simple demo embedding function."""
    import hashlib
    
    hash_val = hashlib.md5(text.encode()).hexdigest()
    return [float(int(hash_val[i % len(hash_val)], 16)) / 15.0 for i in range(384)]


def main():
    """Demonstrate the memory system capabilities."""
    print("=" * 60)
    print("Phase 2.2: RAG-based Project Memory Demo")
    print("=" * 60)
    
    # Create temporary storage
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize memory system
        print("\n1. Initializing memory system...")
        store = ChromaMemoryStore(
            persist_directory=tmpdir,
            embedding_function=simple_embedding,
        )
        retriever = MemoryRetriever(store)
        print("   ✓ Memory store initialized")
        
        # Store some code
        print("\n2. Storing Python code examples...")
        code_example = '''
def calculate_total(items):
    """Calculate total price of items."""
    return sum(item.price for item in items)

def apply_discount(total, discount_percent):
    """Apply percentage discount to total."""
    return total * (1 - discount_percent / 100)
'''
        
        chunks = list(chunk_code(code_example, "pricing.py", "python"))
        for content, meta in chunks:
            metadata = MemoryMetadata(
                source_type="code",
                phase="phase_1",
                timestamp=datetime.now(),
                language="python",
                file_path="pricing.py",
            )
            chunk_id = store.store(content, metadata)
            print(f"   ✓ Stored chunk: {meta['name']}")
        
        # Store documentation
        print("\n3. Storing documentation...")
        doc_text = '''
## Pricing Module

The pricing module handles all price calculations.

### Features

- Calculate totals with `calculate_total()`
- Apply discounts with `apply_discount()`
- Tax calculations coming soon
'''
        
        doc_chunks = list(chunk_documentation(doc_text, "markdown"))
        for content, meta in doc_chunks:
            metadata = MemoryMetadata(
                source_type="documentation",
                phase="phase_1",
                timestamp=datetime.now(),
            )
            store.store(content, metadata)
            print(f"   ✓ Stored doc section: {meta.get('heading', 'N/A')}")
        
        # Retrieve code examples
        print("\n4. Retrieving code examples...")
        results = retriever.retrieve_code_examples(
            query="calculate discount on price",
            language="python",
            top_k=3,
        )
        
        print(f"   Found {len(results)} relevant chunks:")
        for i, result in enumerate(results, 1):
            print(f"   {i}. Similarity: {result.similarity_score:.2f}")
            print(f"      Preview: {result.chunk.content[:60]}...")
        
        # Assemble context for an agent
        print("\n5. Assembling context for agent...")
        context = retriever.assemble_context(results, include_metadata=True)
        print(f"   ✓ Assembled {len(context)} characters of context")
        print(f"   Preview:\n{context[:200]}...")
        
        # Get statistics
        print("\n6. Memory statistics:")
        stats = store.get_stats()
        print(f"   Total chunks: {stats['total_chunks']}")
        print(f"   By source type: {stats['chunks_by_source_type']}")
        print(f"   By phase: {stats['chunks_by_phase']}")
        print(f"   Storage size: {stats['storage_size_mb']:.2f} MB")
        
        print("\n" + "=" * 60)
        print("Demo complete!")
        print("=" * 60)


if __name__ == "__main__":
    main()
