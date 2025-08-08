# Tests Directory - Claude Memory

## Testing Philosophy & Strategy

The Arete project follows **Test-Driven Development (TDD)** principles strictly. All tests are written before implementation, following the Red-Green-Refactor cycle.

## Test Organization & Structure

```
tests/
├── CLAUDE.md               # This file - testing memory
├── __init__.py             # Test package initialization
├── conftest.py             # Shared fixtures and configuration
├── unit/                   # Unit tests (isolated components)
│   ├── __init__.py
│   ├── test_config.py ✅    # Configuration tests (COMPLETED)
│   ├── test_models.py 🔄    # Data model tests (IN PROGRESS)
│   ├── test_services.py     # Service layer tests (PENDING)
│   └── test_utils.py        # Utility function tests (PENDING)
├── integration/             # Integration tests (database/external)
│   ├── __init__.py
│   ├── test_neo4j.py       # Neo4j integration tests (PENDING)
│   ├── test_weaviate.py    # Weaviate integration tests (PENDING)
│   └── test_database.py    # Cross-database tests (PENDING)
├── end_to_end/             # End-to-end system tests
│   ├── __init__.py
│   ├── test_rag_pipeline.py # Full RAG pipeline tests (PENDING)
│   └── test_ui.py          # UI interaction tests (PENDING)
└── fixtures/               # Test data and fixtures
    ├── documents/          # Sample philosophical texts
    ├── entities/           # Sample entity data
    └── responses/          # Expected response samples
```

## Testing Standards & Requirements

### Coverage Requirements
- **Minimum**: 90% coverage for all new code
- **Target**: 95% coverage for critical paths
- **Current**: 79% (config.py completed)
- **Measurement**: `pytest --cov=src/arete --cov-report=html`

### Test Categories & Markers
```python
# pytest.ini configuration
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "end_to_end: marks tests as end-to-end tests",
    "philosophy: marks tests requiring philosophical expertise"
]
```

### Running Tests
```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests only  
pytest tests/integration/ -v

# Exclude slow tests
pytest tests/ -m "not slow"

# With coverage
pytest tests/ -v --cov=src/arete --cov-report=html

# Parallel execution
pytest tests/ -n auto
```

## TDD Implementation Pattern

### 1. RED: Write Failing Test First
```python
# test_document.py
def test_document_creation_with_valid_data():
    """Test creating a document with valid philosophical text."""
    document_data = {
        "title": "Republic",
        "author": "Plato",
        "content": "Justice is the excellence of the soul, and injustice the defect of the soul.",
        "language": "English",
        "source": "Perseus Digital Library"
    }
    
    # This will fail initially - Document class doesn't exist yet
    document = Document(**document_data)
    
    assert document.title == "Republic"
    assert document.author == "Plato"
    assert document.word_count > 0
    assert document.language == "English"
    assert len(document.content) > 50
```

### 2. GREEN: Minimal Implementation
```python
# src/arete/models/document.py
from pydantic import BaseModel

class Document(BaseModel):
    title: str
    author: str
    content: str
    language: str = "English"
    source: str = ""
    
    @property
    def word_count(self) -> int:
        return len(self.content.split())
```

### 3. REFACTOR: Add Validation & Features
```python
# Enhanced implementation
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any

class Document(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    author: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10)
    language: str = Field(default="English", pattern="^[A-Za-z]+$")
    source: Optional[str] = Field(None, max_length=500)
    
    @field_validator("content")
    @classmethod
    def validate_content_length(cls, v: str) -> str:
        if len(v.strip()) < 10:
            raise ValueError("Content must be at least 10 characters")
        return v.strip()
    
    @property
    def word_count(self) -> int:
        return len(self.content.split())
```

## Completed Test Suite: test_config.py

### Test Coverage: 7/7 tests passing
```python
class TestSettings:
    """Comprehensive configuration testing."""
    
    def test_settings_defaults(self):
        """Test default configuration values."""
        # Validates all default settings are correct
        
    def test_settings_from_environment(self, monkeypatch):
        """Test loading from environment variables."""
        # Validates env var loading with monkeypatch
        
    def test_settings_validation(self):
        """Test Pydantic validation rules."""
        # Validates field constraints and type checking
        
    def test_settings_from_env_file(self, tmp_path):
        """Test loading from .env files."""
        # Validates file-based configuration
        
    def test_get_settings_singleton(self):
        """Test singleton pattern implementation."""
        # Validates caching behavior
        
    def test_settings_repr(self):
        """Test secure representation (no password leak)."""
        # Validates security considerations
        
    def test_database_url_properties(self):
        """Test computed properties."""
        # Validates derived fields and methods
```

