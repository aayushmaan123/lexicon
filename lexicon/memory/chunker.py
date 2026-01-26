"""Chunking strategies for different content types."""

import ast
import re
from typing import Iterator


# Minimum chunk sizes for filtering
MIN_CODE_CHUNK_SIZE = 20  # Characters
MIN_DOC_WORD_COUNT = 10   # Words


def chunk_code(code: str, file_path: str = "", language: str = "python") -> Iterator[tuple[str, dict]]:
    """Chunk code at function or class level.
    
    Strategy:
    - Unit: One function or class per chunk
    - Include class context for methods (class name + docstring)
    - Metadata: File path, language, imports
    
    Args:
        code: Source code to chunk
        file_path: Path to the source file
        language: Programming language (currently only "python" supported)
        
    Yields:
        Tuples of (chunk_content, chunk_metadata)
        
    Note:
        For Phase 2.2, only Python is fully supported. Other languages
        will fall back to simple splitting.
    """
    if language.lower() != "python":
        # Fallback for non-Python code: split by blank lines
        yield from _chunk_code_simple(code, file_path, language)
        return
    
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # Fallback if code doesn't parse
        yield from _chunk_code_simple(code, file_path, language)
        return
    
    # Extract imports for context
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"from {module} import {alias.name}")
    
    imports_context = "\n".join(imports[:5]) if imports else ""  # Limit to 5 imports
    
    # Extract functions and classes
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            # Standalone function
            chunk_content = ast.get_source_segment(code, node)
            if chunk_content:
                metadata = {
                    "type": "function",
                    "name": node.name,
                    "file_path": file_path,
                    "imports": imports_context,
                }
                yield chunk_content, metadata
                
        elif isinstance(node, ast.ClassDef):
            # Class: yield the class itself plus individual methods
            class_header = _get_class_header(code, node)
            
            # Yield full class as one chunk
            full_class = ast.get_source_segment(code, node)
            if full_class:
                metadata = {
                    "type": "class",
                    "name": node.name,
                    "file_path": file_path,
                    "imports": imports_context,
                }
                yield full_class, metadata
            
            # Also yield individual methods with class context
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_content = ast.get_source_segment(code, item)
                    if method_content:
                        # Include class header for context
                        context_chunk = f"{class_header}\n\n{method_content}"
                        metadata = {
                            "type": "method",
                            "name": f"{node.name}.{item.name}",
                            "class_name": node.name,
                            "file_path": file_path,
                            "imports": imports_context,
                        }
                        yield context_chunk, metadata


def _get_class_header(code: str, class_node: ast.ClassDef) -> str:
    """Extract class definition line and docstring."""
    lines = code.splitlines()
    class_def_line = lines[class_node.lineno - 1] if class_node.lineno > 0 else ""
    
    # Try to get docstring
    docstring = ast.get_docstring(class_node) or ""
    if docstring:
        return f"{class_def_line}\n    \"\"\"{docstring}\"\"\""
    return class_def_line


def _chunk_code_simple(code: str, file_path: str, language: str) -> Iterator[tuple[str, dict]]:
    """Simple fallback chunking for non-Python or unparseable code."""
    # Split by double newlines (blank lines)
    chunks = re.split(r'\n\s*\n', code)
    
    for i, chunk in enumerate(chunks):
        chunk = chunk.strip()
        if len(chunk) > MIN_CODE_CHUNK_SIZE:
            metadata = {
                "type": "code_block",
                "file_path": file_path,
                "language": language,
                "chunk_index": i,
            }
            yield chunk, metadata


def chunk_documentation(doc_text: str, doc_type: str = "markdown") -> Iterator[tuple[str, dict]]:
    """Chunk documentation at semantic section boundaries.
    
    Strategy:
    - Unit: H2 or H3 heading + content
    - Size: 200-500 words per chunk
    - Overlap: Include parent section title
    
    Args:
        doc_text: Documentation text to chunk
        doc_type: Type of documentation ("markdown", "rst", "plain")
        
    Yields:
        Tuples of (chunk_content, chunk_metadata)
    """
    if doc_type.lower() == "markdown":
        yield from _chunk_markdown(doc_text)
    else:
        # Fallback: split by paragraph
        yield from _chunk_by_paragraph(doc_text)


