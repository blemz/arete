# Models Module Documentation

## Overview

The models module defines all data structures using Pydantic for validation and type safety. Models represent domain entities, chunks, relationships, and configuration objects.

## Core Models

### Chunk

**Purpose**: Represents a semantic text chunk with embeddings and metadata.

**File**: `models/chunk.py`

**Schema**:
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class Chunk(BaseModel):
    """Semantic text chunk with vector embedding."""

    id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document ID")
    content: str = Field(..., description="Chunk text content")
    position: float = Field(..., description="Position in document (0.0-1.0)")
    word_count: int = Field(..., description="Number of words in chunk")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    properties: dict = Field(default_factory=dict, description="Chunk properties")
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "chunk_123",
                "document_id": "doc_456",
                "content": "Socrates questions what virtue is...",
                "position": 0.15,
                "word_count": 287,
                "metadata": {"author": "Plato", "dialogue": "Charmides"},
                "properties": {"has_greek": True},
                "embedding": [0.1, 0.2, 0.3]  # Shortened for example
            }
        }
```

**Usage**:
```python
from arete.models import Chunk

# Create chunk
chunk = Chunk(
    id="chunk_001",
    document_id="doc_plato_apology",
    content="Men of Athens, I honor and love you...",
    position=0.02,
    word_count=145,
    metadata={"author": "Plato", "dialogue": "Apology"},
    properties={"speaker": "Socrates"}
)

# Access properties
print(f"Chunk has {chunk.word_count} words")
print(f"From: {chunk.metadata['dialogue']}")

# Validate on creation (Pydantic automatic)
invalid_chunk = Chunk(
    id="chunk_002",
    document_id="doc_001",
    content="",  # ValidationError: content cannot be empty
    position=-1.0,  # ValidationError: position must be 0.0-1.0
    word_count="ten"  # ValidationError: word_count must be int
)
```

### Entity

**Purpose**: Represents a philosophical entity (concept, person, work, etc.).

**File**: `models/entity.py`

**Schema**:
```python
from pydantic import BaseModel, Field
from typing import Dict, Optional

class Entity(BaseModel):
    """Philosophical entity (concept, person, work)."""

    id: str = Field(..., description="Unique entity identifier")
    name: str = Field(..., description="Entity name")
    entity_type: str = Field(..., description="Entity type (CONCEPT, PERSON, WORK, etc.)")
    description: str = Field(default="", description="Entity description")
    canonical_form: str = Field(..., description="Canonical name form")
    properties: Dict[str, str] = Field(default_factory=dict, description="Entity properties")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "entity_socrates",
                "name": "Socrates",
                "entity_type": "PERSON",
                "description": "Greek philosopher, teacher of Plato",
                "canonical_form": "Socrates",
                "properties": {
                    "birth": "c. 470 BCE",
                    "death": "399 BCE",
                    "nationality": "Athenian"
                }
            }
        }
```

**Entity Types**:
- `CONCEPT`: Philosophical concepts (virtue, justice, temperance)
- `PERSON`: Historical figures (Socrates, Plato, Aristotle)
- `WORK`: Philosophical texts (Republic, Apology, Ethics)
- `PLACE`: Locations (Athens, Academy, Agora)
- `EVENT`: Historical events (Trial of Socrates)

**Usage**:
```python
from arete.models import Entity

# Create entity
entity = Entity(
    id="entity_virtue",
    name="Virtue",
    entity_type="CONCEPT",
    description="Excellence or moral goodness in character",
    canonical_form="virtue",
    properties={
        "greek": "arete",
        "related_concepts": "excellence,goodness,morality"
    }
)

# Get canonical form
print(entity.canonical_form)  # "virtue"

# Check type
if entity.entity_type == "CONCEPT":
    print("This is a philosophical concept")
```

### Relationship

**Purpose**: Represents relationships between entities in the knowledge graph.

**File**: `models/relationship.py`

**Schema**:
```python
from pydantic import BaseModel, Field
from typing import Dict, Optional

