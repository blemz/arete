# Architecture Patterns Memory

This file contains established coding patterns, design patterns, and implementation conventions for the Arete Graph-RAG system.

## [MemoryID: 20250810-MM03] Test-Driven Development Pattern
**Type**: code_pattern  
**Priority**: 1  
**Tags**: tdd, testing, development-workflow, quality

### Pattern Description
All new code follows strict TDD Red-Green-Refactor cycle:
1. **Red**: Write failing test first
2. **Green**: Implement minimal code to pass test
3. **Refactor**: Improve code quality while maintaining tests

### Implementation Example
```python
# 1. RED: Write failing test first
def test_document_creation_with_valid_data():
    document = Document(title="Republic", author="Plato", content="Justice is...")
    assert document.title == "Republic"
    assert document.word_count > 0

# 2. GREEN: Minimal implementation
class Document(BaseModel):
    title: str
    author: str  
    content: str
    
    @property
    def word_count(self) -> int:
        return len(self.content.split())

# 3. REFACTOR: Add validation and features
class Document(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    author: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10)
    
    @property
    def word_count(self) -> int:
        """Calculate word count from content."""
        return len(self.content.split())
```

### Quality Standards
- **Minimum**: 90% test coverage for all new code
- **Target**: 95% coverage for critical business logic
- **Categories**: Unit tests, integration tests, end-to-end validation
- **Mock Strategy**: External dependencies mocked appropriately

### Application Areas
- Model implementation (Document, Entity, Chunk, Citation)
- Service layer business logic
- Database repository implementations
- API endpoint development

---

## [MemoryID: 20250810-MM04] Pydantic BaseModel Pattern
**Type**: code_pattern  
**Priority**: 1  
**Tags**: pydantic, validation, serialization, database-integration

### Pattern Description
Standardized data model pattern using Pydantic BaseModel with:
- **Type Safety**: Strict typing and runtime validation
- **Dual Serialization**: Support for both Neo4j and Weaviate formats
- **Configuration**: Consistent model configuration across all types
- **Validation**: Custom validators for domain-specific rules

### Base Pattern Implementation
```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

class AreteBaseModel(BaseModel):
    """Base class for all Arete data models."""
    
    # Standard fields
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(None)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Configuration
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        extra="ignore"
    )
    
    # Database serialization methods
    def to_neo4j_dict(self) -> Dict[str, Any]:
        """Convert to Neo4j-compatible dictionary."""
        data = self.model_dump(exclude_none=True)
        data['id'] = str(data['id'])  # Convert UUID to string
        data['created_at'] = self.created_at.timestamp()
        return data
    
    def to_weaviate_dict(self) -> Dict[str, Any]:
        """Convert to Weaviate-compatible dictionary."""
        data = self.model_dump(exclude={'id', 'embedding'})
        data['neo4j_id'] = str(self.id)  # Cross-reference
        return data
    
    @classmethod
    def from_neo4j_node(cls, node_data: Dict[str, Any]):
        """Create instance from Neo4j node data."""
        if 'created_at' in node_data:
            node_data['created_at'] = datetime.fromtimestamp(node_data['created_at'])
        return cls(**node_data)
```

### Validation Pattern
```python
@field_validator("field_name")
@classmethod
def validate_field_name(cls, v: str) -> str:
    """Validate and normalize field."""
    if not v.strip():
        raise ValueError("Field cannot be empty")
    return v.strip()

# Multi-field validation
@model_validator(mode='after')
def validate_model_consistency(self):
    """Validate relationships between fields."""
    if self.start_date and self.end_date:
        if self.start_date > self.end_date:
            raise ValueError("Start date must be before end date")
    return self
```

### Security Considerations
```python
# Hide sensitive data in representations
neo4j_password: str = Field(..., repr=False)
api_key: Optional[str] = Field(None, repr=False)
```

### Application Areas
- Document model with content validation
- Entity model with NER confidence scoring
- Chunk model with position validation
- Citation model with format validation

---

## [MemoryID: 20250810-MM11] Database Client Connection Pattern
**Type**: code_pattern
**Priority**: 2
**Tags**: database, connection-management, context-manager, error-handling

### Pattern Description
Standardized database client pattern using context managers for:
- **Connection Management**: Automatic connection lifecycle management
- **Error Handling**: Comprehensive exception handling and retry logic
- **Health Monitoring**: Connection health checks and status reporting
- **Resource Cleanup**: Guaranteed cleanup of database resources

### Neo4j Client Pattern
```python
from neo4j import GraphDatabase, Session
from contextlib import contextmanager
from typing import Dict, Any

class Neo4jClient:
    """Neo4j database client with connection management."""
    
    def __init__(self, uri: str, auth: tuple):
        self.uri = uri
        self.auth = auth
        self._driver = None
    
    def connect(self):
        """Establish database connection with error handling."""
        try:
            self._driver = GraphDatabase.driver(self.uri, auth=self.auth)
            # Verify connectivity
            with self._driver.session() as session:
                session.run("RETURN 1")
        except Exception as e:
            raise GraphConnectionError(f"Failed to connect to Neo4j: {e}")
    
    @contextmanager
    def session(self, **kwargs) -> Session:
        """Provide database session context manager."""
        if not self._driver:
            self.connect()
        
        session = self._driver.session(**kwargs)
        try:
            yield session
        finally:
            session.close()
    
    def health_check(self) -> Dict[str, Any]:
        """Check database health and connectivity."""
        try:
            with self.session() as session:
                result = session.run("CALL dbms.components() YIELD name, versions")
                return {
                    "status": "healthy",
                    "components": [dict(record) for record in result]
                }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
```

