"""
PRD parser for ingesting PRDs from various formats (dict, JSON, Markdown).

This module handles the parsing of PRD documents into structured PRD objects.
Parsing is deterministic and does not involve LLM interpretation.
"""

import json
import re
from typing import Any, Dict, List
from lexicon.pipeline.prd_models import (
    PRD,
    PRDMetadata,
    PRDRequirement,
    RequirementPriority,
    RequirementType,
)


class PRDParser:
    """
    Parser for Product Requirements Documents.
    
    Supports parsing from:
    - Python dictionaries
    - JSON strings
    - Markdown documents (simplified format)
    
    Note: This is a deterministic parser, not an LLM-based interpreter.
    """

    @staticmethod
    def parse_from_dict(data: Dict[str, Any]) -> PRD:
        """
        Parse a PRD from a Python dictionary.
        
        Args:
            data: Dictionary containing PRD data
            
        Returns:
            Parsed PRD object
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        if not isinstance(data, dict):
            raise ValueError("Input must be a dictionary")
        
        # Parse metadata
        metadata_data = data.get("metadata", {})
        if not metadata_data:
            raise ValueError("PRD must have metadata section")
        
        metadata = PRDMetadata(
            title=metadata_data.get("title", ""),
            version=metadata_data.get("version", ""),
            author=metadata_data.get("author", ""),
            tags=metadata_data.get("tags", []),
        )
        
        # Parse overview
        overview = data.get("overview", "")
        if not overview:
            raise ValueError("PRD must have overview section")
        
        # Parse requirements
        requirements_data = data.get("requirements", [])
        if not requirements_data:
            raise ValueError("PRD must have at least one requirement")
        
        requirements = []
        for req_data in requirements_data:
            req = PRDRequirement(
                id=req_data.get("id", ""),
                type=RequirementType(req_data.get("type", "feature")),
                priority=RequirementPriority(req_data.get("priority", "medium")),
                description=req_data.get("description", ""),
                acceptance_criteria=req_data.get("acceptance_criteria", []),
                dependencies=req_data.get("dependencies", []),
                estimated_effort=req_data.get("estimated_effort"),
                metadata=req_data.get("metadata", {}),
            )
            requirements.append(req)
        
        # Parse optional sections
        constraints = data.get("constraints", [])
        out_of_scope = data.get("out_of_scope", [])
        success_criteria = data.get("success_criteria", [])
        
        return PRD(
            metadata=metadata,
            overview=overview,
            requirements=requirements,
            constraints=constraints,
            out_of_scope=out_of_scope,
            success_criteria=success_criteria,
        )

    @staticmethod
    def parse_from_json(json_str: str) -> PRD:
        """
        Parse a PRD from a JSON string.
        
        Args:
            json_str: JSON string containing PRD data
            
        Returns:
            Parsed PRD object
            
        Raises:
            ValueError: If JSON is invalid or PRD structure is incorrect
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        
        return PRDParser.parse_from_dict(data)

    @staticmethod
    def parse_from_markdown(markdown: str) -> PRD:
        """
        Parse a PRD from a Markdown document.
        
        Expected format:
        ```markdown
        # Title
        
        **Version**: v1.0.0
        **Author**: Name
        **Tags**: tag1, tag2
        
        ## Overview
        Description text...
        
        ## Requirements
        
        ### REQ-001: Feature Name (priority: high, type: feature)
        Description...
        
        **Acceptance Criteria**:
        - Criterion 1
        - Criterion 2
        
        **Dependencies**: REQ-002
        **Effort**: 8h
        
        ## Constraints
        - Constraint 1
        
        ## Out of Scope
        - Item 1
        
        ## Success Criteria
        - Criterion 1
        ```
        
        Args:
            markdown: Markdown text containing PRD
            
        Returns:
            Parsed PRD object
            
        Raises:
            ValueError: If markdown structure is invalid
        """
        lines = markdown.split("\n")
        
        # Extract title (first h1)
        title = ""
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break
        
        if not title:
            raise ValueError("Markdown PRD must have a title (# heading)")
        
        # Extract metadata fields
        version = PRDParser._extract_metadata_field(markdown, "Version")
        author = PRDParser._extract_metadata_field(markdown, "Author")
        tags_str = PRDParser._extract_metadata_field(markdown, "Tags")
        tags = [tag.strip() for tag in tags_str.split(",")] if tags_str else []
        
        metadata = PRDMetadata(title=title, version=version, author=author, tags=tags)
        
        # Extract sections
        overview = PRDParser._extract_section(markdown, "Overview")
        requirements = PRDParser._parse_requirements_from_markdown(markdown)
        constraints = PRDParser._extract_list_items(markdown, "Constraints")
        out_of_scope = PRDParser._extract_list_items(markdown, "Out of Scope")
        success_criteria = PRDParser._extract_list_items(markdown, "Success Criteria")
        
        return PRD(
            metadata=metadata,
            overview=overview,
            requirements=requirements,
            constraints=constraints,
            out_of_scope=out_of_scope,
            success_criteria=success_criteria,
        )

    @staticmethod
    def _extract_metadata_field(markdown: str, field_name: str) -> str:
        """Extract a metadata field from markdown."""
        pattern = rf"\*\*{field_name}\*\*:\s*(.+)"
        match = re.search(pattern, markdown)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _extract_section(markdown: str, section_name: str) -> str:
        """Extract content from a markdown section."""
        pattern = rf"##\s+{section_name}\s*\n(.*?)(?=\n##|\Z)"
        match = re.search(pattern, markdown, re.DOTALL)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _extract_list_items(markdown: str, section_name: str) -> List[str]:
        """Extract list items from a markdown section."""
        section_content = PRDParser._extract_section(markdown, section_name)
        if not section_content:
            return []
        
        items = []
        for line in section_content.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                items.append(line[2:].strip())
        return items

    @staticmethod
    def _parse_requirements_from_markdown(markdown: str) -> List[PRDRequirement]:
        """Parse requirements from the Requirements section of markdown."""
        requirements_section = PRDParser._extract_section(markdown, "Requirements")
        if not requirements_section:
            raise ValueError("PRD must have Requirements section")
        
        requirements = []
        # Split by h3 headings (###)
        req_blocks = re.split(r"###\s+", requirements_section)[1:]  # Skip first empty split
        
        for block in req_blocks:
            lines = block.split("\n")
            if not lines:
                continue
            
            # Parse first line: "REQ-001: Description (priority: high, type: feature)"
            first_line = lines[0].strip()
            
            # Extract ID and description
            id_match = re.match(r"([\w-]+):\s*(.+?)(?:\s*\(|$)", first_line)
            if not id_match:
                continue
            
            req_id = id_match.group(1)
            description = id_match.group(2).strip()
            
            # Extract priority and type from parentheses
            priority = RequirementPriority.MEDIUM
            req_type = RequirementType.FEATURE
            
            attrs_match = re.search(r"\((.*?)\)", first_line)
            if attrs_match:
                attrs_str = attrs_match.group(1)
                if "priority:" in attrs_str:
                    priority_match = re.search(r"priority:\s*(\w+)", attrs_str)
                    if priority_match:
                        try:
                            priority = RequirementPriority(priority_match.group(1))
                        except ValueError:
                            pass
                
                if "type:" in attrs_str:
                    type_match = re.search(r"type:\s*(\w+)", attrs_str)
                    if type_match:
                        try:
                            req_type = RequirementType(type_match.group(1))
                        except ValueError:
                            pass
            
            # Extract acceptance criteria
            acceptance_criteria = []
            in_ac_section = False
            for line in lines[1:]:
                line = line.strip()
                if "**Acceptance Criteria**:" in line:
                    in_ac_section = True
                    continue
                elif line.startswith("**"):
                    in_ac_section = False
                
                if in_ac_section and line.startswith("- "):
                    acceptance_criteria.append(line[2:].strip())
            
            # Extract dependencies
            dependencies = []
            deps_match = re.search(r"\*\*Dependencies\*\*:\s*(.+)", block)
            if deps_match:
                deps_str = deps_match.group(1).strip()
                dependencies = [d.strip() for d in deps_str.split(",")]
            
            # Extract effort
            estimated_effort = None
            effort_match = re.search(r"\*\*Effort\*\*:\s*(\d+(?:\.\d+)?)", block)
            if effort_match:
                estimated_effort = float(effort_match.group(1))
            
            requirements.append(
                PRDRequirement(
                    id=req_id,
                    type=req_type,
                    priority=priority,
                    description=description,
                    acceptance_criteria=acceptance_criteria,
                    dependencies=dependencies,
                    estimated_effort=estimated_effort,
                )
            )
        
        if not requirements:
            raise ValueError("No requirements found in markdown")
        
        return requirements