class Relationship(BaseModel):
    """Relationship between entities."""

    source_id: str = Field(..., description="Source entity ID")
    target_id: str = Field(..., description="Target entity ID")
    relationship_type: str = Field(..., description="Type of relationship")
    properties: Dict[str, str] = Field(default_factory=dict, description="Relationship properties")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score")

    class Config:
        json_schema_extra = {
            "example": {
                "source_id": "entity_socrates",
                "target_id": "entity_virtue",
                "relationship_type": "DISCUSSES",
                "properties": {"dialogue": "Charmides", "context": "temperance"},
                "confidence": 0.95
            }
        }
```

**Relationship Types**:
- `DISCUSSES`: Entity discusses another entity
- `DEFINES`: Entity provides definition of another
- `RELATED_TO`: General relationship
- `CONTRADICTS`: Entities are in opposition
- `SUPPORTS`: Entity supports another
- `EXEMPLIFIES`: Entity is example of another
- `TEACHES`: Person teaches another person
- `WROTE`: Person wrote a work

**Usage**:
```python
from arete.models import Relationship

# Create relationship
relationship = Relationship(
    source_id="entity_socrates",
    target_id="entity_knowledge",
    relationship_type="DISCUSSES",
    properties={
        "dialogue": "Apology",
        "position": "argues true knowledge is wisdom"
    },
    confidence=0.98
)

# Filter by confidence
high_confidence = [r for r in relationships if r.confidence > 0.9]
```

### SearchResult

**Purpose**: Container for search results with relevance scoring.

**File**: `models/search_result.py`

**Schema**:
```python
from pydantic import BaseModel, Field
from typing import Optional

class SearchResult(BaseModel):
    """Search result with relevance scoring."""

    chunk_id: str = Field(..., description="Chunk identifier")
    content: str = Field(..., description="Chunk content")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    position: float = Field(..., description="Position in document")
    document_id: str = Field(..., description="Source document ID")
    metadata: dict = Field(default_factory=dict, description="Result metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "chunk_042",
                "content": "Temperance is self-knowledge...",
                "score": 0.87,
                "position": 0.42,
                "document_id": "doc_charmides",
                "metadata": {"dialogue": "Charmides", "speaker": "Socrates"}
            }
        }
```

**Usage**:
```python
from arete.models import SearchResult

# Create result
result = SearchResult(
    chunk_id="chunk_123",
    content="Socrates argues that virtue is knowledge...",
    score=0.89,
    position=0.34,
    document_id="doc_meno",
    metadata={"dialogue": "Meno", "relevance": "high"}
)

# Sort results by score
sorted_results = sorted(results, key=lambda r: r.score, reverse=True)

# Filter by threshold
relevant = [r for r in results if r.score > 0.7]
```

## Configuration Models

### Settings

**Purpose**: Application configuration with environment variable loading.

**File**: `models/settings.py`

**Schema**:
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Database
    neo4j_uri: str = Field(..., env="NEO4J_URI")
    neo4j_user: str = Field(..., env="NEO4J_USER")
    neo4j_password: str = Field(..., env="NEO4J_PASSWORD")
    weaviate_url: str = Field(..., env="WEAVIATE_URL")

    # LLM Provider
    kg_llm_provider: str = Field(default="openai", env="KG_LLM_PROVIDER")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")

    # Embedding Provider
    embedding_provider: str = Field(default="openai", env="EMBEDDING_PROVIDER")

    # Application
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    environment: str = Field(default="development", env="ENVIRONMENT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

**Usage**:
```python
from arete.models import Settings

# Load settings (reads from .env)
settings = Settings()

# Access settings
print(f"Using {settings.kg_llm_provider} as LLM provider")
print(f"Neo4j URI: {settings.neo4j_uri}")

# Validation happens automatically
# If required env var missing, raises ValidationError
```

## Model Validation

### Built-in Validators

Pydantic provides automatic validation:

```python
from pydantic import BaseModel, Field, validator

