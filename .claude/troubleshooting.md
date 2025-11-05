# Arete Troubleshooting Guide

## Common Issues & Solutions

### Database Connection Issues

#### Neo4j Connection Failed

**Symptoms**:
- `ServiceUnavailable: Failed to establish connection`
- `AuthError: The client is unauthorized due to authentication failure`

**Solutions**:
```bash
# 1. Check Neo4j is running
docker ps | grep neo4j

# 2. Restart Neo4j
docker restart neo4j

# 3. Verify credentials in .env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# 4. Test connection manually
python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'your_password')); driver.verify_connectivity()"
```

#### Weaviate Connection Failed

**Symptoms**:
- `WeaviateStartUpError: Weaviate is not ready`
- `ConnectionError: HTTPConnectionPool`

**Solutions**:
```bash
# 1. Check Weaviate is running
docker ps | grep weaviate

# 2. Check Weaviate health
curl http://localhost:8080/v1/.well-known/ready

# 3. View Weaviate logs
docker logs weaviate

# 4. Restart Weaviate
docker restart weaviate
```

#### Redis Connection Issues

**Symptoms**:
- `redis.exceptions.ConnectionError`
- Application slower than expected

**Solutions**:
```bash
# 1. Check if Redis is required
# Redis is optional - application will work without it

# 2. If needed, start Redis
docker run -d --name redis -p 6379:6379 redis:latest

# 3. Update .env
REDIS_URL=redis://localhost:6379

# 4. Or disable Redis caching
# Comment out REDIS_URL in .env
```

### Embedding Generation Issues

#### Ollama Resource Exhaustion

**Symptoms**:
- Computer freezes during embedding generation
- Out of memory errors
- Very slow embedding generation (>5min per batch)

**Solutions**:
```bash
# Switch to cloud embedding provider
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=your_key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Alternative: Use Gemini
EMBEDDING_PROVIDER=gemini
GOOGLE_API_KEY=your_key
GEMINI_EMBEDDING_MODEL=text-embedding-004
```

#### API Rate Limits

**Symptoms**:
- `RateLimitError: Rate limit exceeded`
- 429 HTTP status codes

**Solutions**:
```python
# Reduce batch size in embedding service
EMBEDDING_BATCH_SIZE=50  # Down from 100

# Add retry logic with exponential backoff
# (Already implemented in embedding services)

# Switch to provider with higher limits
# OpenRouter often has higher limits than direct APIs
```

### Ingestion Issues

#### Pydantic Validation Errors

**Symptoms**:
- `ValidationError: X validation errors for Chunk`
- Fields missing or incorrect types

**Solutions**:
```python
# Check chunk model matches data structure
# Ensure all required fields are present:
# - id, document_id, content, position, word_count

# Verify metadata and properties are dicts
chunk = Chunk(
    id=chunk_id,
    document_id=doc_id,
    content=text,
    position=0.0,
    word_count=len(text.split()),
    metadata={},  # Must be dict, not None
    properties={}  # Must be dict, not None
)
```

#### Weaviate 422 Errors

**Symptoms**:
- `UnexpectedStatusCodeException: 422`
- "Invalid properties" errors

**Solutions**:
```python
# Ensure no None values in Weaviate objects
data_object = {
    "content": chunk.content,
    "documentId": chunk.document_id,
    "position": chunk.position,
    "wordCount": chunk.word_count,
    "metadata": chunk.metadata or {},  # Never None
    "properties": chunk.properties or {}  # Never None
}
```

#### Neo4j Type Errors

**Symptoms**:
- `Map{} type mismatch` errors
- `Missing method get_canonical_form`

**Solutions**:
```python
# Ensure entity has canonical_form property
entity = Entity(
    id=entity_id,
    name=name,
    entity_type=entity_type,
    description=description,
    canonical_form=canonical_form,  # Required!
    properties=properties or {}
)

# Convert properties to proper Neo4j types
properties = {k: str(v) if not isinstance(v, (str, int, float, bool)) else v
              for k, v in properties.items()}
```

### RAG Pipeline Issues

#### No Results from Vector Search

**Symptoms**:
- Empty results from semantic search
- "No relevant chunks found" messages

