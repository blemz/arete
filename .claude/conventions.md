# Arete Development Conventions

## Test-Driven Development (TDD)

### Definition
TDD is an iterative software development methodology where you **always write failing unit tests before writing the actual functional code**. This is **mandatory** for all Arete development.

### Red-Green-Refactor Cycle

1. **Red**: Define a unit test for a specific function or feature that does not yet exist. The test must fail because the supporting code is missing.

2. **Green**: Write the minimum code required to make the failing test pass. At this stage, focus solely on correctness, not polish.

3. **Refactor**: Once the test passes, improve the code's structure, readability, and maintainability, ensuring all existing tests remain green.

### Core TDD Principles

**Clarity of Purpose**: The end goal is always clear, maintainable, and idiomatic code that is production-ready. *Always keep this principle in mind.*

**No Test Compromise**: Never weaken or simplify a test just to make it pass; doing so harms correctness and usability. If a test fails, fix the underlying code so the real-world behavior is correct.

**Test Quality**: Prioritize writing tests that are meaningful, relevant, and aligned with the feature's actual use cases.

**Feature Policy**: Every new feature must include both the implementation and its tests, committed together.

**Lifecycle Discipline**: Apply the TDD process consistently for all changes (new features, bug fixes, refactors) across the entire project lifecycle.

### Testing Standards

**Coverage Requirements**:
- Minimum 80% code coverage for new code
- Target 90%+ coverage for critical components
- 100% coverage for core business logic

**Test Organization**:
```
tests/
├── unit/              # Unit tests for individual components
├── integration/       # Integration tests for component interactions
├── e2e/              # End-to-end tests for user flows
└── fixtures/         # Shared test fixtures and mock data
```

**Test Naming Convention**:
```python
def test_<component>_<scenario>_<expected_result>():
    """Test that <component> <expected_result> when <scenario>."""
    # Arrange
    # Act
    # Assert
```

**Example**:
```python
def test_chunk_service_creates_chunks_with_correct_positions():
    """Test that ChunkService creates chunks with sequential positions."""
    # Arrange
    service = ChunkService()
    text = "Sample philosophical text for chunking."

    # Act
    chunks = service.create_chunks(text)

    # Assert
    assert len(chunks) > 0
    assert chunks[0].position == 0.0
    assert all(chunks[i].position < chunks[i+1].position
               for i in range(len(chunks)-1))
```

## Code Quality Standards

### Type Safety

**Type Hints**: All functions must include type hints for parameters and return values.

```python
# Good
def process_text(text: str, max_length: int) -> List[str]:
    """Process text into chunks."""
    pass

# Bad
def process_text(text, max_length):
    """Process text into chunks."""
    pass
```

**Pydantic Models**: Use Pydantic for all data models to ensure validation.

```python
from pydantic import BaseModel, Field

class Entity(BaseModel):
    """Philosophical entity model."""
    id: str
    name: str
    entity_type: str
    description: str = Field(default="")
    properties: dict = Field(default_factory=dict)
```

**Static Type Checking**: Run mypy before committing code.

```bash
mypy src/arete
```

### Code Style

**Formatting**: Use Black with default settings (88 character line length).

```bash
black src/arete tests
```

**Linting**: Use Ruff for fast, comprehensive linting.

```bash
ruff check src/arete tests
```

**Import Order**: Follow isort conventions:
1. Standard library imports
2. Third-party imports
3. Local application imports

```python
# Standard library
import os
from typing import List, Optional

# Third-party
import numpy as np
from pydantic import BaseModel

# Local
from arete.models import Chunk, Entity
from arete.services import ChunkService
```

### Documentation

**Docstrings**: Use Google-style docstrings for all public functions and classes.

```python
def create_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """Create an embedding vector for the given text.

    Args:
        text: The text to embed
        model: The embedding model to use

    Returns:
        A list of float values representing the embedding vector

    Raises:
        ValueError: If text is empty
        APIError: If the embedding service is unavailable
    """
    pass
```

**Comments**: Use comments sparingly, preferring self-documenting code. Add comments for:
- Complex algorithms
- Non-obvious business logic
- Workarounds for external library issues

### Error Handling

**Explicit Error Handling**: Catch specific exceptions, not broad Exception classes.

```python
# Good
try:
    result = api_call()
except APIError as e:
    logger.error(f"API call failed: {e}")
    raise

# Bad
try:
    result = api_call()
except Exception:
    pass
```

**Logging**: Use structured logging with appropriate levels.

```python
import logging

logger = logging.getLogger(__name__)

# Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
logger.info("Processing started", extra={"document_id": doc_id})
logger.error("Processing failed", extra={"error": str(e), "document_id": doc_id})
```

## Repository Pattern

### Structure

All database interactions go through repository classes:

