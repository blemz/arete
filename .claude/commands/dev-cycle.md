# Dev Cycle Command

Implements a complete TDD development cycle for the Enhanced CAM Extraction System.

## Command: /dev-cycle

**Purpose**: Execute a complete development phase using Test-Driven Development methodology, following the roadmap in specs\001-implementar-fluxo-completo\tasks.md and using specs\001-implementar-fluxo-completo\plan.md as reference.

## Execution Steps:

### 1. Read Current Implementation Status
- Use serena, context7 and sequential-thinking MCP proactively to avoid unnecessary mistakes.
- MUST ALWAYS use subagents, prompting orc (orchestrator-agent) to manage execution using the other sub-agents as fit.
- Read @specs\001-implementar-fluxo-completo\tasks.md to understand current progress
- Identify the next phase/component to implement
- Review test coverage and completion status

### 2. TDD Implementation Cycle
- **RED**: Write failing tests first for the target component
- **GREEN**: Implement minimum code to make tests pass
- **REFACTOR**: Improve code structure and maintainability
- Follow our quality criteria: >90% test coverage, production-ready code

### 3. Phase Completion Tasks
- Update specs\001-implementar-fluxo-completo\tasks.md with completion status
- Mark completed components as ✅ COMPLETED
- Update test counts and progress metrics
- Document any architectural decisions or technical achievements

### 4. Git Commit
- Stage all changes: tests, implementation, and documentation updates
- Create meaningful commit message describing the completed phase
- Commit with proper co-authoring attribution

### 5. Cycle Reset
- Execute /clear command to reset chat context
- Ready to continue with next phase implementation

## Quality Criteria:
- ✅ All tests must pass (100% pass rate)
- ✅ Follow Clean Architecture patterns
- ✅ Maintain TDD discipline (Red-Green-Refactor)
- ✅ Production-ready code quality
- ✅ Comprehensive error handling
- ✅ Type safety with Pydantic models

## Continuation Protocol:
- After /clear, the next cycle begins automatically by reading the updated ENHANCED-TODO.md and implementing the next identified phase.

This ensures continuous progress toward completing all remaining components in the Enhanced CAM Extraction System roadmap.