# Services Module Documentation

## Overview

The services module contains business logic for the Arete application. Services orchestrate operations across repositories, handle complex workflows, and implement domain-specific algorithms.

## Core Services

### ChunkService

**Purpose**: Manage semantic text chunking and chunk lifecycle.

**File**: `services/chunk_service.py`

**Responsibilities**:
- Create semantic chunks from text
- Calculate chunk positions and boundaries
- Manage chunk metadata
- Handle chunk validation

**Key Methods**:
```python
class ChunkService:
    """Service for chunk operations."""

    def create_chunks(
        self,
        text: str,
        document_id: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[Chunk]:
        """Create semantic chunks from text.

        Args:
            text: Source text to chunk
            document_id: Parent document identifier
            chunk_size: Target chunk size in tokens
            overlap: Overlap between chunks in tokens

        Returns:
            List of Chunk objects with embeddings
        """
        pass

    def calculate_position(self, chunk_index: int, total_chunks: int) -> float:
        """Calculate normalized position (0.0-1.0) for chunk."""
        return chunk_index / max(total_chunks - 1, 1)
```

**Usage**:
```python
from arete.services import ChunkService

service = ChunkService()

# Create chunks
chunks = service.create_chunks(
    text=philosophical_text,
    document_id="doc_republic",
    chunk_size=500,
    overlap=50
)

# Access chunks
for chunk in chunks:
    print(f"Chunk {chunk.id} at position {chunk.position}")
    print(f"Content: {chunk.content[:100]}...")
```

### EmbeddingService

**Purpose**: Generate vector embeddings using multiple providers.

**File**: `services/embedding_service.py`

**Responsibilities**:
- Generate embeddings from text
- Support multiple providers (OpenAI, Gemini, etc.)
- Batch processing for efficiency
- Retry logic with exponential backoff

**Provider Support**:
- `OpenAIEmbeddingService`: text-embedding-3-small (1536d)
- `GeminiEmbeddingService`: text-embedding-004 (768d)
- `OpenRouterEmbeddingService`: Multiple models via single API
- `AnthropicEmbeddingService`: Feature-based fallback
- `OllamaEmbeddingService`: Local embedding models

**Key Methods**:
```python
class EmbeddingService:
    """Base embedding service interface."""

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        pass

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        pass
```

**Usage**:
```python
from arete.services.embedding_service import get_embedding_service

# Get service based on EMBEDDING_PROVIDER env var
service = get_embedding_service()

# Single embedding
embedding = service.embed_text("What is virtue?")
print(f"Embedding dimension: {len(embedding)}")

# Batch processing
texts = [chunk.content for chunk in chunks]
embeddings = service.embed_batch(texts)

# Check dimensions
assert len(embeddings[0]) == service.dimension
```

**Provider-Specific Configuration**:
```python
# .env configuration
EMBEDDING_PROVIDER=openai  # or gemini, openrouter, anthropic, ollama

# OpenAI
OPENAI_API_KEY=your_key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Gemini
GOOGLE_API_KEY=your_key
GEMINI_EMBEDDING_MODEL=text-embedding-004
```

### RAGService

**Purpose**: Orchestrate the RAG pipeline for question answering.

**File**: `services/rag_service.py`

**Responsibilities**:
- Query processing and expansion
- Hybrid retrieval (sparse + dense + graph)
- Context assembly and ranking
- LLM response generation
- Citation extraction and formatting

**Key Methods**:
```python
class RAGService:
    """Retrieval-Augmented Generation service."""

    def __init__(
        self,
        chunk_repository,
        entity_repository,
        llm_service,
        embedding_service
    ):
        self.chunk_repo = chunk_repository
        self.entity_repo = entity_repository
        self.llm = llm_service
        self.embeddings = embedding_service

    async def answer_question(
        self,
        question: str,
        max_chunks: int = 10,
        min_relevance: float = 0.7
    ) -> dict:
        """Answer question using RAG pipeline.

        Args:
            question: User question
            max_chunks: Maximum chunks to retrieve
            min_relevance: Minimum relevance threshold

        Returns:
            dict with answer, citations, and metadata
        """
        # 1. Generate query embedding
        query_embedding = self.embeddings.embed_text(question)

        # 2. Retrieve relevant chunks
        chunks = await self.retrieve_chunks(
            query_embedding,
            limit=max_chunks,
            min_score=min_relevance
        )

        # 3. Find related entities
        entities = await self.find_related_entities(question)

        # 4. Assemble context
        context = self.assemble_context(chunks, entities)

        # 5. Generate response
        response = await self.llm.generate(
            prompt=self.build_prompt(question, context)
        )

        # 6. Extract citations
        citations = self.extract_citations(response, chunks)

        return {
            "answer": response,
            "citations": citations,
            "chunks_used": len(chunks),
            "entities_found": len(entities)
        }
```

