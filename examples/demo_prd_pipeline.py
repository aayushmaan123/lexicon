"""
Demo: PRD Pipeline - End-to-End Execution

This script demonstrates Phase 2.4 functionality:
1. Creating a PRD from different formats
2. Validating PRDs
3. Converting requirements to tasks
4. Executing tasks through the Coordinator

Note: This demo uses mock agents for demonstration purposes.
In production, real agents would be used with LLM integration.
"""

import json
from lexicon.agents import PlannerAgent, BuilderAgent, ReviewerAgent, FixerAgent
from lexicon.orchestrator.coordinator import Coordinator
from lexicon.pipeline import (
    PRD,
    PRDMetadata,
    PRDRequirement,
    RequirementPriority,
    RequirementType,
    PRDParser,
    PRDValidator,
    PRDProcessor,
    PRDPipeline,
)


def demo_1_create_prd_from_dict():
    """Demo 1: Create and validate a PRD from a dictionary."""
    print("=" * 80)
    print("DEMO 1: Create PRD from Dictionary")
    print("=" * 80)
    
    prd_dict = {
        "metadata": {
            "title": "User Authentication Service",
            "version": "1.0.0",
            "author": "Engineering Team",
            "tags": ["security", "backend", "authentication"],
        },
        "overview": "Implement a secure user authentication service with JWT tokens, "
                   "password hashing, and session management. The service must be "
                   "production-ready with comprehensive security measures.",
        "requirements": [
            {
                "id": "AUTH-001",
                "type": "feature",
                "priority": "critical",
                "description": "Implement password hashing using bcrypt with salt rounds >= 12",
                "acceptance_criteria": [
                    "Passwords are hashed before storage",
                    "Salt rounds configurable but minimum 12",
                    "Old password hashes can be verified",
                ],
                "dependencies": [],
                "estimated_effort": 8.0,
            },
            {
                "id": "AUTH-002",
                "type": "feature",
                "priority": "critical",
                "description": "Implement JWT token generation and validation",
                "acceptance_criteria": [
                    "Tokens include user ID and expiration",
                    "Tokens are signed with secret key",
                    "Token validation includes signature and expiration checks",
                ],
                "dependencies": ["AUTH-001"],
                "estimated_effort": 12.0,
            },
            {
                "id": "AUTH-003",
                "type": "testing",
                "priority": "high",
                "description": "Create comprehensive test suite for authentication",
                "acceptance_criteria": [
                    "Unit tests for password hashing",
                    "Unit tests for JWT operations",
                    "Integration tests for full auth flow",
                    "Security tests for common attack vectors",
                ],
                "dependencies": ["AUTH-001", "AUTH-002"],
                "estimated_effort": 16.0,
            },
        ],
        "constraints": [
            "Must use industry-standard libraries only",
            "No plaintext password storage",
            "Tokens must expire within 24 hours",
        ],
        "out_of_scope": [
            "OAuth integration",
            "Multi-factor authentication",
            "Social login",
        ],
        "success_criteria": [
            "All tests pass",
            "Security audit completed",
            "Documentation complete",
        ],
    }
    
    # Parse PRD
    parser = PRDParser()
    prd = parser.parse_from_dict(prd_dict)
    
    print(f"\nPRD Created:")
    print(f"  Title: {prd.metadata.title}")
    print(f"  Version: {prd.metadata.version}")
    print(f"  Requirements: {len(prd.requirements)}")
    print(f"  Constraints: {len(prd.constraints)}")
    print(f"  Success Criteria: {len(prd.success_criteria)}")
    
    # Validate PRD
    validator = PRDValidator()
    validation_result = validator.validate(prd)
    
    print(f"\nValidation Result:")
    print(f"  Valid: {validation_result.is_valid}")
    print(f"  Errors: {len(validation_result.errors)}")
    print(f"  Warnings: {len(validation_result.warnings)}")
    
    if validation_result.warnings:
        for warning in validation_result.warnings:
            print(f"    - {warning}")
    
    return prd


def demo_2_convert_to_tasks():
    """Demo 2: Convert PRD requirements to tasks."""
    print("\n" + "=" * 80)
    print("DEMO 2: Convert Requirements to Tasks")
    print("=" * 80)
    
    # Create a simple PRD
    prd = PRD(
        metadata=PRDMetadata(
            title="API Endpoint Development",
            version="1.0.0",
            author="Backend Team",
        ),
        overview="Add new REST API endpoints for user management",
        requirements=[
            PRDRequirement(
                id="API-001",
                type=RequirementType.FEATURE,
                priority=RequirementPriority.HIGH,
                description="Create GET /users endpoint",
                acceptance_criteria=["Returns paginated user list", "Supports filtering"],
            ),
            PRDRequirement(
                id="API-002",
                type=RequirementType.FEATURE,
                priority=RequirementPriority.HIGH,
                description="Create POST /users endpoint",
                acceptance_criteria=["Validates input", "Returns created user"],
                dependencies=["API-001"],
            ),
        ],
    )
    
    # Process into tasks
    processor = PRDProcessor()
    tasks = processor.process(prd)
    
    print(f"\nGenerated {len(tasks)} tasks:")
    for i, task in enumerate(tasks, 1):
        print(f"\nTask {i}:")
        print(f"  ID: {task.task_id}")
        print(f"  Requirement: {task.requirement_id}")
        print(f"  Status: {task.status.value}")
        print(f"  Description (first 100 chars): {task.description[:100]}...")
    
    return tasks


