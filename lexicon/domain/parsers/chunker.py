"""Document chunking strategies for RAG."""

import hashlib
import re

from lexicon.domain.entities.document import DocumentChunk, ParsedDocument
from lexicon.shared.config import settings
from lexicon.shared.token_counter.counter import TokenCounter


def clause_aware_chunker(
    parsed_doc: ParsedDocument,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[DocumentChunk]:
    """Chunk document with clause awareness for contracts.

    Uses smaller chunks optimized for legal contracts with clause boundaries.

    Args:
        parsed_doc: The parsed document to chunk
        chunk_size: Token size for each chunk (default: from settings)
        chunk_overlap: Token overlap between chunks (default: from settings)

    Returns:
        List of document chunks
    """
    chunk_size = chunk_size or settings.chunk_size_contract
    chunk_overlap = chunk_overlap or settings.chunk_overlap_contract

    return _sliding_window_chunker(
        parsed_doc=parsed_doc,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


def section_based_chunker(
    parsed_doc: ParsedDocument,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[DocumentChunk]:
    """Chunk document based on sections for case law.

    Uses larger chunks optimized for case law with section boundaries.

    Args:
        parsed_doc: The parsed document to chunk
        chunk_size: Token size for each chunk (default: from settings)
        chunk_overlap: Token overlap between chunks (default: from settings)

    Returns:
        List of document chunks
    """
    chunk_size = chunk_size or settings.chunk_size_case_law
    chunk_overlap = chunk_overlap or settings.chunk_overlap_case_law

    return _sliding_window_chunker(
        parsed_doc=parsed_doc,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


def sliding_window_chunker(
    parsed_doc: ParsedDocument,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[DocumentChunk]:
    """Chunk document using sliding window for general documents.

    Uses medium-sized chunks optimized for general documents.

    Args:
        parsed_doc: The parsed document to chunk
        chunk_size: Token size for each chunk (default: from settings)
        chunk_overlap: Token overlap between chunks (default: from settings)

    Returns:
        List of document chunks
    """
    chunk_size = chunk_size or settings.chunk_size_general
    chunk_overlap = chunk_overlap or settings.chunk_overlap_general

    return _sliding_window_chunker(
        parsed_doc=parsed_doc,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


def _sliding_window_chunker(
    parsed_doc: ParsedDocument,
    chunk_size: int,
    chunk_overlap: int,
) -> list[DocumentChunk]:
    """Internal sliding window chunker implementation.

    Args:
        parsed_doc: The parsed document to chunk
        chunk_size: Token size for each chunk
        chunk_overlap: Token overlap between chunks

    Returns:
        List of document chunks
    """
    token_counter = TokenCounter()
    chunks = []

    # Split text into sentences (simple approach)
    text = parsed_doc.full_text
    sentences = _split_into_sentences(text)

    current_chunk = []
    current_tokens = 0
    chunk_index = 0

    for sentence in sentences:
        sentence_tokens = token_counter.count_tokens(sentence)

        # If adding this sentence exceeds chunk size, create a chunk
        if current_tokens + sentence_tokens > chunk_size and current_chunk:
            # Create chunk
            chunk_text = " ".join(current_chunk)
            chunk_id = _generate_chunk_id(parsed_doc.document_id, chunk_index)

            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=parsed_doc.document_id,
                    content=chunk_text,
                    chunk_index=chunk_index,
                    token_count=current_tokens,
                    metadata={
                        "filename": parsed_doc.filename,
                        "document_type": parsed_doc.document_type,
                    },
                )
            )

            # Calculate overlap
            overlap_tokens = 0
            overlap_sentences = []

            # Keep sentences from the end to match overlap size
            for sent in reversed(current_chunk):
                sent_tokens = token_counter.count_tokens(sent)
                if overlap_tokens + sent_tokens <= chunk_overlap:
                    overlap_sentences.insert(0, sent)
                    overlap_tokens += sent_tokens
                else:
                    break

            # Start new chunk with overlap
            current_chunk = overlap_sentences
            current_tokens = overlap_tokens
            chunk_index += 1

        current_chunk.append(sentence)
        current_tokens += sentence_tokens

    # Add final chunk if there's remaining content
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunk_id = _generate_chunk_id(parsed_doc.document_id, chunk_index)

        chunks.append(
            DocumentChunk(
                chunk_id=chunk_id,
                document_id=parsed_doc.document_id,
                content=chunk_text,
                chunk_index=chunk_index,
                token_count=current_tokens,
                metadata={
                    "filename": parsed_doc.filename,
                    "document_type": parsed_doc.document_type,
                },
            )
        )

    return chunks


def _split_into_sentences(text: str) -> list[str]:
    """Split text into sentences.

    Args:
        text: Input text

    Returns:
        List of sentences
    """
    # Split on period, exclamation, or question mark followed by space
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def _generate_chunk_id(document_id: str, chunk_index: int) -> str:
    """Generate a unique chunk ID.

    Args:
        document_id: Document identifier
        chunk_index: Index of the chunk

    Returns:
        Unique chunk identifier
    """
    content = f"{document_id}_{chunk_index}"
    return hashlib.md5(content.encode()).hexdigest()