### Usage Pattern
```python
# Automatic resource management
client = Neo4jClient(uri, auth)

with client.session() as session:
    result = session.run("MATCH (n) RETURN count(n)")
    count = result.single()[0]
    
# Session automatically closed, resources cleaned up
```

### Application Areas
- Neo4j graph database operations
- Weaviate vector database connections
- Redis cache client management
- Connection pooling implementations

---

## [MemoryID: 20250810-MM12] Query Builder Pattern
**Type**: code_pattern
**Priority**: 2
**Tags**: query-builder, fluent-api, cypher, type-safety

### Pattern Description
Fluent query builder pattern for constructing complex database queries:
- **Type Safety**: Compile-time query validation
- **Readability**: Natural language-like query construction
- **Reusability**: Composable query components
- **Parameter Safety**: Automatic parameter binding and sanitization

### Cypher Query Builder
```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class GraphQueryBuilder:
    """Builder for complex Cypher queries."""
    
    def __init__(self):
        self._match_clauses: List[str] = []
        self._where_clauses: List[str] = []
        self._return_clauses: List[str] = []
        self._order_clauses: List[str] = []
        self._limit: Optional[int] = None
        self._parameters: Dict[str, Any] = {}
    
    def match(self, pattern: str):
        """Add MATCH clause."""
        self._match_clauses.append(f"MATCH {pattern}")
        return self
    
    def where(self, condition: str, **params):
        """Add WHERE clause with parameters."""
        self._where_clauses.append(condition)
        self._parameters.update(params)
        return self
    
    def return_nodes(self, *nodes):
        """Add RETURN clause for nodes."""
        self._return_clauses.extend(nodes)
        return self
    
    def order_by(self, field: str, desc: bool = False):
        """Add ORDER BY clause."""
        direction = "DESC" if desc else "ASC"
        self._order_clauses.append(f"{field} {direction}")
        return self
    
    def limit(self, count: int):
        """Add LIMIT clause."""
        self._limit = count
        return self
    
    def build(self) -> tuple[str, Dict[str, Any]]:
        """Build final query and parameters."""
        query_parts = []
        
        if self._match_clauses:
            query_parts.extend(self._match_clauses)
        if self._where_clauses:
            query_parts.append("WHERE " + " AND ".join(self._where_clauses))
        if self._return_clauses:
            query_parts.append("RETURN " + ", ".join(self._return_clauses))
        if self._order_clauses:
            query_parts.append("ORDER BY " + ", ".join(self._order_clauses))
        if self._limit:
            query_parts.append(f"LIMIT {self._limit}")
        
        return "\n".join(query_parts), self._parameters
```

### Usage Example
```python
# Natural language-like query construction
query, params = (GraphQueryBuilder()
    .match("(philosopher:Entity {type: 'Person'})-[:INFLUENCES]->(student:Entity)")
    .where("philosopher.name = $name", name="Socrates")
    .return_nodes("student.name as influenced", "philosopher.name as teacher")
    .order_by("student.name")
    .limit(10)
    .build())

# Execute with automatic parameter binding
with client.session() as session:
    result = session.run(query, params)
```

### Application Areas
- Complex graph traversal queries
- Dynamic search query construction
- RAG retrieval query building
- Analytics and reporting queries

---

## [MemoryID: 20250810-MM13] Error Handling Pattern
**Type**: code_pattern
**Priority**: 2
**Tags**: error-handling, exceptions, logging, resilience

### Pattern Description
Comprehensive error handling strategy with:
- **Custom Exceptions**: Domain-specific error types
- **Structured Logging**: Contextual error information
- **Retry Logic**: Automatic retry for transient failures
- **Graceful Degradation**: System continues operation when possible

### Custom Exception Hierarchy
```python
class AreteError(Exception):
    """Base exception for Arete system."""
    pass

class DatabaseError(AreteError):
    """Database operation errors."""
    pass

class GraphConnectionError(DatabaseError):
    """Neo4j connection failures."""
    pass

class ValidationError(AreteError):
    """Data validation failures."""
    pass

class LLMProviderError(AreteError):
    """LLM provider integration errors."""
    pass
```

### Error Handling with Logging
```python
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

def handle_database_errors(func: Callable) -> Callable:
    """Decorator for database error handling."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except GraphConnectionError as e:
            logger.error(f"Graph connection failed in {func.__name__}: {e}")
            raise DatabaseError(f"Database operation failed: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}")
            raise AreteError(f"System error: {e}")
    return wrapper

# Usage
@handle_database_errors
def create_document(self, document: Document) -> Document:
    """Create document with error handling."""
    # Implementation here
```

### Retry Pattern
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
def connect_with_retry(self):
    """Connect to database with automatic retry."""
    try:
        self._driver = GraphDatabase.driver(self.uri, auth=self.auth)
    except Exception as e:
        logger.warning(f"Connection attempt failed, retrying: {e}")
        raise
```

### Application Areas
- Database connection management
- LLM provider communication
- File processing operations
- API request handling

---

## Pattern Dependencies

### Core Foundation Patterns
1. **TDD Pattern** (MM03) → All development work
2. **Pydantic Pattern** (MM04) → All data models
3. **Database Client Pattern** (MM11) → All database operations

### Advanced Patterns
1. **Query Builder** (MM12) depends on **Database Client** (MM11)
2. **Error Handling** (MM13) applies to all patterns
3. **Repository Pattern** (from architecture/decisions.md) uses all client patterns

### Implementation Priority
1. Base patterns: TDD, Pydantic, Database Client
2. Query building and error handling
3. Advanced patterns: Repository, Service Layer

**Last Updated**: 2025-08-10  
**Review Schedule**: Monthly for pattern consistency, as-needed for new patterns