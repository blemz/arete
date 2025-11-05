# Database Module Documentation

## Overview

The database module provides client interfaces for Neo4j (knowledge graph), Weaviate (vector database), and Redis (caching). All database interactions follow the repository pattern for clean separation of concerns.

## Database Clients

### Neo4jClient

**Purpose**: Manage connections and sessions for Neo4j graph database.

**Key Features**:
- Connection pooling with configurable pool size
- Session management with context managers
- Query execution with parameter binding
- Transaction support
- Health checks and connectivity verification

**Usage**:
```python
from arete.database.neo4j_client import Neo4jClient

# Initialize client (reads from .env)
client = Neo4jClient()

# Verify connection
if client.verify_connectivity():
    print("Connected to Neo4j")

# Execute query
with client.session() as session:
    result = session.run(
        "MATCH (e:Entity {name: $name}) RETURN e",
        name="Socrates"
    )
    entities = [record["e"] for record in result]

# Close client when done
client.close()
```

**Configuration**:
```python
# .env variables
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
NEO4J_MAX_CONNECTION_POOL_SIZE=50
```

**Common Patterns**:
```python
# Transaction with rollback
with client.session() as session:
    tx = session.begin_transaction()
    try:
        tx.run("CREATE (e:Entity {name: $name})", name="Plato")
        tx.commit()
    except Exception as e:
        tx.rollback()
        raise

# Batch operations
with client.session() as session:
    with session.begin_transaction() as tx:
        for entity in entities:
            tx.run("CREATE (e:Entity {name: $name})", name=entity.name)
```

### WeaviateClient

**Purpose**: Manage connections to Weaviate vector database for semantic search.

**Key Features**:
- Vector similarity search
- Metadata filtering
- Batch operations for embeddings
- Schema management
- Health checks

**Usage**:
```python
from arete.database.weaviate_client import WeaviateClient

# Initialize client
client = WeaviateClient()

# Check if ready
if client.is_ready():
    print("Weaviate is ready")

# Vector search
results = client.search_by_vector(
    class_name="Chunk",
    vector=embedding,
    limit=10,
    min_certainty=0.7
)

# Add object with vector
client.add_object(
    class_name="Chunk",
    data_object={
        "content": text,
        "documentId": doc_id,
        "position": 0.0
    },
    vector=embedding
)
```

**Configuration**:
```python
# .env variables
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=  # Optional for cloud
```

**Schema Definition**:
```python
# Define schema for Chunk class
schema = {
    "class": "Chunk",
    "vectorizer": "none",  # We provide vectors
    "properties": [
        {"name": "content", "dataType": ["text"]},
        {"name": "documentId", "dataType": ["string"]},
        {"name": "position", "dataType": ["number"]},
        {"name": "wordCount", "dataType": ["int"]}
    ]
}

client.create_class(schema)
```

### RedisClient (Optional)

**Purpose**: Caching layer for query results and session data.

**Key Features**:
- Key-value storage
- TTL-based expiration
- Connection pooling
- Pub/sub messaging

**Usage**:
```python
from arete.database.redis_client import RedisClient

# Initialize client
client = RedisClient()

# Set with expiration
client.set("query:result", json.dumps(result), ex=3600)

# Get cached value
cached = client.get("query:result")
if cached:
    result = json.loads(cached)

# Delete key
client.delete("query:result")
```

**Configuration**:
```python
# .env variables
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=  # Optional
REDIS_DB=0
```

## Repository Pattern

All database access goes through repository classes that encapsulate queries and provide clean interfaces.

### ChunkRepository

**File**: `repositories/chunk_repository.py`

**Methods**:
- `save(chunk: Chunk) -> str`: Save chunk to Weaviate
- `find_by_id(chunk_id: str) -> Optional[Chunk]`: Find chunk by ID
- `search_by_similarity(embedding, limit) -> List[SearchResult]`: Semantic search
- `delete(chunk_id: str) -> bool`: Delete chunk

**Example**:
```python
from arete.repositories.chunk_repository import ChunkRepository

repo = ChunkRepository(weaviate_client)

# Save chunk
chunk_id = repo.save(chunk)

# Search
results = repo.search_by_similarity(
    embedding=query_embedding,
    limit=10
)
```

### EntityRepository

**File**: `repositories/entity_repository.py`

**Methods**:
- `save(entity: Entity) -> str`: Save entity to Neo4j
- `find_by_name(name: str) -> Optional[Entity]`: Find by name
- `find_by_type(entity_type: str) -> List[Entity]`: Find by type
- `get_related_entities(entity_id: str) -> List[Entity]`: Get related entities