def demo_3_execute_prd_pipeline():
    """Demo 3: Execute complete PRD pipeline."""
    print("\n" + "=" * 80)
    print("DEMO 3: Execute Complete PRD Pipeline")
    print("=" * 80)
    
    # Set up Coordinator with agents
    coordinator = Coordinator()
    coordinator.register_agent("planner", PlannerAgent())
    coordinator.register_agent("builder", BuilderAgent())
    coordinator.register_agent("reviewer", ReviewerAgent())
    coordinator.register_agent("fixer", FixerAgent())
    
    print("\nCoordinator initialized with 4 agents")
    
    # Create pipeline
    pipeline = PRDPipeline(coordinator)
    
    # Define PRD
    prd_dict = {
        "metadata": {
            "title": "Simple Feature",
            "version": "1.0.0",
            "author": "Demo",
        },
        "overview": "Demonstrate PRD pipeline with a simple feature",
        "requirements": [
            {
                "id": "DEMO-001",
                "type": "feature",
                "priority": "medium",
                "description": "Add hello world function",
                "acceptance_criteria": ["Function returns 'Hello, World!'"],
            },
        ],
        "success_criteria": ["Feature works as expected"],
    }
    
    print("\nExecuting PRD pipeline...")
    
    # Execute
    result = pipeline.execute_from_dict(prd_dict, validate=True)
    
    print(f"\nExecution Results:")
    print(f"  PRD: {result['prd_title']} v{result['prd_version']}")
    print(f"  Total Tasks: {result['total_tasks']}")
    print(f"  Completed: {result['completed_tasks']}")
    print(f"  Failed: {result['failed_tasks']}")
    print(f"  Overall Success: {result['success']}")
    
    print(f"\nTask Results:")
    for task_result in result['task_results']:
        print(f"  - Task {task_result['task_id']}")
        print(f"    Requirement: {task_result['requirement_id']}")
        print(f"    Status: {task_result['status']}")
        print(f"    Success: {task_result['success']}")
        print(f"    Final State: {task_result['final_state']}")
    
    return result


def demo_4_markdown_prd():
    """Demo 4: Parse PRD from Markdown."""
    print("\n" + "=" * 80)
    print("DEMO 4: Parse PRD from Markdown")
    print("=" * 80)
    
    markdown_prd = """# User Profile Feature

**Version**: 2.0.0
**Author**: Product Team
**Tags**: frontend, user-experience

## Overview

Enhance the user profile page with additional fields and better UX.
Users should be able to view and edit their profile information easily.

## Requirements

### PROFILE-001: Add Bio Field (priority: medium, type: feature)

Add a biography text field to user profiles. Maximum 500 characters.

**Acceptance Criteria**:
- Bio field appears on profile page
- Character count displayed
- Bio is optional

**Effort**: 4

### PROFILE-002: Add Avatar Upload (priority: high, type: feature)

Allow users to upload profile avatars. Support JPG and PNG formats.

**Acceptance Criteria**:
- File upload button present
- Image preview before save
- Images resized to 200x200px

**Dependencies**: PROFILE-001
**Effort**: 8

## Constraints
- Avatar files must be < 5MB
- PII must be handled securely

## Out of Scope
- Video uploads
- GIF support

## Success Criteria
- All acceptance criteria met
- Performance impact < 100ms
"""
    
    parser = PRDParser()
    prd = parser.parse_from_markdown(markdown_prd)
    
    print(f"\nParsed Markdown PRD:")
    print(f"  Title: {prd.metadata.title}")
    print(f"  Version: {prd.metadata.version}")
    print(f"  Author: {prd.metadata.author}")
    print(f"  Tags: {', '.join(prd.metadata.tags)}")
    print(f"  Requirements: {len(prd.requirements)}")
    
    for req in prd.requirements:
        print(f"\n  Requirement {req.id}:")
        print(f"    Type: {req.type.value}")
        print(f"    Priority: {req.priority.value}")
        print(f"    Dependencies: {req.dependencies or 'None'}")
        print(f"    Acceptance Criteria: {len(req.acceptance_criteria)}")
    
    return prd


def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("PRD PIPELINE DEMONSTRATION")
    print("Phase 2.4: PRD → Task → Execution")
    print("=" * 80)
    
    try:
        # Demo 1: Create from dict
        prd1 = demo_1_create_prd_from_dict()
        
        # Demo 2: Convert to tasks
        tasks = demo_2_convert_to_tasks()
        
        # Demo 3: Execute pipeline
        result = demo_3_execute_prd_pipeline()
        
        # Demo 4: Markdown parsing
        prd4 = demo_4_markdown_prd()
        
        print("\n" + "=" * 80)
        print("ALL DEMOS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
