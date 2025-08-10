# Bug Patterns and Solutions Memory

This file contains bug patterns, recurring issues, debugging insights, and prevention strategies for the Arete Graph-RAG system.

## [MemoryID: 20250810-MM20] Database Connection Management Issues
**Type**: bug_pattern  
**Priority**: 2  
**Tags**: database, connections, resource-management, neo4j, weaviate

### Bug Pattern Description
Database connection leaks and timeout issues occur when connections are not properly managed in async/concurrent environments.

### Common Symptoms
- Gradual memory increase over time
- "Connection pool exhausted" errors under load
- Intermittent database timeout exceptions
- System slowdown after extended operation

### Root Causes
```python
# PROBLEMATIC PATTERN - Connection not properly closed
class BadGraphOperations:
    def get_document(self, doc_id: UUID) -> Document:
        driver = GraphDatabase.driver(uri, auth=auth)
        session = driver.session()  # Never closed!
        result = session.run("MATCH (d:Document {id: $id}) RETURN d", id=str(doc_id))
        return result.single()  # Connection leak

# PROBLEMATIC PATTERN - Multiple drivers created
def get_documents() -> List[Document]:
    documents = []
    for doc_id in doc_ids:
        driver = GraphDatabase.driver(uri, auth=auth)  # New driver each time!
        # Process document
        driver.close()  # Expensive connection churn
    return documents
```

### Solution Patterns
```python
# CORRECT PATTERN - Context manager usage
class GraphOperations:
    def __init__(self, client: Neo4jClient):
        self.client = client
    
    def get_document(self, doc_id: UUID) -> Optional[Document]:
        with self.client.session() as session:  # Automatic cleanup
            result = session.run(
                "MATCH (d:Document {id: $id}) RETURN d", 
                id=str(doc_id)
            )
            record = result.single()
            if record:
                return Document.from_neo4j_node(record["d"])
            return None

# CORRECT PATTERN - Shared driver with connection pooling
@lru_cache(maxsize=1)
def get_shared_driver():
    """Single shared driver with connection pooling."""
    return GraphDatabase.driver(
        settings.neo4j_uri,
        auth=settings.neo4j_auth,
        max_connection_lifetime=30 * 60,
        max_connection_pool_size=50
    )
```

### Prevention Strategies
- **Always use context managers** for database sessions
- **Shared driver instances** with connection pooling
- **Proper exception handling** ensures cleanup even on errors
- **Connection health monitoring** detects issues early
- **Resource cleanup in finally blocks** for critical sections

### Detection Methods
```python
# Connection monitoring utility
class ConnectionMonitor:
    def check_connection_health(self) -> Dict[str, Any]:
        """Monitor database connection health."""
        with self.client.session() as session:
            result = session.run("CALL dbms.listConnections()")
            connections = [dict(record) for record in result]
            
            return {
                "active_connections": len(connections),
                "max_connections": self.client._driver.max_connection_pool_size,
                "connection_utilization": len(connections) / self.client._driver.max_connection_pool_size,
                "warning": len(connections) > (self.client._driver.max_connection_pool_size * 0.8)
            }
```

---

## [MemoryID: 20250810-MM21] Pydantic Validation Edge Cases
**Type**: bug_pattern  
**Priority**: 2  
**Tags**: validation, pydantic, data-models, edge-cases

### Bug Pattern Description
Pydantic validation failures occur with edge cases involving empty strings, None values, and type coercion, especially with philosophical text processing.

### Common Symptoms
- ValidationError exceptions with unclear error messages
- Silent data corruption with type coercion
- Inconsistent behavior between different data sources
- Unicode/encoding issues with classical texts

### Problematic Patterns
```python
# PROBLEMATIC - Doesn't handle empty strings properly
class Document(BaseModel):
    title: str
    author: str
    content: str
    
# Input: {"title": "  ", "author": "", "content": "Valid content"}
# Result: Validation passes but creates invalid document

# PROBLEMATIC - No proper None handling
class Entity(BaseModel):
    name: str
    description: Optional[str] = None
    confidence: float
    
# Input: {"name": "Socrates", "description": "", "confidence": "high"}
# Result: Unexpected type coercion and validation issues
```

