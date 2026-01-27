# Phase 3.1: Advanced PRD Handling

## Overview

Phase 3.1 extends the Phase 2.4 PRD pipeline to support nested tasks, optional subtasks, cross-project dependencies, and enhanced validation. This enables complex, hierarchical project requirements while maintaining full backward compatibility with flat PRD structures.

**Status**: Design Document  
**Dependencies**: Phase 2.4 (PRD Pipeline)  
**Version**: 1.0

---

## Objectives

1. Support nested task hierarchies (parent tasks with subtasks)
2. Enable optional vs. required subtask marking
3. Handle cross-project dependencies
4. Validate complex dependency graphs (including nested structures)
5. Maintain 100% backward compatibility with Phase 2.4 flat PRDs

---

## Extended Data Models

### Advanced PRD Requirement

```python
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class RequirementPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ResourceType(str, Enum):
    FILE = "file"
    API = "api"
    DATABASE = "database"
    EXTERNAL_SERVICE = "external_service"

class AdvancedPRDRequirement(BaseModel):
    """Extended PRD requirement with nesting and advanced features."""
    
    # Core fields (from Phase 2.4)
    id: str
    description: str
    dependencies: List[str] = Field(default_factory=list)
    type: str = "feature"
    
    # Phase 3.1 extensions
    parent_id: Optional[str] = None  # For nested tasks
    optional: bool = False  # Required vs. optional subtask
    priority: RequirementPriority = RequirementPriority.MEDIUM
    estimated_hours: Optional[float] = None
    external_dependencies: List[str] = Field(default_factory=list)  # Cross-project
    resources: List[ResourceType] = Field(default_factory=list)  # Resource annotations
    acceptance_criteria: List[str] = Field(default_factory=list)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    assignee: Optional[str] = None
```

### Advanced PRD

```python
class AdvancedPRD(BaseModel):
    """Extended PRD with nested requirements and advanced features."""
    
    metadata: PRDMetadata  # Reuse from Phase 2.4
    requirements: List[AdvancedPRDRequirement]
    constraints: Optional[List[str]] = None
    
    # Phase 3.1 extensions
    external_projects: List[str] = Field(default_factory=list)  # Cross-project links
    resource_limits: Optional[Dict[str, int]] = None  # e.g., {"max_parallel_tasks": 3}
    validation_rules: Optional[Dict[str, Any]] = None  # Custom validation logic
```

---

## Parsing Logic

### Nested PRD Parser

```python
class AdvancedPRDParser:
    """Parse PRDs with nested task structures."""
    
    def parse_nested_dict(self, data: Dict[str, Any]) -> AdvancedPRD:
        """Parse nested PRD from dictionary."""
        # Validate structure
        if "requirements" not in data:
            raise ValueError("Missing 'requirements' field")
        
        # Parse requirements (flatten nested structures)
        requirements = self._parse_requirements_tree(data["requirements"])
        
        return AdvancedPRD(
            metadata=PRDMetadata(**data.get("metadata", {})),
            requirements=requirements,
            constraints=data.get("constraints"),
            external_projects=data.get("external_projects", []),
            resource_limits=data.get("resource_limits"),
            validation_rules=data.get("validation_rules")
        )
    
    def _parse_requirements_tree(
        self, 
        reqs: List[Dict[str, Any]], 
        parent_id: Optional[str] = None
    ) -> List[AdvancedPRDRequirement]:
        """Recursively parse nested requirements."""
        result = []
        for req_data in reqs:
            # Parse current requirement
            req = AdvancedPRDRequirement(
                id=req_data["id"],
                description=req_data["description"],
                dependencies=req_data.get("dependencies", []),
                parent_id=parent_id,
                optional=req_data.get("optional", False),
                priority=req_data.get("priority", "medium"),
                # ... other fields
            )
            result.append(req)
            
            # Recursively parse subtasks
            if "subtasks" in req_data:
                subtasks = self._parse_requirements_tree(
                    req_data["subtasks"],
                    parent_id=req.id
                )
                result.extend(subtasks)
        
        return result
```

### Markdown Parsing (Extended)

Support for nested task syntax:

```markdown
## Requirements

### req1: Implement User Authentication
- Priority: high
- Dependencies: []

  #### req1.1: Create login endpoint (required)
  - Description: Implement POST /api/login
  
  #### req1.2: Add JWT validation (required)
  - Dependencies: req1.1
  
  #### req1.3: Add password reset (optional)
  - Dependencies: req1.1
```

---

## Validation Logic

### Enhanced Validator

```python
class AdvancedPRDValidator:
    """Validate advanced PRD structures."""
    
    def validate(self, prd: AdvancedPRD) -> PRDValidationResult:
        """Comprehensive validation with nested task support."""
        errors = []
        warnings = []
        
        # Phase 2.4 validations (backward compatible)
        errors.extend(self._validate_metadata(prd.metadata))
        errors.extend(self._validate_duplicate_ids(prd.requirements))
        errors.extend(self._validate_dependencies(prd.requirements))
        
        # Phase 3.1 enhanced validations
        errors.extend(self._validate_parent_child_relationships(prd.requirements))
        errors.extend(self._validate_optional_subtasks(prd.requirements))
        errors.extend(self._validate_cross_project_deps(prd))
        errors.extend(self._validate_priority_conflicts(prd.requirements))
        warnings.extend(self._check_resource_annotations(prd.requirements))
        
        return PRDValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_parent_child_relationships(
        self, 
        requirements: List[AdvancedPRDRequirement]
    ) -> List[str]:
        """Ensure parent_id references exist and no cycles."""
        errors = []
        req_map = {req.id: req for req in requirements}
        
        for req in requirements:
            if req.parent_id:
                # Check parent exists
                if req.parent_id not in req_map:
                    errors.append(
                        f"Requirement {req.id} references non-existent parent {req.parent_id}"
                    )
                
                # Check for cycles in parent chain
                if self._has_parent_cycle(req, req_map):
                    errors.append(
                        f"Requirement {req.id} has circular parent reference"
                    )
        
        return errors
    
    def _validate_optional_subtasks(
        self, 
        requirements: List[AdvancedPRDRequirement]
    ) -> List[str]:
        """Ensure optional subtasks don't have required dependents."""
        errors = []
        req_map = {req.id: req for req in requirements}
        
        for req in requirements:
            if req.optional:
                # Find all requirements that depend on this optional one
                dependents = [r for r in requirements if req.id in r.dependencies]
                required_dependents = [r for r in dependents if not r.optional]
                
                if required_dependents:
                    errors.append(
                        f"Optional requirement {req.id} has required dependents: "
                        f"{[r.id for r in required_dependents]}"
                    )
        
        return errors
    
    def _validate_cross_project_deps(self, prd: AdvancedPRD) -> List[str]:
        """Validate external project dependencies."""
        errors = []
        
        # Collect all external deps from requirements
        all_external_deps = set()
        for req in prd.requirements:
            all_external_deps.update(req.external_dependencies)
        
        # Check all are declared in PRD metadata
        undeclared = all_external_deps - set(prd.external_projects)
        if undeclared:
            errors.append(
                f"External dependencies not declared in PRD metadata: {undeclared}"
            )
        
        return errors
```

---

## Task Decomposition

### PRD Decomposer

```python
class PRDDecomposer:
    """Decompose nested PRD into flat, execution-ready task graph."""
    
    def decompose(self, prd: AdvancedPRD) -> List[PRDTask]:
        """Convert hierarchical PRD into flat task list."""
        tasks = []
        
        for req in prd.requirements:
            # Skip optional subtasks if configured
            if req.optional and not self._should_include_optional(req):
                continue
            
            # Create task with enhanced context
            task = self._requirement_to_task(req, prd)
            tasks.append(task)
        
        # Topological sort (reuse Phase 2.4 logic)
        sorted_tasks = self._topological_sort(tasks)
        
        return sorted_tasks
    
    def _requirement_to_task(
        self, 
        req: AdvancedPRDRequirement, 
        prd: AdvancedPRD
    ) -> PRDTask:
        """Convert requirement to executable task."""
        # Build enhanced description with nesting context
        description = self._build_task_description(req, prd)
        
        return PRDTask(
            id=req.id,
            description=description,
            dependencies=req.dependencies,
            status=TaskStatus.PENDING,
            context={
                "parent_id": req.parent_id,
                "optional": req.optional,
                "priority": req.priority,
                "resources": req.resources,
                "acceptance_criteria": req.acceptance_criteria,
                "external_dependencies": req.external_dependencies
            }
        )
    
    def _build_task_description(
        self, 
        req: AdvancedPRDRequirement, 
        prd: AdvancedPRD
    ) -> str:
        """Build comprehensive task description with context."""
        parts = [req.description]
        
        if req.parent_id:
            parent = self._find_requirement(prd, req.parent_id)
            if parent:
                parts.append(f"(Subtask of: {parent.description})")
        
        if req.acceptance_criteria:
            parts.append(f"Acceptance Criteria: {', '.join(req.acceptance_criteria)}")
        
        if req.external_dependencies:
            parts.append(f"External Dependencies: {', '.join(req.external_dependencies)}")
        
        return " | ".join(parts)
```