**Usage**:
```python
from arete.services import RAGService

service = RAGService(
    chunk_repository=chunk_repo,
    entity_repository=entity_repo,
    llm_service=llm_service,
    embedding_service=embedding_service
)

# Answer question
result = await service.answer_question(
    question="What is Socrates' definition of virtue?",
    max_chunks=10,
    min_relevance=0.75
)

print(f"Answer: {result['answer']}")
print(f"Citations: {len(result['citations'])}")
for citation in result['citations']:
    print(f"- {citation['source']}: {citation['content'][:100]}...")
```

### EntityService

**Purpose**: Manage philosophical entities and their relationships.

**File**: `services/entity_service.py`

**Responsibilities**:
- Entity creation and validation
- Relationship management
- Entity deduplication
- Canonical form resolution

**Key Methods**:
```python
class EntityService:
    """Service for entity operations."""

    def create_entity(
        self,
        name: str,
        entity_type: str,
        description: str = "",
        properties: dict = None
    ) -> Entity:
        """Create and validate entity."""
        pass

    def find_or_create(self, name: str, entity_type: str) -> Entity:
        """Find existing entity or create new one."""
        pass

    def merge_duplicate_entities(self, entity_ids: List[str]) -> Entity:
        """Merge duplicate entities into canonical form."""
        pass

    def get_related_entities(
        self,
        entity_id: str,
        relationship_type: Optional[str] = None,
        max_depth: int = 1
    ) -> List[Entity]:
        """Get entities related to given entity."""
        pass
```

**Usage**:
```python
from arete.services import EntityService

service = EntityService(entity_repository=entity_repo)

# Create entity
socrates = service.create_entity(
    name="Socrates",
    entity_type="PERSON",
    description="Greek philosopher",
    properties={"birth": "c. 470 BCE", "death": "399 BCE"}
)

# Find or create (avoids duplicates)
virtue = service.find_or_create(name="virtue", entity_type="CONCEPT")

# Get related entities
related = service.get_related_entities(
    entity_id=socrates.id,
    relationship_type="DISCUSSES",
    max_depth=2
)
```

### GraphAnalyticsService

**Purpose**: Perform graph analysis on knowledge graph.

**File**: `services/graph_analytics_service.py`

**Responsibilities**:
- Centrality analysis (degree, betweenness, PageRank)
- Community detection
- Influence network analysis
- Concept clustering

**Key Methods**:
```python
class GraphAnalyticsService:
    """Graph analytics and network analysis."""

    def calculate_centrality(
        self,
        algorithm: str = "pagerank"
    ) -> Dict[str, float]:
        """Calculate node centrality scores.

        Args:
            algorithm: One of 'degree', 'betweenness', 'closeness',
                      'eigenvector', 'pagerank'

        Returns:
            Dict mapping entity IDs to centrality scores
        """
        pass

    def detect_communities(self) -> Dict[str, int]:
        """Detect communities using label propagation.

        Returns:
            Dict mapping entity IDs to community IDs
        """
        pass

    def find_influential_nodes(self, top_n: int = 10) -> List[Entity]:
        """Find most influential entities in graph."""
        pass
```

**Usage**:
```python
from arete.services import GraphAnalyticsService

service = GraphAnalyticsService(neo4j_client=neo4j_client)

# Calculate PageRank
scores = service.calculate_centrality(algorithm="pagerank")
top_concepts = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]

print("Most central concepts:")
for entity_id, score in top_concepts:
    print(f"- {entity_id}: {score:.4f}")

# Detect communities
communities = service.detect_communities()
print(f"Found {len(set(communities.values()))} communities")

# Find influential nodes
influential = service.find_influential_nodes(top_n=5)
for entity in influential:
    print(f"- {entity.name} ({entity.entity_type})")
```

## Service Patterns

### Dependency Injection

Services should receive dependencies through constructor injection:

```python
class RAGService:
    """RAG service with injected dependencies."""

    def __init__(
        self,
        chunk_repository: ChunkRepository,
        entity_repository: EntityRepository,
        llm_service: LLMService,
        embedding_service: EmbeddingService
    ):
        self.chunk_repo = chunk_repository
        self.entity_repo = entity_repository
        self.llm = llm_service
        self.embeddings = embedding_service
```

**Benefits**:
- Easy to test with mock dependencies
- Clear service dependencies
- Flexible configuration

### Error Handling