### Solution Patterns
```python
# CORRECT PATTERN - Comprehensive validation
class Document(AreteBaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    author: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10)
    language: str = Field(default="English")
    
    @field_validator("title", "author")
    @classmethod
    def validate_non_empty_string(cls, v: str) -> str:
        """Ensure strings are not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace-only")
        return v.strip()
    
    @field_validator("content")
    @classmethod
    def validate_content_length(cls, v: str) -> str:
        """Validate content has minimum meaningful length."""
        cleaned = v.strip()
        if len(cleaned) < 10:
            raise ValueError("Content must be at least 10 characters")
        return cleaned

# CORRECT PATTERN - Proper None and type handling
class Entity(AreteBaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    confidence: float = Field(..., ge=0.0, le=1.0)
    
    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Handle empty strings as None for optional fields."""
        if v is not None and not v.strip():
            return None
        return v.strip() if v else None
    
    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v) -> float:
        """Ensure confidence is a valid float between 0 and 1."""
        try:
            confidence = float(v)
            if not 0.0 <= confidence <= 1.0:
                raise ValueError("Confidence must be between 0.0 and 1.0")
            return confidence
        except (ValueError, TypeError):
            raise ValueError("Confidence must be a number between 0.0 and 1.0")
```

### Unicode and Encoding Issues
```python
# Handle classical text encoding issues
@field_validator("content")
@classmethod
def validate_unicode_content(cls, v: str) -> str:
    """Handle unicode issues in classical texts."""
    try:
        # Normalize unicode to handle different representations
        import unicodedata
        normalized = unicodedata.normalize('NFC', v)
        
        # Remove problematic characters but preserve meaning
        cleaned = normalized.replace('\x00', '').strip()
        
        if len(cleaned) < 10:
            raise ValueError("Content too short after cleaning")
        
        return cleaned
    except UnicodeError as e:
        raise ValueError(f"Unicode encoding issue: {e}")
```

### Prevention Strategies
- **Explicit field validation** for all string fields
- **Type coercion handling** with custom validators
- **Unicode normalization** for international text
- **Comprehensive test cases** covering edge cases
- **Clear error messages** for validation failures

---

## [MemoryID: 20250810-MM22] LLM Provider Integration Issues
**Type**: bug_pattern  
**Priority**: 1  
**Tags**: llm, api-integration, rate-limits, timeout, error-handling

### Bug Pattern Description
LLM provider integration failures due to rate limiting, API timeouts, authentication issues, and response format inconsistencies.

### Common Symptoms
- Intermittent API failures with different providers
- Rate limit exceeded errors during peak usage
- Authentication token expiration issues
- Response parsing errors due to format variations
- Timeout exceptions on complex queries

### Problematic Integration Patterns
```python
# PROBLEMATIC - No error handling or retry logic
def query_llm(prompt: str) -> str:
    response = requests.post(
        f"{provider_url}/api/generate",
        json={"prompt": prompt},
        headers={"Authorization": f"Bearer {api_key}"}
    )
    return response.json()["response"]  # Multiple failure points

# PROBLEMATIC - No provider failover
def get_philosophy_response(question: str) -> str:
    if default_provider == "ollama":
        return query_ollama(question)
    else:
        raise ValueError("Only Ollama supported")
```

