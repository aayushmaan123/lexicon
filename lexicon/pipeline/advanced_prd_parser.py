"""
Advanced PRD parser for Phase 3.1: Support for nested task hierarchies.

This module extends Phase 2.4 PRD parsing with support for:
- Nested task structures (parent/child relationships)
- Recursive parsing of hierarchical requirements
- Extended metadata and attributes

Maintains 100% backward compatibility with Phase 2.4 flat PRDs.
"""

import json
import re
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional

from .prd_models import PRDMetadata, RequirementType, RequirementPriority
from .advanced_prd_models import AdvancedPRDRequirement, AdvancedPRD


class AdvancedPRDParser:
    """
    Parser for Advanced PRDs with nested task support.
    
    Supports parsing from:
    - Python dictionaries (nested structure)
    - JSON strings
    - Markdown format (with nested sections)
    
    All parsing is deterministic (no LLM interpretation).
    """
    
    @staticmethod
    def parse_from_dict(data: Dict[str, Any]) -> AdvancedPRD:
        """
        Parse AdvancedPRD from a dictionary.
        
        Args:
            data: Dictionary with PRD structure
            
        Returns:
            Parsed AdvancedPRD object
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Parse metadata
        metadata_dict = data.get("metadata", {})
        metadata = PRDMetadata(
            title=metadata_dict.get("title", ""),
            version=metadata_dict.get("version", "1.0"),
            author=metadata_dict.get("author", ""),
            created_at=metadata_dict.get("created_at", datetime.now(UTC)),
            updated_at=metadata_dict.get("updated_at", datetime.now(UTC)),
            tags=metadata_dict.get("tags", []),
        )
        
        # Parse overview
        overview = data.get("overview", "")
        
        # Parse requirements
        requirements_data = data.get("requirements", [])
        requirements = [
            AdvancedPRDParser._parse_requirement(req_data)
            for req_data in requirements_data
        ]
        
        # Parse optional fields
        constraints = data.get("constraints", [])
        out_of_scope = data.get("out_of_scope", [])
        success_criteria = data.get("success_criteria", [])
        
        return AdvancedPRD(
            metadata=metadata,
            overview=overview,
            requirements=requirements,
            constraints=constraints,
            out_of_scope=out_of_scope,
            success_criteria=success_criteria,
        )
    
    @staticmethod
    def _parse_requirement(data: Dict[str, Any]) -> AdvancedPRDRequirement:
        """
        Parse a single AdvancedPRDRequirement from dictionary.
        
        Args:
            data: Dictionary with requirement data
            
        Returns:
            Parsed AdvancedPRDRequirement
        """
        # Core fields
        req_id = data.get("id", "")
        description = data.get("description", "")
        dependencies = data.get("dependencies", [])
        req_type = data.get("type", "feature")
        
        # Phase 3.1 extensions
        parent_id = data.get("parent_id")
        optional = data.get("optional", False)
        
        # Priority (handle both string and enum)
        priority_val = data.get("priority", "medium")
        if isinstance(priority_val, str):
            try:
                priority = RequirementPriority(priority_val.lower())
            except ValueError:
                priority = RequirementPriority.MEDIUM
        else:
            priority = priority_val
        
        estimated_hours = data.get("estimated_hours")
        external_dependencies = data.get("external_dependencies", [])
        resources = data.get("resources", [])
        acceptance_criteria = data.get("acceptance_criteria", [])
        tags = data.get("tags", [])
        assignee = data.get("assignee")
        metadata = data.get("metadata", {})
        
        return AdvancedPRDRequirement(
            id=req_id,
            description=description,
            dependencies=dependencies,
            type=req_type,
            parent_id=parent_id,
            optional=optional,
            priority=priority,
            estimated_hours=estimated_hours,
            external_dependencies=external_dependencies,
            resources=resources,
            acceptance_criteria=acceptance_criteria,
            tags=tags,
            assignee=assignee,
            metadata=metadata,
        )
    
    @staticmethod
    def parse_from_json(json_str: str) -> AdvancedPRD:
        """
        Parse AdvancedPRD from JSON string.
        
        Args:
            json_str: JSON string containing PRD
            
        Returns:
            Parsed AdvancedPRD object
            
        Raises:
            ValueError: If JSON is invalid or required fields missing
        """
        try:
            data = json.loads(json_str)
            return AdvancedPRDParser.parse_from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
    
    @staticmethod
    def parse_from_markdown(markdown: str) -> AdvancedPRD:
        """
        Parse AdvancedPRD from Markdown format.
        
        Expected format:
            # PRD: {title}
            **Version:** {version}
            **Author:** {author}
            
            ## Overview
            {overview text}
            
            ## Requirements
            ### {id}: {description}
            - **Type:** {type}
            - **Priority:** {priority}
            - **Parent:** {parent_id}  (optional)
            - **Optional:** {yes/no}  (optional)
            - **Dependencies:** {dep1, dep2}  (optional)
            - **Resources:** {res1, res2}  (optional)
            - **Acceptance Criteria:**
              - {criterion 1}
              - {criterion 2}
            
            #### {child_id}: {child description}  (nested under parent)
            ...
        
        Args:
            markdown: Markdown string
            
        Returns:
            Parsed AdvancedPRD object
            
        Raises:
            ValueError: If required sections are missing
        """
        lines = markdown.strip().split("\n")
        
        # Parse title from first heading
        title = ""
        for line in lines:
            if line.startswith("# PRD:") or line.startswith("# "):
                title = line.lstrip("#").replace("PRD:", "").strip()
                break
        
        # Parse metadata fields
        version = "1.0"
        author = "Unknown"
        
        for line in lines:
            if "**Version:**" in line:
                version = line.split("**Version:**")[1].strip()
            elif "**Author:**" in line:
                author = line.split("**Author:**")[1].strip()
        
        metadata = PRDMetadata(
            title=title or "Untitled PRD",
            version=version,
            author=author,
        )
        
        # Parse overview section
        overview = AdvancedPRDParser._extract_section(lines, "## Overview")
        
        # Parse requirements
        requirements = AdvancedPRDParser._parse_requirements_from_markdown(lines)
        
        # Parse optional sections
        constraints = AdvancedPRDParser._extract_list_section(lines, "## Constraints")
        out_of_scope = AdvancedPRDParser._extract_list_section(lines, "## Out of Scope")
        success_criteria = AdvancedPRDParser._extract_list_section(lines, "## Success Criteria")
        
        return AdvancedPRD(
            metadata=metadata,
            overview=overview or "No overview provided",
            requirements=requirements,
            constraints=constraints,
            out_of_scope=out_of_scope,
            success_criteria=success_criteria,
        )
    
    @staticmethod
    def _extract_section(lines: List[str], header: str) -> str:
        """Extract text from a markdown section."""
        in_section = False
        section_lines = []
        
        for line in lines:
            if line.startswith(header):
                in_section = True
                continue
            elif in_section and line.startswith("##"):
                break
            elif in_section:
                section_lines.append(line)
        
        return "\n".join(section_lines).strip()
    
    @staticmethod
    def _extract_list_section(lines: List[str], header: str) -> List[str]:
        """Extract list items from a markdown section."""
        section_text = AdvancedPRDParser._extract_section(lines, header)
        if not section_text:
            return []
        
        items = []
        for line in section_text.split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("*"):
                items.append(line.lstrip("-*").strip())
        
        return items
    
    @staticmethod
    def _parse_requirements_from_markdown(lines: List[str]) -> List[AdvancedPRDRequirement]:
        """
        Parse requirements from markdown, supporting nested structure.
        
        Uses heading levels to determine nesting:
        - ### = root requirement
        - #### = child of previous ###
        - ##### = grandchild
        etc.
        """
        requirements = []
        current_req = None
        current_level = 0
        parent_stack = []  # Stack of (level, req_id) tuples
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check for requirement heading
            if line.startswith("###"):
                # Determine level
                level = len(re.match(r"^#+", line).group())
                heading_text = line.lstrip("#").strip()
                
                # Parse ID and description from heading: "id: description"
                if ":" in heading_text:
                    req_id, description = heading_text.split(":", 1)
                    req_id = req_id.strip()
                    description = description.strip()
                else:
                    req_id = heading_text
                    description = heading_text
                
                # Determine parent based on level
                parent_id = None
                if level > 3:  # Level 3 is root (###), 4+ are nested
                    # Find parent at level - 1
                    for stack_level, stack_id in reversed(parent_stack):
                        if stack_level == level - 1:
                            parent_id = stack_id
                            break
                
                # Parse requirement attributes from following lines
                j = i + 1
                req_type = "feature"
                priority = RequirementPriority.MEDIUM
                optional = False
                dependencies = []
                resources = []
                acceptance_criteria = []
                
                while j < len(lines):
                    attr_line = lines[j].strip()
                    
                    # Stop at next requirement
                    if attr_line.startswith("###"):
                        break
                    
                    # Parse attributes
                    if "**Type:**" in attr_line:
                        req_type = attr_line.split("**Type:**")[1].strip().lower()
                    elif "**Priority:**" in attr_line:
                        priority_str = attr_line.split("**Priority:**")[1].strip().lower()
                        try:
                            priority = RequirementPriority(priority_str)
                        except ValueError:
                            priority = RequirementPriority.MEDIUM
                    elif "**Optional:**" in attr_line:
                        optional_str = attr_line.split("**Optional:**")[1].strip().lower()
                        optional = optional_str in ["yes", "true", "1"]
                    elif "**Dependencies:**" in attr_line:
                        deps_str = attr_line.split("**Dependencies:**")[1].strip()
                        dependencies = [d.strip() for d in deps_str.split(",") if d.strip()]
                    elif "**Resources:**" in attr_line:
                        res_str = attr_line.split("**Resources:**")[1].strip()
                        resources = [r.strip() for r in res_str.split(",") if r.strip()]
                    elif "**Acceptance Criteria:**" in attr_line:
                        # Read list items following
                        k = j + 1
                        while k < len(lines):
                            criteria_line = lines[k].strip()
                            if criteria_line.startswith("-") or criteria_line.startswith("*"):
                                acceptance_criteria.append(criteria_line.lstrip("-*").strip())
                                k += 1
                            else:
                                break
                        j = k - 1
                    
                    j += 1
                
                # Create requirement
                req = AdvancedPRDRequirement(
                    id=req_id,
                    description=description,
                    dependencies=dependencies,
                    type=req_type,
                    parent_id=parent_id,
                    optional=optional,
                    priority=priority,
                    resources=resources,
                    acceptance_criteria=acceptance_criteria,
                )
                requirements.append(req)
                
                # Update parent stack
                # Remove items at same or deeper level
                parent_stack = [(l, id) for l, id in parent_stack if l < level]
                # Add current requirement
                parent_stack.append((level, req_id))
                
                i = j
            else:
                i += 1
        
        return requirements