---

## Examples

### Nested PRD (Dictionary Format)

```python
advanced_prd = {
    "metadata": {
        "title": "User Management System",
        "version": "2.0",
        "author": "Engineering Team"
    },
    "requirements": [
        {
            "id": "auth",
            "description": "Implement authentication system",
            "priority": "high",
            "subtasks": [
                {
                    "id": "auth.login",
                    "description": "Create login endpoint",
                    "optional": False,
                    "acceptance_criteria": ["Returns JWT on success", "Rate limiting applied"]
                },
                {
                    "id": "auth.logout",
                    "description": "Create logout endpoint",
                    "dependencies": ["auth.login"],
                    "optional": False
                },
                {
                    "id": "auth.password_reset",
                    "description": "Add password reset flow",
                    "dependencies": ["auth.login"],
                    "optional": True  # Nice-to-have
                }
            ]
        },
        {
            "id": "profile",
            "description": "User profile management",
            "dependencies": ["auth"],
            "priority": "medium",
            "subtasks": [
                {
                    "id": "profile.view",
                    "description": "View user profile",
                    "optional": False
                },
                {
                    "id": "profile.edit",
                    "description": "Edit user profile",
                    "dependencies": ["profile.view"],
                    "optional": False
                }
            ]
        }
    ],
    "external_projects": [],
    "resource_limits": {
        "max_parallel_tasks": 2
    }
}
```

---

## Testing Strategy

### Unit Tests
- Parse nested PRD structures (2-3 levels deep)
- Validate parent-child relationships
- Detect optional subtask dependency violations
- Handle cross-project dependencies
- Test backward compatibility with Phase 2.4 flat PRDs

### Integration Tests
- End-to-end nested PRD processing
- Optional subtask inclusion/exclusion
- Task decomposition with nesting
- Execution with hierarchical context

---

## Backward Compatibility

### Phase 2.4 PRDs
- All Phase 2.4 flat PRDs parse unchanged
- `parent_id` defaults to `None` (flat structure)
- `optional` defaults to `False` (all required)
- `priority` defaults to `MEDIUM`

### Migration Path
1. Existing flat PRDs continue working without modification
2. New PRDs can gradually adopt nesting (opt-in)
3. Mixed PRDs supported (some nested, some flat)

---

## Performance Considerations

- **Parsing**: O(n) where n = total requirements (nested + flat)
- **Validation**: O(n²) worst case for dependency checking
- **Decomposition**: O(n log n) for topological sort
- **Target**: < 5 seconds for PRDs with 100+ requirements

---

## Out of Scope

- **Dynamic Nesting**: Task structure defined at parse time, not runtime
- **LLM-Based Decomposition**: Human-authored task hierarchies only
- **Infinite Nesting**: Practical limit of 5 levels deep
- **Auto-Optimization**: No automatic task restructuring

---

## Success Criteria

- ✅ Parse nested PRDs up to 5 levels deep
- ✅ Validate parent-child relationships correctly
- ✅ Enforce optional subtask constraints
- ✅ 100% backward compatible with Phase 2.4
- ✅ All tests passing (target: 50+ tests)

---

## Summary

Phase 3.1 enables hierarchical PRD structures while maintaining full compatibility with Phase 2.4's flat PRD model. All features are deterministic, well-tested, and opt-in.