**Solutions**:
```bash
# 1. Verify embeddings exist
python quick_verify.py

# 2. Check embedding dimensions match
# OpenAI text-embedding-3-small: 1536d
# Gemini text-embedding-004: 768d

# 3. Lower similarity threshold
MIN_SIMILARITY_THRESHOLD=0.5  # Down from 0.7

# 4. Increase result limit
VECTOR_SEARCH_LIMIT=20  # Up from 10
```

#### LLM Timeout Errors

**Symptoms**:
- `TimeoutError` during response generation
- Requests taking >120 seconds

**Solutions**:
```python
# Increase timeout for reasoning models
LLM_TIMEOUT=180  # For GPT-5-mini

# Reduce context size
MAX_CONTEXT_CHUNKS=5  # Down from 10

# Switch to faster model
OPENAI_MODEL=gpt-4-turbo  # Instead of gpt-5-mini
```

#### Citations Not Appearing

**Symptoms**:
- Responses lack source references
- Empty citation panels

**Solutions**:
```python
# 1. Verify citation extraction in RAG service
# Check chat_rag_clean.py for citation formatting

# 2. Ensure chunks have position data
# Verify during ingestion: chunk.position is set

# 3. Check citation display in UI
# Verify Reflex state includes message_sources
```

### UI Issues

#### Reflex Won't Start

**Symptoms**:
- `ModuleNotFoundError` errors
- Port already in use
- Blank screen

**Solutions**:
```bash
# 1. Reinstall Reflex
pip install --upgrade reflex

# 2. Clear Reflex cache
rm -rf .web

# 3. Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# 4. Rebuild frontend
cd src/arete/ui/reflex_app
reflex init  # If needed
reflex run

# 5. Check for import errors
python -c "from arete.ui.reflex_app import app"
```

#### CSS Not Loading

**Symptoms**:
- Unstyled or broken layout
- Missing colors/fonts

**Solutions**:
```bash
# 1. Verify tailwind.config.js exists
ls src/arete/ui/reflex_app/tailwind.config.js

# 2. Rebuild Tailwind
cd src/arete/ui/reflex_app
npm install
npm run build

# 3. Clear browser cache
# Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)

# 4. Check global.css imports
# Verify Google Fonts URLs are accessible
```

#### State Not Updating

**Symptoms**:
- UI doesn't respond to interactions
- Messages not appearing in chat

**Solutions**:
```python
# 1. Check event handlers are properly decorated
@rx.event
def handle_submit(self):
    # Event logic

# 2. Verify state variables are reactive
chat_messages: list[dict] = []  # Use simple types

# 3. Check for async issues
# Use await for async operations
async def send_message(self):
    result = await self.process_query()

# 4. Add debug logging
print(f"State updated: {self.chat_messages}")
```

### Performance Issues

#### Slow Query Performance

**Symptoms**:
- Queries taking >10 seconds
- High CPU/memory usage

**Solutions**:
```cypher
# 1. Add Neo4j indexes
CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name);
CREATE INDEX chunk_position IF NOT EXISTS FOR (c:Chunk) ON (c.position);

# 2. Optimize Cypher queries
// Use LIMIT
MATCH (e:Entity)
WHERE e.name CONTAINS $query
RETURN e
LIMIT 10

# 3. Enable query caching
REDIS_CACHE_ENABLED=true
QUERY_CACHE_TTL=3600
```

#### High Memory Usage

**Symptoms**:
- Out of memory errors
- Application crashes

**Solutions**:
```python
# 1. Use generators for large datasets
def process_chunks():
    for chunk in chunks_generator():
        yield process(chunk)

# 2. Batch operations
for i in range(0, len(items), batch_size):
    batch = items[i:i+batch_size]
    process_batch(batch)

# 3. Release connections promptly
with neo4j_client.session() as session:
    # Use session
    pass  # Connection released here

# 4. Stream large files
with open(file_path) as f:
    for line in f:  # Don't load entire file
        process(line)
```

### Testing Issues

#### Tests Failing After Changes

**Symptoms**:
- Previously passing tests now fail
- Inconsistent test results

