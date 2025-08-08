# Source Code Directory - Claude Memory

## Directory Purpose
This directory contains the main application source code for the Arete Graph-RAG system. All business logic, data models, and core functionality is implemented here.

## Module Structure & Status

```
src/arete/
├── __init__.py              # Package initialization
├── config.py ✅             # Configuration management (COMPLETED)
├── models/                  # Data models and schemas
│   ├── __init__.py
│   ├── document.py 🔄       # Document model (IN PROGRESS)
│   ├── entity.py           # Entity model (PENDING)
│   ├── chunk.py            # Text chunk model (PENDING)
│   ├── citation.py         # Citation model (PENDING)
│   └── relationship.py     # Relationship model (PENDING)
├── graph/                  # Neo4j operations
│   ├── __init__.py
│   ├── client.py           # Neo4j client (PENDING)
│   ├── operations.py       # CRUD operations (PENDING)
│   └── queries.py          # Cypher queries (PENDING)
├── rag/                    # RAG system components
│   ├── __init__.py
│   ├── retriever.py        # Hybrid retrieval (PENDING)
│   ├── generator.py        # Response generation (PENDING)
│   ├── embeddings.py       # Embedding management (PENDING)
│   └── fusion.py           # Result fusion (PENDING)
├── services/               # Business logic services
│   ├── __init__.py
│   ├── document_service.py # Document processing (PENDING)
│   ├── query_service.py    # Query processing (PENDING)
│   └── validation_service.py # Response validation (PENDING)
├── pipelines/              # Data processing pipelines
│   ├── __init__.py
│   ├── text_processing.py  # Text chunking and cleaning (PENDING)
│   ├── entity_extraction.py # NER pipeline (PENDING)
│   └── knowledge_graph.py  # Graph construction (PENDING)
└── ui/                     # User interface components
    ├── __init__.py
    ├── streamlit_app.py    # Main Streamlit app (PENDING)
    └── components/         # Reusable UI components (PENDING)
```

## Coding Standards & Patterns

### Import Organization
```python
# Standard library imports
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Third-party imports
from pydantic import BaseModel, Field, validator
import neo4j
import weaviate

# Local imports
from arete.config import get_settings
from arete.models.base import BaseEntity
```

### Type Hints (Required)
```python
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel

# Always provide return type hints
def process_document(content: str, metadata: Dict[str, Any]) -> Document:
    """Process a document and return validated Document instance."""
    pass

# Use Optional for nullable values
def find_entity(name: str) -> Optional[Entity]:
    """Find entity by name, return None if not found."""
    pass

# Use Union for multiple possible types
def parse_content(source: Union[str, Path]) -> str:
    """Parse content from string or file path."""
    pass
```

### Error Handling Pattern
```python
from loguru import logger
from arete.exceptions import AreteException, ValidationError

def safe_operation() -> Optional[Result]:
    """Example of proper error handling."""
    try:
        # Attempt operation
        result = risky_operation()
        logger.info("Operation completed successfully", extra={"result_id": result.id})
        return result
        
    except ValidationError as e:
        logger.warning("Validation failed", extra={"error": str(e)})
        return None
        
    except AreteException as e:
        logger.error("Arete-specific error", extra={"error": str(e)})
        raise
        
    except Exception as e:
        logger.error("Unexpected error", extra={"error": str(e)})
        raise AreteException(f"Operation failed: {e}") from e
```

### Pydantic Model Pattern (Established)
```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

class PhilosophicalModel(BaseModel):
    """Base pattern for all philosophical domain models."""
    
    # Required fields with validation
    name: str = Field(..., min_length=1, description="Entity name")
    
    # Optional fields with defaults
    description: Optional[str] = Field(None, description="Entity description")
    
    # Computed fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Custom validation
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and normalize name field."""
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()
    
    # Business logic methods
    def to_neo4j_dict(self) -> Dict[str, Any]:
        """Convert to Neo4j-compatible dictionary."""
        return self.model_dump(exclude={'created_at'})
```

## Completed Implementation: config.py

### Features
- ✅ Environment variable loading with `.env` support
- ✅ Pydantic validation for all configuration values
- ✅ Secure password handling (excluded from repr)
- ✅ Singleton pattern for settings access
- ✅ Logging configuration management
- ✅ Type safety with strict validation

### Usage Pattern
```python
from arete.config import get_settings, setup_logging

# Get settings (cached singleton)
settings = get_settings()

# Use in other modules
neo4j_client = Neo4jClient(
    uri=settings.neo4j_uri,
    auth=settings.neo4j_auth
)

# Setup logging
setup_logging()
```

### Test Coverage: 79% (7/7 tests passing)