**Example**:
```python
from arete.repositories.entity_repository import EntityRepository

repo = EntityRepository(neo4j_client)

# Save entity
entity_id = repo.save(entity)

# Find related
related = repo.get_related_entities(entity_id)
```

## Connection Management

### Best Practices

**1. Use Context Managers**:
```python
# Good
with neo4j_client.session() as session:
    result = session.run(query)

# Bad
session = neo4j_client.session()
result = session.run(query)
# Session never closed!
```

**2. Connection Pooling**:
```python
# Configure pool sizes in .env
NEO4J_MAX_CONNECTION_POOL_SIZE=50
WEAVIATE_CONNECTION_POOL_SIZE=20
```

**3. Error Handling**:
```python
try:
    with client.session() as session:
        result = session.run(query)
except ServiceUnavailable as e:
    logger.error(f"Database unavailable: {e}")
    # Implement retry logic or fallback
except Exception as e:
    logger.error(f"Query failed: {e}")
    raise
```

**4. Resource Cleanup**:
```python
# Always close clients in production
try:
    client = Neo4jClient()
    # Use client
finally:
    client.close()

# Or use as context manager (if implemented)
with Neo4jClient() as client:
    # Use client
    pass
```

## Performance Optimization

### Neo4j Indexes

```cypher
-- Create indexes for frequently queried fields
CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name);
CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.entity_type);
CREATE INDEX chunk_document IF NOT EXISTS FOR (c:Chunk) ON (c.document_id);
CREATE INDEX relationship_type IF NOT EXISTS FOR ()-[r:RELATED_TO]-() ON (r.type);
```

### Batch Operations

```python
# Good: Batch inserts
with neo4j_client.session() as session:
    with session.begin_transaction() as tx:
        for entity in entities:
            tx.run("CREATE (e:Entity {name: $name})", name=entity.name)

# Bad: Individual inserts
for entity in entities:
    with neo4j_client.session() as session:
        session.run("CREATE (e:Entity {name: $name})", name=entity.name)
```

### Query Caching

```python
from arete.database.redis_client import RedisClient

def cached_query(key: str, query_fn, ttl: int = 3600):
    """Execute query with Redis caching."""
    redis = RedisClient()

    # Check cache
    cached = redis.get(key)
    if cached:
        return json.loads(cached)

    # Execute query
    result = query_fn()

    # Cache result
    redis.set(key, json.dumps(result), ex=ttl)

    return result
```

## Testing

### Unit Tests

```python
import pytest
from unittest.mock import Mock, patch
from arete.database.neo4j_client import Neo4jClient

def test_neo4j_client_verify_connectivity():
    """Test Neo4j connectivity verification."""
    with patch("neo4j.GraphDatabase.driver") as mock_driver:
        mock_driver.return_value.verify_connectivity.return_value = True

        client = Neo4jClient()
        assert client.verify_connectivity() is True
```

### Integration Tests

```python
import pytest
from arete.database.neo4j_client import Neo4jClient

@pytest.fixture
def test_neo4j_client():
    """Provide test Neo4j client."""
    client = Neo4jClient()
    yield client
    # Cleanup
    with client.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    client.close()

def test_entity_crud_operations(test_neo4j_client):
    """Test entity CRUD with real database."""
    with test_neo4j_client.session() as session:
        # Create
        result = session.run(
            "CREATE (e:Entity {name: $name}) RETURN e",
            name="TestEntity"
        )
        entity = result.single()["e"]
        assert entity["name"] == "TestEntity"

        # Read
        result = session.run(
            "MATCH (e:Entity {name: $name}) RETURN e",
            name="TestEntity"
        )
        assert result.single() is not None

        # Delete
        session.run("MATCH (e:Entity {name: $name}) DELETE e", name="TestEntity")
```

## Troubleshooting

### Common Issues

**Neo4j Connection Refused**:
```bash
# Check Neo4j is running
docker ps | grep neo4j

# Check logs
docker logs neo4j

# Verify credentials
# Update .env with correct password
```

**Weaviate Not Ready**:
```bash
# Check status
curl http://localhost:8080/v1/.well-known/ready

# Restart Weaviate
docker restart weaviate
```

**Redis Connection Error**:
```bash
# Redis is optional - application works without it
# To use Redis:
docker run -d --name redis -p 6379:6379 redis:latest
```

For more troubleshooting, see [Troubleshooting Guide](../../../.claude/troubleshooting.md).

---

**Related Documentation**:
- [Architecture Overview](../../../.claude/architecture.md)
- [Models Documentation](../models/MODELS.md)
- [Repositories Documentation](../repositories/REPOSITORIES.md)
