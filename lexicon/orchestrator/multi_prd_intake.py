"""
Multi-PRD Intake for Phase 3.2.1: Normalize multiple PRDs into common format.

This module handles:
- Accepting multiple PRDs (mixed Phase 2.4 and Phase 3.1)
- Normalizing to common DecomposedTask format
- Tracking task-to-PRD mapping
- Calculating statistics

All processing is stateless and deterministic.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any, Dict, List, Union

# Direct imports to avoid circular dependency
from lexicon.pipeline.prd_models import PRD
from lexicon.pipeline.advanced_prd_models import AdvancedPRD, DecomposedTask
from lexicon.pipeline.prd_decomposer import PRDDecomposer


class DuplicateTaskIDError(ValueError):
    """
    Duplicate task IDs detected across PRDs.
    
    This error is raised when multiple PRDs contain tasks with the same ID,
    which would lead to ambiguity and potential data loss during orchestration.
    """
    
    def __init__(self, duplicates: Dict[str, List[str]]):
        """
        Args:
            duplicates: Mapping from task_id to list of prd_ids where it appears
        """
        msg_parts = ["Duplicate task IDs detected:"]
        for task_id, prd_ids in duplicates.items():
            msg_parts.append(
                f"  - Task '{task_id}' appears in PRDs: {', '.join(prd_ids)}"
            )
        super().__init__("\n".join(msg_parts))


@dataclass
class MultiPRDMetadata:
    """
    Metadata for multi-PRD orchestration.
    
    Attributes:
        orchestration_id: Unique identifier for this orchestration run
        created_at: Timestamp when orchestration was initiated
        source: Source of the PRD collection (e.g., "api", "cli", "batch")
        description: Optional description of the orchestration purpose
        tags: Optional tags for categorization
    """
    
    orchestration_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    source: str = "api"
    description: str = ""
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate metadata fields."""
        if not self.orchestration_id or not self.orchestration_id.strip():
            raise ValueError("Orchestration ID cannot be empty")


@dataclass
class MultiPRDInput:
    """
    Input container for multiple PRDs.
    
    Attributes:
        prds: List of PRDs (mixed Phase 2.4 PRD and Phase 3.1 AdvancedPRD)
        metadata: Metadata for this orchestration
    """
    
    prds: List[Union[PRD, AdvancedPRD]]
    metadata: MultiPRDMetadata
    
    def __post_init__(self):
        """Validate input."""
        if not isinstance(self.prds, list):
            raise TypeError("prds must be a list")
        if len(self.prds) == 0:
            raise ValueError("prds list cannot be empty")
        for i, prd in enumerate(self.prds):
            if not isinstance(prd, (PRD, AdvancedPRD)):
                raise TypeError(
                    f"prds[{i}] must be PRD or AdvancedPRD, got {type(prd).__name__}"
                )


@dataclass
class NormalizedPRDCollection:
    """
    Normalized collection of decomposed tasks from multiple PRDs.
    
    This is the output of the Multi-PRD Intake process. All PRDs have been
    normalized into a common DecomposedTask format, ready for further processing.
    
    Attributes:
        tasks: All tasks from all PRDs (in source order, not sorted)
        prd_sources: Mapping from task_id to prd_id showing which PRD each task came from
        task_count_by_prd: Statistics showing how many tasks from each PRD
        prd_metadata: Metadata for each PRD (prd_id -> metadata)
        total_prds: Total number of PRDs processed
        total_tasks: Total number of tasks across all PRDs
        orchestration_metadata: Metadata for the orchestration run
    """
    
    tasks: List[DecomposedTask]
    prd_sources: Dict[str, str]  # task_id -> prd_id
    task_count_by_prd: Dict[str, int]  # prd_id -> count
    prd_metadata: Dict[str, Dict[str, Any]]  # prd_id -> metadata dict
    total_prds: int
    total_tasks: int
    orchestration_metadata: MultiPRDMetadata
    
    def __post_init__(self):
        """Validate normalized collection."""
        if self.total_tasks != len(self.tasks):
            raise ValueError(
                f"total_tasks ({self.total_tasks}) doesn't match len(tasks) ({len(self.tasks)})"
            )
        if self.total_prds != len(self.prd_metadata):
            raise ValueError(
                f"total_prds ({self.total_prds}) doesn't match len(prd_metadata) ({len(self.prd_metadata)})"
            )
        # Verify all tasks are in prd_sources
        task_ids = {task.task_id for task in self.tasks}
        source_task_ids = set(self.prd_sources.keys())
        if task_ids != source_task_ids:
            raise ValueError("Mismatch between tasks and prd_sources")