Services should handle errors gracefully and provide meaningful messages:

```python
class ChunkService:
    def create_chunks(self, text: str, document_id: str) -> List[Chunk]:
        """Create chunks with error handling."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        if not document_id:
            raise ValueError("Document ID is required")

        try:
            chunks = self._process_text(text)
            return chunks
        except Exception as e:
            logger.error(f"Failed to create chunks: {e}", exc_info=True)
            raise ChunkCreationError(f"Chunk creation failed: {e}") from e
```

### Async Operations

Use async/await for I/O-bound operations:

```python
class RAGService:
    async def answer_question(self, question: str) -> dict:
        """Answer question asynchronously."""
        # Parallel API calls
        embedding_task = asyncio.create_task(
            self.embeddings.embed_text(question)
        )
        entities_task = asyncio.create_task(
            self.entity_repo.search(question)
        )

        # Wait for both
        embedding, entities = await asyncio.gather(
            embedding_task,
            entities_task
        )

        # Continue with results
        chunks = await self.chunk_repo.search_by_similarity(embedding)
        return self.generate_response(question, chunks, entities)
```

## Testing Services

### Unit Tests with Mocks

```python
import pytest
from unittest.mock import Mock, AsyncMock
from arete.services import RAGService

@pytest.fixture
def mock_repositories():
    """Provide mock repositories."""
    return {
        "chunk_repo": Mock(),
        "entity_repo": Mock(),
        "llm_service": Mock(),
        "embedding_service": Mock()
    }

@pytest.mark.asyncio
async def test_rag_service_answer_question(mock_repositories):
    """Test RAG service question answering."""
    # Arrange
    service = RAGService(**mock_repositories)

    mock_repositories["embedding_service"].embed_text.return_value = [0.1] * 1536
    mock_repositories["chunk_repo"].search_by_similarity = AsyncMock(
        return_value=[Mock(content="Virtue is knowledge")]
    )

    # Act
    result = await service.answer_question("What is virtue?")

    # Assert
    assert "answer" in result
    assert result["chunks_used"] > 0
    mock_repositories["embedding_service"].embed_text.assert_called_once()
```

### Integration Tests

```python
import pytest
from arete.services import ChunkService
from arete.repositories import ChunkRepository
from arete.database import WeaviateClient

@pytest.fixture
def chunk_service():
    """Provide real chunk service with test database."""
    client = WeaviateClient()
    repository = ChunkRepository(client)
    return ChunkService(repository)

def test_chunk_service_end_to_end(chunk_service):
    """Test chunk service with real database."""
    # Create chunks
    chunks = chunk_service.create_chunks(
        text="Sample philosophical text for testing.",
        document_id="test_doc"
    )

    assert len(chunks) > 0
    assert all(chunk.document_id == "test_doc" for chunk in chunks)
    assert all(0.0 <= chunk.position <= 1.0 for chunk in chunks)
```

## Best Practices

### 1. Single Responsibility

Each service should have one clear purpose:

```python
# Good: Focused service
class ChunkService:
    """Handles chunk creation and management."""
    pass

# Bad: Too many responsibilities
class DataService:
    """Handles chunks, entities, embeddings, and queries."""
    pass
```

### 2. Separation of Concerns

Services orchestrate, repositories handle data access:

```python
# Service layer
class EntityService:
    def create_entity(self, name: str) -> Entity:
        entity = Entity(name=name, ...)
        return self.entity_repo.save(entity)  # Delegate to repository

# Repository layer
class EntityRepository:
    def save(self, entity: Entity) -> str:
        # Handle database interaction
        pass
```

### 3. Explicit Dependencies

Make dependencies explicit in constructor:

```python
# Good: Clear dependencies
class RAGService:
    def __init__(self, chunk_repo, entity_repo, llm, embeddings):
        self.chunk_repo = chunk_repo
        # ...

# Bad: Hidden dependencies
class RAGService:
    def __init__(self):
        self.chunk_repo = ChunkRepository()  # Hard to test!
```

### 4. Return Domain Objects

Services should return domain models, not raw data:

```python
# Good: Returns domain model
def find_entity(self, name: str) -> Optional[Entity]:
    return self.entity_repo.find_by_name(name)

# Bad: Returns raw dict
def find_entity(self, name: str) -> Optional[dict]:
    return {"name": name, "type": "CONCEPT"}
```

---

**Related Documentation**:
- [Models Documentation](../models/MODELS.md)
- [Database Documentation](../database/DATABASE.md)
- [RAG Pipeline Documentation](../rag/RAG.md)
- [Architecture Overview](../../../.claude/architecture.md)
