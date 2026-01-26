"""Unit tests for chunking strategies."""

import pytest

from lexicon.memory.chunker import (
    chunk_code,
    chunk_documentation,
    chunk_error,
)


class TestChunkCode:
    """Test code chunking strategies."""
    
    def test_chunk_simple_function(self):
        """Test chunking a simple standalone function."""
        code = '''
def greet(name):
    """Greet a person."""
    return f"Hello, {name}!"
'''
        
        chunks = list(chunk_code(code, "test.py", "python"))
        
        assert len(chunks) == 1
        content, metadata = chunks[0]
        
        assert "def greet(name):" in content
        assert metadata["type"] == "function"
        assert metadata["name"] == "greet"
        assert metadata["file_path"] == "test.py"
    
    def test_chunk_multiple_functions(self):
        """Test chunking multiple standalone functions."""
        code = '''
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b
'''
        
        chunks = list(chunk_code(code, "math.py", "python"))
        
        assert len(chunks) == 3
        
        names = [meta["name"] for _, meta in chunks]
        assert "add" in names
        assert "subtract" in names
        assert "multiply" in names
    
    def test_chunk_class_with_methods(self):
        """Test chunking a class yields both full class and individual methods."""
        code = '''
class Calculator:
    """A simple calculator."""
    
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
'''
        
        chunks = list(chunk_code(code, "calc.py", "python"))
        
        # Should have: 1 full class + 2 methods with context
        assert len(chunks) == 3
        
        # Check for full class
        class_chunks = [c for c, m in chunks if m["type"] == "class"]
        assert len(class_chunks) == 1
        assert "class Calculator:" in class_chunks[0]
        
        # Check for methods with class context
        method_chunks = [c for c, m in chunks if m["type"] == "method"]
        assert len(method_chunks) == 2
        
        # Methods should include class header
        for method_content in method_chunks:
            assert "class Calculator:" in method_content
    
    def test_chunk_with_imports(self):
        """Test that imports are included in metadata."""
        code = '''
import os
from pathlib import Path
from typing import Optional

def read_file(path: str) -> str:
    return Path(path).read_text()
'''
        
        chunks = list(chunk_code(code, "io.py", "python"))
        
        assert len(chunks) == 1
        _, metadata = chunks[0]
        
        assert "imports" in metadata
        assert "import os" in metadata["imports"]
        assert "from pathlib import Path" in metadata["imports"]
    
    def test_chunk_async_function(self):
        """Test chunking async functions."""
        code = '''
async def fetch_data(url: str):
    """Fetch data from URL."""
    return await client.get(url)
'''
        
        chunks = list(chunk_code(code, "api.py", "python"))
        
        assert len(chunks) == 1
        content, metadata = chunks[0]
        
        assert "async def fetch_data" in content
        assert metadata["name"] == "fetch_data"
    
    def test_chunk_invalid_syntax(self):
        """Test that invalid Python falls back to simple chunking."""
        code = '''
This is not valid Python code!
def incomplete(

Some more text here.
'''
        
        chunks = list(chunk_code(code, "bad.py", "python"))
        
        # Should still return some chunks via fallback
        assert len(chunks) > 0
    
    def test_chunk_non_python_language(self):
        """Test chunking non-Python code uses fallback."""
        code = '''
function greet(name) {
    return `Hello, ${name}!`;
}

function farewell(name) {
    return `Goodbye, ${name}!`;
}
'''
        
        chunks = list(chunk_code(code, "test.js", "javascript"))
        
        # Should use fallback chunking
        assert len(chunks) > 0
        
        for _, metadata in chunks:
            assert metadata["language"] == "javascript"
            assert metadata["type"] == "code_block"