```python
class ChunkRepository:
    """Repository for chunk data access."""

    def __init__(self, client: WeaviateClient):
        self.client = client

    def save(self, chunk: Chunk) -> str:
        """Save a chunk to the database."""
        pass

    def find_by_id(self, chunk_id: str) -> Optional[Chunk]:
        """Find a chunk by ID."""
        pass

    def search_by_similarity(self,
                            embedding: List[float],
                            limit: int = 10) -> List[SearchResult]:
        """Search for similar chunks."""
        pass
```

### Benefits
- Clean separation of concerns
- Easy to test with mock repositories
- Consistent interface across data sources
- Simple to swap implementations

## Performance Guidelines

### Database Operations
- Use batch operations when processing multiple items
- Implement connection pooling for all database clients
- Cache frequently accessed data
- Use indexes on commonly queried fields

### Memory Management
- Stream large files instead of loading into memory
- Release database connections promptly
- Use generators for large collections
- Profile memory usage for resource-intensive operations

### Async Operations
- Use async/await for I/O-bound operations
- Implement proper timeout handling
- Use connection pooling for async clients

## Educational Focus

### Citation Requirements
- All philosophical claims must be backed by source citations
- Citations include: text reference, position, relevance score
- Preserve philosophical context in responses

### Pedagogical Value
- Prioritize educational accuracy over response speed
- Provide complete philosophical arguments, not summaries
- Include Greek terminology with transliterations
- Cross-reference related concepts across dialogues

## Security Guidelines

### Input Validation
- Validate all user inputs with Pydantic models
- Sanitize text inputs to prevent injection attacks
- Limit input sizes to prevent DoS

### API Keys & Secrets
- Never commit API keys to version control
- Use environment variables for all secrets
- Rotate API keys regularly
- Use different keys for dev/staging/prod

### Data Privacy
- No PII in logs
- Secure database connections
- HTTPS only in production

## Git Workflow

### Branch Naming
```
feature/<description>    # New features
bugfix/<description>     # Bug fixes
refactor/<description>   # Code refactoring
docs/<description>       # Documentation updates
```

### Commit Messages
Follow conventional commits format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

Example:
```
feat(rag): Add GPT-5-mini reasoning model support

Implement support for OpenAI's GPT-5-mini with:
- Extended timeout handling (180s)
- max_completion_tokens parameter
- Temperature restriction handling

Improves response quality by 40% for complex philosophical queries.
```

### Pull Request Guidelines
1. Create feature branch from main
2. Implement with TDD methodology
3. Ensure all tests pass
4. Update documentation
5. Request code review
6. Address review comments
7. Squash commits if needed
8. Merge to main

## Code Review Checklist

- [ ] All tests pass (unit, integration, e2e)
- [ ] Code coverage meets minimum threshold (80%+)
- [ ] Type hints present and correct
- [ ] Documentation updated (docstrings, README, etc.)
- [ ] No linting errors
- [ ] Performance impact considered
- [ ] Security implications reviewed
- [ ] Accessibility maintained (for UI changes)
- [ ] Error handling implemented
- [ ] Logging added for key operations

## Development Environment

### Required Tools
- Python 3.10+
- Neo4j
- Weaviate
- Redis (optional)
- Git
- Docker (for deployment)

### Recommended IDE Setup
- VSCode with Python extension
- Pylance for type checking
- Black formatter integration
- Pytest runner
- GitLens for Git integration

### Environment Variables
Required variables in `.env`:
```
# Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

WEAVIATE_URL=http://localhost:8080

# LLM Provider (choose one)
KG_LLM_PROVIDER=openai  # openai, anthropic, gemini, openrouter, ollama
OPENAI_API_KEY=your_key

# Embedding Provider
EMBEDDING_PROVIDER=openai  # openai, gemini, openrouter, anthropic, ollama
```

## Common Pitfalls to Avoid

### Don't Simplify Tests to Pass
❌ **Bad**: Changing test to match broken code
```python
def test_chunk_count():
    chunks = create_chunks("text")
    assert len(chunks) == 3  # Changed from 5 to match buggy output
```

✅ **Good**: Fix the code to pass the correct test
```python
def test_chunk_count():
    chunks = create_chunks("text")
    assert len(chunks) == 5  # Correct expectation, fix create_chunks()
```

### Don't Use Unicode in Code
❌ **Bad**: Unicode characters that may break on Windows
```python
message = "Process completed ✓"
```

✅ **Good**: ASCII-safe alternatives
```python
message = "Process completed [OK]"
```

### Don't Skip Type Hints
❌ **Bad**: Missing type information
```python
def process(data):
    return data.split()
```

✅ **Good**: Complete type annotations
```python
def process(data: str) -> List[str]:
    return data.split()
```

---

**Last Updated**: 2025-11-05
**Related**: [Architecture](.claude/architecture.md), [Troubleshooting](.claude/troubleshooting.md)