def _chunk_markdown(text: str) -> Iterator[tuple[str, dict]]:
    """Chunk markdown by headings."""
    # Split by H2 and H3 headings
    pattern = r'^\s*(#{2,3})\s+(.+)$'  # Allow leading whitespace
    lines = text.splitlines()
    
    current_chunk = []
    current_heading = None
    current_level = 0
    parent_heading = None
    word_count = 0
    
    for line in lines:
        match = re.match(pattern, line)
        
        if match:
            # Found a heading
            level = len(match.group(1))  # Number of #'s
            heading = match.group(2)
            
            # Emit previous chunk if it exists and is large enough
            if current_chunk and word_count >= MIN_DOC_WORD_COUNT:
                chunk_text = "\n".join(current_chunk)
                metadata = {
                    "type": "documentation",
                    "heading": current_heading,
                    "parent_heading": parent_heading,
                    "word_count": word_count,
                }
                yield chunk_text, metadata
            
            # Start new chunk
            if level == 2:
                parent_heading = heading
            current_heading = heading
            current_level = level
            current_chunk = [line]
            word_count = len(heading.split())
        else:
            # Regular content line
            current_chunk.append(line)
            word_count += len(line.split())
            
            # Split if chunk is getting too large (>500 words)
            if word_count > 500:
                chunk_text = "\n".join(current_chunk)
                metadata = {
                    "type": "documentation",
                    "heading": current_heading,
                    "parent_heading": parent_heading,
                    "word_count": word_count,
                }
                yield chunk_text, metadata
                
                # Reset but keep heading context
                current_chunk = [f"{'#' * current_level} {current_heading}"]
                word_count = len(current_heading.split())
    
    # Emit final chunk
    if current_chunk and word_count >= MIN_DOC_WORD_COUNT:
        chunk_text = "\n".join(current_chunk)
        metadata = {
            "type": "documentation",
            "heading": current_heading,
            "parent_heading": parent_heading,
            "word_count": word_count,
        }
        yield chunk_text, metadata


def _chunk_by_paragraph(text: str) -> Iterator[tuple[str, dict]]:
    """Simple paragraph-based chunking fallback."""
    paragraphs = re.split(r'\n\s*\n', text)
    
    current_chunk = []
    word_count = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        para_words = len(para.split())
        
        if word_count + para_words > 500 and current_chunk:
            # Emit current chunk
            chunk_text = "\n\n".join(current_chunk)
            metadata = {
                "type": "documentation",
                "word_count": word_count,
            }
            yield chunk_text, metadata
            
            # Start new chunk
            current_chunk = [para]
            word_count = para_words
        else:
            current_chunk.append(para)
            word_count += para_words
    
    # Emit final chunk
    if current_chunk:
        chunk_text = "\n\n".join(current_chunk)
        metadata = {
            "type": "documentation",
            "word_count": word_count,
        }
        yield chunk_text, metadata


def chunk_error(error_message: str, context: str = "", fix: str = "") -> tuple[str, dict]:
    """Chunk error + context + fix as a single unit.
    
    Strategy:
    - Unit: One error + fix pattern
    - Size: Error message + context + solution
    - No overlap
    
    Args:
        error_message: The error message or stack trace
        context: Additional context (file, line number, etc.)
        fix: The fix that resolved the error (optional)
        
    Returns:
        Tuple of (chunk_content, chunk_metadata)
    """
    sections = []
    
    sections.append(f"ERROR:\n{error_message}")
    
    if context:
        sections.append(f"\nCONTEXT:\n{context}")
    
    if fix:
        sections.append(f"\nFIX:\n{fix}")
    
    chunk_content = "\n".join(sections)
    
    # Extract error type from message
    error_type = "unknown"
    if ":" in error_message:
        first_line = error_message.split("\n")[0]
        if "Error" in first_line or "Exception" in first_line:
            error_type = first_line.split(":")[0].strip()
    
    metadata = {
        "type": "error_pattern",
        "error_type": error_type,
        "has_fix": bool(fix),
        "has_context": bool(context),
    }
    
    return chunk_content, metadata