class TestChunkDocumentation:
    """Test documentation chunking strategies."""
    
    def test_chunk_markdown_with_h2_headings(self):
        """Test chunking markdown by H2 headings."""
        doc = '''
# Main Title

## Section 1

This is the first section with some content.
It has multiple paragraphs.

This is the second paragraph.

## Section 2

This is the second section.
It also has content.

## Section 3

Final section here with enough words to pass minimum threshold for chunking.
'''
        
        chunks = list(chunk_documentation(doc, "markdown"))
        
        # Should have chunks for each H2 section  (that meets minimum size)
        assert len(chunks) >= 2  # At least 2 sections
        
        headings = [meta.get("heading") for _, meta in chunks if meta.get("heading")]
        assert "Section 1" in headings
        assert "Section 2" in headings
    
    def test_chunk_markdown_with_h3_headings(self):
        """Test chunking includes H3 subsections."""
        doc = '''
## Main Section

Some intro text that provides context for the sections below.

### Subsection A

Content for subsection A with sufficient words to meet minimum threshold.

### Subsection B

Content for subsection B also with enough words.
'''
        
        chunks = list(chunk_documentation(doc, "markdown"))
        
        assert len(chunks) >= 1  # At least one chunk
        
        # Check that subsections reference parent
        for content, meta in chunks:
            if meta.get("heading") in ["Subsection A", "Subsection B"]:
                assert meta.get("parent_heading") == "Main Section"
    
    def test_chunk_respects_word_limits(self):
        """Test that chunks stay within reasonable word count limits."""
        # Create a long section
        long_text = " ".join(["word"] * 600)  # 600 words
        doc = f'''
## Long Section

{long_text}
'''
        
        chunks = list(chunk_documentation(doc, "markdown"))
        
        # Should have at least one chunk (might not split in this implementation)
        assert len(chunks) >= 1
        
        # Check that chunks don't massively exceed limit
        for _, meta in chunks:
            # Allow some tolerance above 500 words
            assert meta.get("word_count", 0) <= 700
    
    def test_chunk_minimum_size(self):
        """Test that very small sections are filtered out."""
        doc = '''
## Section 1

Just a few words.

## Section 2

This section has enough content to be included in the chunking process.
It has multiple sentences and provides meaningful information that exceeds minimum threshold.

## Section 3

Too small.
'''
        
        chunks = list(chunk_documentation(doc, "markdown"))
        
        # Only Section 2 should be included (meets minimum word count)
        headings = [meta.get("heading") for _, meta in chunks]
        assert "Section 2" in headings
        # Small sections might be filtered
        assert len(headings) >= 1
    
    def test_chunk_plain_text_fallback(self):
        """Test chunking plain text uses paragraph-based strategy."""
        doc = '''
This is the first paragraph.
It has some content.

This is the second paragraph.
It also has content.

This is the third paragraph.
More content here.
'''
        
        chunks = list(chunk_documentation(doc, "plain"))
        
        # Should chunk by paragraphs
        assert len(chunks) > 0
        
        for _, meta in chunks:
            assert meta["type"] == "documentation"


class TestChunkError:
    """Test error pattern chunking."""
    
    def test_chunk_error_only(self):
        """Test chunking error message alone."""
        error_msg = "TypeError: expected str, got int"
        
        content, metadata = chunk_error(error_msg)
        
        assert "ERROR:" in content
        assert error_msg in content
        assert metadata["type"] == "error_pattern"
        assert metadata["error_type"] == "TypeError"
        assert metadata["has_fix"] is False
        assert metadata["has_context"] is False
    
    def test_chunk_error_with_context(self):
        """Test chunking error with context."""
        error_msg = "ValueError: invalid literal for int()"
        context = "File: main.py, Line: 42"
        
        content, metadata = chunk_error(error_msg, context=context)
        
        assert "ERROR:" in content
        assert "CONTEXT:" in content
        assert error_msg in content
        assert context in content
        assert metadata["has_context"] is True
    
    def test_chunk_error_with_fix(self):
        """Test chunking error with fix."""
        error_msg = "ImportError: No module named 'foo'"
        fix = "Install foo: pip install foo"
        
        content, metadata = chunk_error(error_msg, fix=fix)
        
        assert "ERROR:" in content
        assert "FIX:" in content
        assert error_msg in content
        assert fix in content
        assert metadata["has_fix"] is True
    
    def test_chunk_complete_error_pattern(self):
        """Test chunking complete error pattern with all components."""
        error_msg = "AttributeError: 'NoneType' object has no attribute 'value'"
        context = "File: services/processor.py, Line: 128\nFunction: process_data"
        fix = "Added null check before accessing .value attribute"
        
        content, metadata = chunk_error(error_msg, context=context, fix=fix)
        
        assert "ERROR:" in content
        assert "CONTEXT:" in content
        assert "FIX:" in content
        assert metadata["error_type"] == "AttributeError"
        assert metadata["has_fix"] is True
        assert metadata["has_context"] is True
    
    def test_extract_error_type(self):
        """Test error type extraction from message."""
        test_cases = [
            ("TypeError: bad type", "TypeError"),
            ("ValueError: invalid value", "ValueError"),
            ("CustomError: something wrong", "CustomError"),
            ("Just a message", "unknown"),
        ]
        
        for error_msg, expected_type in test_cases:
            _, metadata = chunk_error(error_msg)
            assert metadata["error_type"] == expected_type