### Solution Patterns
```python
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

class LLMProviderManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.providers = {
            "ollama": self._query_ollama,
            "openrouter": self._query_openrouter,
            "gemini": self._query_gemini,
            "anthropic": self._query_anthropic
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def query_with_failover(self, prompt: str) -> LLMResponse:
        """Query LLM with automatic provider failover."""
        primary_provider = self.settings.default_llm_provider
        
        try:
            return await self._query_provider(primary_provider, prompt)
        except (RateLimitError, TimeoutError, AuthenticationError) as e:
            logger.warning(f"Primary provider {primary_provider} failed: {e}")
            
            if self.settings.enable_provider_failover:
                return await self._try_fallback_providers(prompt, exclude=primary_provider)
            raise
    
    async def _query_provider(self, provider: str, prompt: str) -> LLMResponse:
        """Query specific provider with comprehensive error handling."""
        if provider not in self.providers:
            raise ValueError(f"Unsupported provider: {provider}")
        
        try:
            response = await self.providers[provider](prompt)
            return LLMResponse(
                content=response.content,
                provider=provider,
                token_usage=response.token_usage,
                cost=self._calculate_cost(provider, response.token_usage)
            )
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Timeout querying {provider}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise RateLimitError(f"Rate limit exceeded for {provider}")
            elif e.response.status_code == 401:
                raise AuthenticationError(f"Authentication failed for {provider}")
            else:
                raise LLMProviderError(f"HTTP error {e.response.status_code} for {provider}")
```

### Rate Limiting and Cost Management
```python
class CostTracker:
    def __init__(self):
        self.daily_usage = defaultdict(float)
        self.query_costs = []
    
    def check_budget(self, provider: str, estimated_cost: float) -> bool:
        """Check if query fits within budget constraints."""
        daily_cost = self.daily_usage[date.today()]
        query_cost_limit = self.settings.max_cost_per_query
        
        if estimated_cost > query_cost_limit:
            raise CostLimitError(f"Query cost {estimated_cost} exceeds limit {query_cost_limit}")
        
        if daily_cost + estimated_cost > self.settings.daily_cost_limit:
            raise CostLimitError(f"Daily budget would be exceeded")
        
        return True
    
    def record_usage(self, provider: str, cost: float):
        """Record actual usage for budget tracking."""
        self.daily_usage[date.today()] += cost
        self.query_costs.append({
            "provider": provider,
            "cost": cost,
            "timestamp": datetime.utcnow()
        })
```

### Prevention Strategies
- **Comprehensive error handling** for all provider interactions
- **Automatic retry logic** with exponential backoff
- **Provider failover** for reliability
- **Cost tracking and budgeting** to prevent overspend
- **Response validation** to ensure consistent format
- **Authentication token refresh** for long-running services

---

## [MemoryID: 20250810-MM23] Memory Management and Scaling Issues
**Type**: bug_pattern  
**Priority**: 2  
**Tags**: memory, performance, scaling, embeddings, caching

### Bug Pattern Description
Memory leaks and performance degradation when processing large philosophical texts and maintaining vector embeddings in memory.

### Common Symptoms
- Gradually increasing memory usage over time
- OutOfMemory errors when processing large documents
- Slow performance as system runs longer
- Cache invalidation issues
- Embedding storage consuming excessive memory

### Problematic Memory Patterns
```python
# PROBLEMATIC - Keeping all embeddings in memory
class DocumentProcessor:
    def __init__(self):
        self.document_embeddings = {}  # Never cleared!
        self.processed_chunks = []     # Grows indefinitely
    
    def process_document(self, document: Document):
        chunks = self.create_chunks(document)
        for chunk in chunks:
            embedding = self.generate_embedding(chunk.text)
            self.document_embeddings[chunk.id] = embedding  # Memory leak
            self.processed_chunks.append(chunk)  # More memory leak

# PROBLEMATIC - Large objects in cache without expiration
@lru_cache(maxsize=None)  # Unlimited cache size!
def get_document_analysis(doc_id: str) -> LargeAnalysisObject:
    # Returns large analysis object that stays in memory forever
    return perform_expensive_analysis(doc_id)
```