**Solutions**:
```bash
# 1. Clear pytest cache
pytest --cache-clear

# 2. Run tests in isolation
pytest tests/test_specific.py::test_name -v

# 3. Check for test dependencies
# Ensure tests don't rely on execution order

# 4. Verify mock data is up-to-date
# Update fixtures to match current models

# 5. Check for database state pollution
# Use test database or clean state between tests
```

#### Import Errors in Tests

**Symptoms**:
- `ModuleNotFoundError` in test files
- Tests can't find application modules

**Solutions**:
```bash
# 1. Install package in editable mode
pip install -e .

# 2. Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"

# 3. Use absolute imports
from arete.services import ChunkService  # Not: from services import...

# 4. Check test discovery
pytest --collect-only
```

## Known Issues & Workarounds

### Issue: Weaviate gRPC Connection Errors

**Status**: Known issue with some Weaviate versions
**Workaround**: Use HTTP instead of gRPC, or upgrade Weaviate to latest version

### Issue: Windows Unicode Errors

**Status**: Windows console doesn't fully support Greek characters
**Workaround**: Use ASCII-safe output, or run in WSL/Linux environment

### Issue: Ollama Model Download Slow

**Status**: Large models (>5GB) take time to download
**Workaround**: Use cloud providers (OpenAI, Gemini) for faster setup

## Memory System

Arete uses a `.memory/` directory for persistent knowledge storage across sessions.

### Memory Categories

**Architecture Memories**:
- Technical decisions
- System design patterns
- Database schemas
- Component relationships

**Development Memories**:
- TDD workflows
- Bug patterns and solutions
- Performance learnings
- Integration challenges

**Archived Memories**:
- Historical context
- Superseded implementations
- Migration notes

### Reading Memories

```bash
# List available memories
ls .memory/

# Read specific memory
cat .memory/development/phase-7-4-production-rag-cli.md
```

### When to Create Memories

- After completing major features/phases
- When solving complex bugs
- After architectural decisions
- When discovering performance optimizations

## Development Phase History

### Completed Phases

- **Phase 1**: Foundation (Database clients, models, configuration)
- **Phase 2**: Text processing (Chunking, PDF extraction, embeddings)
- **Phase 3**: Retrieval systems (BM25/SPLADE, vectors, re-ranking)
- **Phase 4**: LLM integration (Multi-provider support)
- **Phase 5**: User interface (Chat, document viewer, accessibility)
- **Phase 6**: Advanced analytics (Centrality, communities, influence)
- **Phase 7**: Production pipeline (Ingestion, embeddings, RAG CLI, GPT-5-mini)
- **Phase 8**: Reflex migration & redesign (Modern UI, classical aesthetic)

### Current Phase: 8.5 - UI Redesign

**Status**: Sprint 1 Phase 1 Complete
**Next**: Sprint 2 - Conversation History Sidebar

See `planning/todo.md` for detailed sprint plan.

## Getting Additional Help

### Documentation
- [Architecture Guide](.claude/architecture.md) - System design details
- [Conventions Guide](.claude/conventions.md) - Development standards
- [Deployment Guide](.claude/deployment.md) - Setup and launch procedures

### Debugging Tips

1. **Enable Debug Logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **Use Interactive Debugger**:
```python
import pdb; pdb.set_trace()
```

3. **Check Service Health**:
```bash
# Neo4j
curl http://localhost:7474/

# Weaviate
curl http://localhost:8080/v1/.well-known/ready

# Redis
redis-cli ping
```

4. **Monitor Resource Usage**:
```bash
# Docker stats
docker stats

# Python memory profiling
pip install memory_profiler
python -m memory_profiler script.py
```

5. **Verify Environment**:
```python
from arete.config import Settings
settings = Settings()
print(settings.model_dump())
```

### Reporting Issues

When reporting issues, include:
- Error message and full stack trace
- Steps to reproduce
- Environment details (OS, Python version, dependency versions)
- Relevant log excerpts
- Configuration (with secrets redacted)

---

**Last Updated**: 2025-11-05
**Related**: [Architecture](.claude/architecture.md), [Deployment](.claude/deployment.md), [Conventions](.claude/conventions.md)