class MultiPRDIntake:
    """
    Multi-PRD intake processor for Phase 3.2.1.
    
    Responsible for:
    1. Accepting multiple PRDs (mixed Phase 2.4 and 3.1)
    2. Normalizing all PRDs to common DecomposedTask format
    3. Tracking task-to-PRD mappings
    4. Calculating statistics
    
    All processing is stateless and deterministic. The same inputs always
    produce the same outputs.
    """
    
    def __init__(self):
        """Initialize the multi-PRD intake processor."""
        self.prd_decomposer = PRDDecomposer()
    
    def process(self, multi_prd_input: MultiPRDInput) -> NormalizedPRDCollection:
        """
        Process multiple PRDs into a normalized task collection.
        
        This is the main entry point for Phase 3.2.1. It accepts mixed PRD types
        and normalizes them into a common format.
        
        Args:
            multi_prd_input: Input containing multiple PRDs and metadata
            
        Returns:
            NormalizedPRDCollection with all tasks normalized
            
        Raises:
            ValueError: If input validation fails
            TypeError: If PRD types are invalid
        """
        all_tasks = []
        prd_sources = {}
        task_count_by_prd = {}
        prd_metadata = {}
        
        # Process each PRD
        for prd_index, prd in enumerate(multi_prd_input.prds):
            # Generate unique PRD identifier
            prd_id = self._generate_prd_id(prd, prd_index)
            
            # Normalize PRD to tasks
            tasks = self._normalize_prd(prd, prd_id)
            
            # Track statistics
            task_count_by_prd[prd_id] = len(tasks)
            
            # Extract PRD metadata
            prd_metadata[prd_id] = self._extract_prd_metadata(prd, prd_index)
            
            # Add tasks and track sources
            for task in tasks:
                # Check for task ID collisions across PRDs
                if task.task_id in prd_sources:
                    existing_prd_id = prd_sources[task.task_id]
                    raise DuplicateTaskIDError({
                        task.task_id: [existing_prd_id, prd_id]
                    })
                
                all_tasks.append(task)
                prd_sources[task.task_id] = prd_id
        
        # Create normalized collection
        return NormalizedPRDCollection(
            tasks=all_tasks,
            prd_sources=prd_sources,
            task_count_by_prd=task_count_by_prd,
            prd_metadata=prd_metadata,
            total_prds=len(multi_prd_input.prds),
            total_tasks=len(all_tasks),
            orchestration_metadata=multi_prd_input.metadata,
        )
    
    def _generate_prd_id(self, prd: Union[PRD, AdvancedPRD], index: int) -> str:
        """
        Generate a unique PRD identifier.
        
        Uses PRD metadata title and index to create deterministic ID.
        
        Args:
            prd: The PRD
            index: PRD index in the input list
            
        Returns:
            Unique PRD identifier
        """
        # Use metadata title if available, otherwise use index
        if hasattr(prd, 'metadata') and prd.metadata:
            title_slug = prd.metadata.title.lower().replace(" ", "-")
            # Limit slug length and sanitize
            title_slug = "".join(c for c in title_slug if c.isalnum() or c == "-")[:50]
            return f"prd-{index}-{title_slug}"
        return f"prd-{index}"
    
    def _normalize_prd(
        self, prd: Union[PRD, AdvancedPRD], prd_id: str
    ) -> List[DecomposedTask]:
        """
        Normalize a PRD to DecomposedTask format.
        
        Handles both Phase 2.4 PRD and Phase 3.1 AdvancedPRD.
        
        Args:
            prd: The PRD to normalize
            prd_id: Unique identifier for this PRD
            
        Returns:
            List of DecomposedTask objects
            
        Raises:
            TypeError: If PRD type is not supported
        """
        if isinstance(prd, AdvancedPRD):
            # Phase 3.1: Use decomposer
            return self.prd_decomposer.decompose(prd)
        elif isinstance(prd, PRD):
            # Phase 2.4: Convert directly from requirements to DecomposedTask
            # (PRDProcessor has bugs, so we bypass it)
            return self._convert_prd_to_decomposed(prd, prd_id)
        else:
            raise TypeError(f"Unsupported PRD type: {type(prd).__name__}")
    
    def _convert_prd_to_decomposed(self, prd: PRD, prd_id: str) -> List[DecomposedTask]:
        """
        Convert Phase 2.4 PRD directly to DecomposedTask format.
        
        This bypasses PRDProcessor (which has bugs) and converts requirements
        directly to DecomposedTask objects, preserving backward compatibility.
        
        Args:
            prd: Phase 2.4 PRD
            prd_id: Unique identifier for this PRD
            
        Returns:
            List of DecomposedTask objects
        """
        decomposed_tasks = []
        
        # Build mapping for internal dependencies
        # This ensures that internal requirement IDs are correctly mapped to 
        # the new deterministic task IDs.
        req_id_to_task_id = {req.id: f"task-{prd_id}-{req.id}" for req in prd.requirements}
        
        for req in prd.requirements:
            # Generate deterministic task ID using compound key
            task_id = req_id_to_task_id[req.id]
            
            # Map dependencies: transform internal req IDs, preserve others
            mapped_deps = [req_id_to_task_id.get(dep, dep) for dep in req.dependencies]
            
            # Build task description
            description = f"{req.description}\n\nPRD: {prd.metadata.title}\n"
            if req.acceptance_criteria:
                description += "\nAcceptance Criteria:\n"
                for criterion in req.acceptance_criteria:
                    description += f"- {criterion}\n"
            
            # Create DecomposedTask
            decomposed_task = DecomposedTask(
                task_id=task_id,
                requirement_id=req.id,
                description=description,
                dependencies=mapped_deps,  # Use mapped dependencies
                is_optional=False,  # Phase 2.4 tasks are always required
                priority=req.priority.value,  # Use priority from requirement
                resources=[],  # Phase 2.4 doesn't track resources
                context={
                    "requirement_type": req.type.value,
                    "acceptance_criteria": req.acceptance_criteria,
                    "prd_title": prd.metadata.title,
                    "prd_version": prd.metadata.version,
                    "prd_author": prd.metadata.author,
                },
                metadata={
                    "source": "phase_2.4_prd",
                    "estimated_effort": req.estimated_effort,
                },
            )
            decomposed_tasks.append(decomposed_task)
        
        return decomposed_tasks
    
    def _extract_prd_metadata(
        self, prd: Union[PRD, AdvancedPRD], index: int
    ) -> Dict[str, Any]:
        """
        Extract metadata from a PRD for tracking purposes.
        
        Args:
            prd: The PRD
            index: PRD index in the input list
            
        Returns:
            Dictionary of metadata
        """
        metadata = {
            "index": index,
            "type": type(prd).__name__,
        }
        
        if hasattr(prd, 'metadata') and prd.metadata:
            metadata.update({
                "title": prd.metadata.title,
                "version": prd.metadata.version,
                "author": prd.metadata.author,
                "created_at": prd.metadata.created_at.isoformat(),
                "tags": prd.metadata.tags,
            })
        
        if hasattr(prd, 'overview'):
            metadata["overview"] = prd.overview
        
        if isinstance(prd, AdvancedPRD):
            metadata["has_nested_structure"] = prd.has_nested_structure()
            metadata["max_depth"] = prd.get_max_depth()
        
        return metadata