class Chunk(BaseModel):
    position: float = Field(..., ge=0.0, le=1.0)  # Must be 0.0-1.0
    word_count: int = Field(..., gt=0)  # Must be positive
    content: str = Field(..., min_length=1)  # Cannot be empty

    @validator("content")
    def content_not_empty(cls, v):
        """Ensure content is not just whitespace."""
        if not v.strip():
            raise ValueError("Content cannot be empty or whitespace")
        return v
```

### Custom Validators

```python
from pydantic import BaseModel, validator

class Entity(BaseModel):
    entity_type: str

    @validator("entity_type")
    def validate_entity_type(cls, v):
        """Validate entity type is one of allowed types."""
        allowed_types = ["CONCEPT", "PERSON", "WORK", "PLACE", "EVENT"]
        if v.upper() not in allowed_types:
            raise ValueError(f"Invalid entity type: {v}")
        return v.upper()
```

## Type Safety

### Using Models with Type Hints

```python
from typing import List
from arete.models import Chunk, Entity

def process_chunks(chunks: List[Chunk]) -> List[str]:
    """Process chunks and return content."""
    return [chunk.content for chunk in chunks]

def find_entities_by_type(entities: List[Entity], entity_type: str) -> List[Entity]:
    """Filter entities by type."""
    return [e for e in entities if e.entity_type == entity_type]
```

### Model Serialization

```python
from arete.models import Chunk

# To dict
chunk_dict = chunk.model_dump()

# To JSON
chunk_json = chunk.model_dump_json()

# From dict
chunk = Chunk(**chunk_dict)

# From JSON
chunk = Chunk.model_validate_json(chunk_json)
```

## Best Practices

### 1. Always Use Models

```python
# Good
chunk = Chunk(id="1", document_id="doc1", content="...", ...)

# Bad
chunk = {
    "id": "1",
    "document_id": "doc1",
    "content": "..."
}
```

### 2. Leverage Validation

```python
# Let Pydantic catch errors early
try:
    chunk = Chunk(
        id="1",
        document_id="doc1",
        content="",  # Will raise ValidationError
        position=0.5,
        word_count=10
    )
except ValidationError as e:
    print(f"Invalid chunk: {e}")
```

### 3. Use Field Defaults

```python
class Chunk(BaseModel):
    metadata: dict = Field(default_factory=dict)  # Good: default to {}
    properties: dict = {}  # Bad: mutable default shared across instances!
```

### 4. Document with Examples

```python
class Chunk(BaseModel):
    """Semantic text chunk."""

    class Config:
        json_schema_extra = {
            "example": {
                "id": "chunk_001",
                "content": "Example content..."
            }
        }
```

## Testing

### Model Unit Tests

```python
import pytest
from pydantic import ValidationError
from arete.models import Chunk

def test_chunk_creation_valid():
    """Test creating valid chunk."""
    chunk = Chunk(
        id="test_chunk",
        document_id="test_doc",
        content="Test content",
        position=0.5,
        word_count=2
    )
    assert chunk.id == "test_chunk"
    assert chunk.word_count == 2

def test_chunk_creation_invalid_position():
    """Test chunk creation with invalid position."""
    with pytest.raises(ValidationError) as exc_info:
        Chunk(
            id="test",
            document_id="test",
            content="test",
            position=1.5,  # Invalid: > 1.0
            word_count=1
        )

    assert "position" in str(exc_info.value)

def test_chunk_defaults():
    """Test chunk default values."""
    chunk = Chunk(
        id="test",
        document_id="test",
        content="test",
        position=0.0,
        word_count=1
    )
    assert chunk.metadata == {}
    assert chunk.properties == {}
    assert chunk.embedding is None
```

---

**Related Documentation**:
- [Database Module](../database/DATABASE.md)
- [Services Module](../services/SERVICES.md)
- [Architecture Overview](../../../.claude/architecture.md)