## In Progress: models/document.py

### Current Status
- 🔄 Writing comprehensive tests following TDD
- ⏳ Implementation pending test completion

### Planned Features
- Pydantic model with full validation
- Word count and metadata extraction
- Neo4j and Weaviate serialization methods
- Citation tracking and reference management

## Architectural Decisions

### Database Abstraction
- **Pattern**: Repository pattern for database operations
- **Clients**: Separate client classes for Neo4j and Weaviate
- **Models**: Pydantic models with database serialization methods

### Service Layer
- **Separation**: Clear separation between data models and business logic
- **Dependency Injection**: Services receive dependencies through constructors
- **Error Handling**: Consistent error handling across all services

### RAG System
- **Hybrid Retrieval**: Dense + sparse retrieval with result fusion
- **Caching**: Aggressive caching for embeddings and query results
- **Validation**: Multi-stage validation for response accuracy

## Performance Considerations

### Memory Management
```python
# Use generators for large datasets
def process_documents(documents: List[Document]) -> Iterator[ProcessedDocument]:
    """Process documents lazily to manage memory."""
    for doc in documents:
        yield process_single_document(doc)

# Implement connection pooling
@lru_cache(maxsize=1)
def get_neo4j_driver() -> neo4j.Driver:
    """Get cached Neo4j driver instance."""
    settings = get_settings()
    return neo4j.GraphDatabase.driver(
        settings.neo4j_uri,
        auth=settings.neo4j_auth
    )
```

### Caching Strategy
```python
from functools import lru_cache
from typing import List

# Cache expensive computations
@lru_cache(maxsize=1000)
def get_embeddings(text: str) -> List[float]:
    """Get cached embeddings for text."""
    # Expensive embedding computation
    pass

# Use Redis for distributed caching (planned)
async def get_cached_result(key: str) -> Optional[Any]:
    """Get result from Redis cache."""
    pass
```

## Testing Patterns

### Test File Organization
```
tests/
├── unit/                   # Unit tests (isolated)
│   ├── test_config.py ✅
│   ├── test_models.py
│   └── test_services.py
├── integration/            # Integration tests (database)
│   ├── test_neo4j.py
│   └── test_weaviate.py
└── end_to_end/            # E2E tests (full system)
    └── test_rag_pipeline.py
```

### Test Fixtures Pattern
```python
# tests/conftest.py
import pytest
from arete.models import Document, Entity

@pytest.fixture
def sample_document() -> Document:
    """Create sample document for testing."""
    return Document(
        title="Republic",
        author="Plato",
        content="Justice is the excellence of the soul...",
        language="English"
    )

@pytest.fixture
def neo4j_test_session():
    """Provide test Neo4j session."""
    # Setup test database
    yield session
    # Cleanup
```

## Logging Standards

### Structured Logging Pattern
```python
from loguru import logger

# Information logging
logger.info(
    "Document processed successfully",
    extra={
        "document_id": doc.id,
        "word_count": doc.word_count,
        "processing_time": elapsed_time
    }
)

# Error logging with context
logger.error(
    "Failed to extract entities",
    extra={
        "document_id": doc.id,
        "error_type": type(e).__name__,
        "error_message": str(e)
    }
)
```

## Security Guidelines

### Input Validation
```python
from pydantic import BaseModel, validator

class UserQuery(BaseModel):
    """User query with validation."""
    
    query: str = Field(..., min_length=1, max_length=1000)
    context: Optional[str] = Field(None, max_length=5000)
    
    @validator("query")
    def sanitize_query(cls, v):
        """Sanitize user query for safety."""
        # Remove potentially dangerous characters
        return v.strip()
```

### Database Query Safety
```python
# Always use parameterized queries
def find_documents_by_author(author: str) -> List[Document]:
    """Find documents by author using safe query."""
    query = """
    MATCH (d:Document {author: $author})
    RETURN d
    """
    # Neo4j driver automatically handles parameterization
    return session.run(query, author=author)
```

## Next Implementation Priorities

1. **Complete Document Model** (In Progress)
   - Finish comprehensive tests
   - Implement model with all validation
   - Add Neo4j/Weaviate serialization

2. **Entity Model** (Next)
   - Design entity type system
   - Implement relationship tracking
   - Add confidence scoring

3. **Database Client Layer**
   - Neo4j connection management
   - Weaviate client wrapper
   - Health check implementations

4. **Text Processing Pipeline**
   - PDF parsing with pymupdf4llm
   - TEI-XML processing for classical texts
   - Intelligent chunking algorithm

---

**Last Updated**: 2025-08-08  
**Current Focus**: Document model implementation following TDD  
**Next Milestone**: Complete all core models with >95% test coverage