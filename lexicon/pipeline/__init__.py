"""
Pipeline module for PRD ingestion and task execution.

This module provides the infrastructure to:
1. Parse Product Requirements Documents (PRDs)
2. Validate PRD structure and content
3. Convert PRDs into executable tasks
4. Execute tasks through the Coordinator

Phase 2.4: Basic PRD support with flat task lists
Phase 3.1: Advanced PRD support with nested task hierarchies

PRDs are inputs, not control logic. They define what to build, not how to build it.
"""

from lexicon.pipeline.prd_models import (
    PRD,
    PRDMetadata,
    PRDRequirement,
    PRDTask,
    PRDValidationResult,
    RequirementPriority,
    RequirementType,
    TaskStatus,
)
from lexicon.pipeline.prd_parser import PRDParser
from lexicon.pipeline.prd_pipeline import PRDPipeline
from lexicon.pipeline.prd_processor import PRDProcessor
from lexicon.pipeline.prd_validator import PRDValidator

# Phase 3.1: Advanced PRD support
from lexicon.pipeline.advanced_prd_models import (
    AdvancedPRD,
    AdvancedPRDRequirement,
    DecomposedTask,
    ResourceType,
)
from lexicon.pipeline.advanced_prd_parser import AdvancedPRDParser
from lexicon.pipeline.advanced_prd_validator import AdvancedPRDValidator
from lexicon.pipeline.prd_decomposer import PRDDecomposer

__all__ = [
    # Phase 2.4 exports
    "PRD",
    "PRDMetadata",
    "PRDRequirement",
    "PRDTask",
    "PRDValidationResult",
    "RequirementPriority",
    "RequirementType",
    "TaskStatus",
    "PRDParser",
    "PRDPipeline",
    "PRDProcessor",
    "PRDValidator",
    # Phase 3.1 exports
    "AdvancedPRD",
    "AdvancedPRDRequirement",
    "DecomposedTask",
    "ResourceType",
    "AdvancedPRDParser",
    "AdvancedPRDValidator",
    "PRDDecomposer",
]