### Key Testing Patterns Established

#### 1. Fixture-Based Test Data
```python
@pytest.fixture
def sample_settings():
    """Provide consistent test settings."""
    return Settings(
        neo4j_uri="bolt://test:7687",
        neo4j_username="test_user",
        neo4j_password="test_pass"
    )
```

#### 2. Environment Variable Testing
```python
def test_env_var_loading(self, monkeypatch):
    """Test environment variable precedence."""
    monkeypatch.setenv("NEO4J_URI", "bolt://env:7687")
    settings = Settings()
    assert settings.neo4j_uri == "bolt://env:7687"
```

#### 3. Validation Testing
```python
def test_invalid_configuration():
    """Test validation catches invalid values."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(max_context_tokens=-1)
    assert "greater than or equal to 1000" in str(exc_info.value)
```

#### 4. Security Testing
```python
def test_password_security():
    """Test passwords are not exposed."""
    settings = Settings(neo4j_password="secret123")
    repr_str = repr(settings)
    assert "secret123" not in repr_str
```

## Test Fixtures & Data

### Global Fixtures (conftest.py - TO BE CREATED)
```python
import pytest
from pathlib import Path
from arete.config import Settings
from arete.models import Document, Entity

@pytest.fixture(scope="session")
def test_settings():
    """Test-specific settings."""
    return Settings(
        neo4j_uri="bolt://localhost:7687",
        neo4j_username="test",
        neo4j_password="test",
        log_level="DEBUG"
    )

@pytest.fixture
def sample_philosophical_text():
    """Sample philosophical text for testing."""
    return """
    The unexamined life is not worth living. This famous declaration by Socrates
    at his trial represents a fundamental principle of philosophical inquiry.
    To examine one's life means to question assumptions, seek truth, and
    pursue wisdom through rational discourse.
    """

@pytest.fixture
def sample_document(sample_philosophical_text):
    """Create sample Document for testing."""
    return Document(
        title="Apology",
        author="Plato", 
        content=sample_philosophical_text,
        language="English",
        source="Perseus Digital Library"
    )

@pytest.fixture
def sample_entities():
    """Sample entities for testing."""
    return [
        Entity(name="Socrates", type="Person", description="Greek philosopher"),
        Entity(name="Wisdom", type="Concept", description="Love of knowledge"),
        Entity(name="Virtue", type="Concept", description="Excellence of character")
    ]
```

### Philosophical Test Data
```python
# fixtures/documents/plato_republic_excerpt.py
REPUBLIC_EXCERPT = {
    "title": "Republic",
    "author": "Plato",
    "content": """
    Justice is the excellence of the soul, and injustice the defect of the soul.
    But excellence implies knowledge, and defect implies ignorance. 
    Therefore, the just soul and the just man will live well, 
    and the unjust man will live ill.
    """,
    "metadata": {
        "translator": "Benjamin Jowett",
        "stephanus_page": "353e",
        "book": "I",
        "source": "Perseus Digital Library"
    }
}
```

## Database Testing Patterns

### Neo4j Integration Tests (PENDING)
```python
import pytest
from neo4j import GraphDatabase
from arete.graph.client import Neo4jClient

@pytest.fixture(scope="session") 
def neo4j_test_session():
    """Provide clean Neo4j test session."""
    # Setup test database
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("test", "test"))
    
    with driver.session() as session:
        # Clear test data
        session.run("MATCH (n) DETACH DELETE n")
        yield session
        
    # Cleanup after tests
    driver.close()

def test_document_creation_in_neo4j(neo4j_test_session, sample_document):
    """Test creating document in Neo4j."""
    client = Neo4jClient(neo4j_test_session)
    result = client.create_document(sample_document)
    
    assert result.id is not None
    assert result.title == sample_document.title
```