### Solution Patterns
```python
from functools import lru_cache
from typing import Generator
import gc

class OptimizedDocumentProcessor:
    def __init__(self):
        # Limited cache with automatic eviction
        self._embedding_cache = {}
        self._max_cache_size = 1000
    
    @lru_cache(maxsize=100)  # Limited cache size
    def get_document_analysis(self, doc_id: str) -> AnalysisResult:
        """Cache analysis with size limits."""
        return self._perform_analysis(doc_id)
    
    def process_document_streaming(self, document: Document) -> Generator[ProcessedChunk, None, None]:
        """Process document in streaming fashion to control memory."""
        for chunk in self._create_chunks_streaming(document):
            # Process one chunk at a time
            embedding = self._generate_embedding(chunk.text)
            
            # Store embedding in database, not memory
            self._store_embedding_in_db(chunk.id, embedding)
            
            # Yield processed chunk and let caller decide retention
            yield ProcessedChunk(chunk=chunk, embedding_stored=True)
            
            # Explicit cleanup for large objects
            del embedding
    
    def _manage_embedding_cache(self, chunk_id: str, embedding: List[float]):
        """Manage embedding cache with size limits."""
        if len(self._embedding_cache) >= self._max_cache_size:
            # Remove oldest entries (LRU eviction)
            oldest_key = next(iter(self._embedding_cache))
            del self._embedding_cache[oldest_key]
        
        self._embedding_cache[chunk_id] = embedding
    
    def cleanup_resources(self):
        """Explicit resource cleanup."""
        self._embedding_cache.clear()
        gc.collect()  # Force garbage collection

# Batch processing with memory management
class BatchProcessor:
    def process_documents_in_batches(self, documents: List[Document], batch_size: int = 10):
        """Process documents in controlled batches."""
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            # Process batch
            results = []
            for doc in batch:
                result = self.process_document(doc)
                results.append(result)
            
            # Yield results and clear batch from memory
            yield results
            
            # Explicit cleanup
            del batch, results
            gc.collect()
```

### Memory Monitoring
```python
import psutil
import logging

class MemoryMonitor:
    def __init__(self, threshold_mb: int = 1000):
        self.threshold_mb = threshold_mb
        self.process = psutil.Process()
    
    def check_memory_usage(self) -> Dict[str, Any]:
        """Monitor current memory usage."""
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        status = {
            "memory_mb": memory_mb,
            "threshold_mb": self.threshold_mb,
            "warning": memory_mb > self.threshold_mb,
            "percent_used": self.process.memory_percent()
        }
        
        if status["warning"]:
            logging.warning(f"High memory usage: {memory_mb:.1f}MB")
        
        return status
    
    def trigger_cleanup_if_needed(self):
        """Trigger cleanup if memory usage is high."""
        if self.check_memory_usage()["warning"]:
            # Clear caches
            gc.collect()
            
            # Clear any application-specific caches
            if hasattr(self, 'clear_application_caches'):
                self.clear_application_caches()
```

### Prevention Strategies
- **Stream processing** for large documents
- **Limited cache sizes** with LRU eviction
- **Explicit resource cleanup** after processing
- **Memory monitoring** with automatic cleanup triggers
- **Batch processing** with controlled memory usage
- **Database storage** instead of in-memory retention for large objects

---

## Bug Pattern Dependencies

### Database Issues Chain
1. **Connection Management** (MM20) → **All Database Operations**
2. **Validation Issues** (MM21) → **Data Quality Problems**

### Integration Issues Chain  
1. **LLM Provider Issues** (MM22) → **Response Generation Failures**
2. **Memory Issues** (MM23) → **System Performance Degradation**

### Prevention Strategy Integration
- All patterns include comprehensive error handling
- Memory management applies to all processing operations
- Database connection patterns used throughout system
- LLM provider patterns essential for system reliability

### Monitoring and Detection
- Automated health checks for all critical components
- Performance monitoring for early issue detection
- Resource usage tracking for capacity planning
- Error pattern analysis for prevention improvements

**Last Updated**: 2025-08-10  
**Review Schedule**: Weekly for critical bugs, monthly for prevention strategy updates