# Memory System Migration Complete

Testing strategy and TDD workflow information has been migrated to the hybrid memory system.

## Testing Information Now Located At:

- **Testing Strategy**: `../.memory/development/workflows.md` → [MemoryID: 20250810-MM24]
- **TDD Patterns**: `../.memory/architecture/patterns.md` → [MemoryID: 20250810-MM03]
- **Development Workflows**: `../.memory/development/workflows.md`

## Key Testing Standards (Quick Reference):
- **Coverage**: >90% minimum, >95% target for critical paths  
- **TDD Workflow**: Red-Green-Refactor cycle strictly followed
- **Philosophy Testing**: Specialized `@pytest.mark.philosophy` tests for content accuracy
- **Performance Testing**: `@pytest.mark.slow` for load and performance validation

## Current Test Structure:

```
tests/
├── unit/                   # Unit tests (>95% coverage target)
├── integration/            # Database/external service integration tests  
├── end_to_end/            # Full system workflow validation
└── fixtures/              # Test data including philosophical text samples
```

## Quick Commands:
```bash
# Full test suite with coverage
pytest tests/ -v --cov=src/arete --cov-report=html --cov-fail-under=90

# TDD watch mode
pytest-watch tests/unit/test_models.py

# Philosophy accuracy tests
pytest tests/ -m philosophy -v
```


For complete testing documentation, patterns, and TDD workflows, see the hybrid memory system at `../.memory/`.