### Weaviate Integration Tests (PENDING) 
```python
import pytest
import weaviate
from arete.rag.client import WeaviateClient

@pytest.fixture(scope="session")
def weaviate_test_client():
    """Provide clean Weaviate test client."""
    client = weaviate.Client("http://localhost:8080")
    
    # Clean test data
    client.schema.delete_all()
    
    # Setup test schema
    client.schema.create_class({
        "class": "TestDocument",
        "properties": [
            {"name": "title", "dataType": ["text"]},
            {"name": "content", "dataType": ["text"]}
        ]
    })
    
    yield client
    
    # Cleanup
    client.schema.delete_all()

def test_document_embedding_storage(weaviate_test_client, sample_document):
    """Test storing document embeddings in Weaviate."""
    client = WeaviateClient(weaviate_test_client)
    result = client.store_document(sample_document)
    
    assert result.id is not None
    assert result.vector is not None
    assert len(result.vector) == 768  # Expected embedding size
```

## Performance Testing

### Load Testing Pattern (PENDING)
```python
import pytest
import time
from concurrent.futures import ThreadPoolExecutor

@pytest.mark.slow
def test_concurrent_query_performance():
    """Test system handles concurrent queries."""
    def single_query():
        # Simulate user query
        return query_service.ask("What is virtue?")
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(single_query) for _ in range(50)]
        results = [f.result() for f in futures]
    
    elapsed = time.time() - start_time
    
    # Performance assertions
    assert elapsed < 30  # Should complete within 30 seconds
    assert all(r.answer for r in results)  # All queries should succeed
    assert len(set(r.answer for r in results)) > 1  # Responses should vary
```

## Error Handling Tests

### Exception Testing Pattern
```python
from arete.exceptions import AreteException, ValidationError

def test_document_validation_errors():
    """Test document validation catches errors."""
    
    # Test empty title
    with pytest.raises(ValidationError) as exc_info:
        Document(title="", author="Plato", content="Some content")
    assert "min_length" in str(exc_info.value)
    
    # Test short content
    with pytest.raises(ValidationError):
        Document(title="Title", author="Author", content="Short")
    
    # Test invalid language
    with pytest.raises(ValidationError):
        Document(title="Title", author="Author", content="Content", language="123")
```

## Philosophical Accuracy Testing

### Expert Validation Pattern (PLANNED)
```python
@pytest.mark.philosophy
def test_aristotle_virtue_ethics_accuracy():
    """Test accuracy of Aristotelian virtue ethics responses."""
    query = "What is Aristotle's concept of eudaimonia?"
    response = rag_system.generate_response(query)
    
    # Content accuracy checks
    assert "flourishing" in response.answer.lower()
    assert "highest good" in response.answer.lower()
    assert any("Nicomachean Ethics" in c.source for c in response.citations)
    
    # Citation verification
    for citation in response.citations:
        assert citation.page_number is not None
        assert citation.book_reference is not None
        
    # Expert validation (manual review flagged)
    assert response.requires_expert_review == False
```

## Next Testing Priorities

1. **Complete Document Model Tests** (IN PROGRESS)
   - Comprehensive validation testing
   - Serialization/deserialization tests
   - Performance benchmarks

2. **Entity Model Tests** (NEXT)
   - Relationship management tests
   - Type validation tests
   - Confidence scoring tests

3. **Database Integration Tests**
   - Neo4j connection and CRUD operations
   - Weaviate embedding storage/retrieval
   - Cross-database consistency tests

4. **RAG Pipeline Tests**
   - End-to-end query processing
   - Retrieval accuracy measurements
   - Response quality validation

## Common Test Commands

```bash
# Development testing
pytest tests/unit/ -v --tb=short

# Integration testing (requires databases)
pytest tests/integration/ -v

# Full test suite with coverage
pytest tests/ -v --cov=src/arete --cov-report=html --cov-report=term-missing

# Performance tests only
pytest tests/ -m slow -v

# Philosophy accuracy tests
pytest tests/ -m philosophy -v

# Watch mode for TDD
pytest-watch tests/unit/test_models.py
```

---

**Last Updated**: 2025-08-08  
**Current Focus**: Document model test completion following TDD  
**Coverage Target**: 95% for all critical path components