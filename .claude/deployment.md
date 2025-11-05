# Arete Deployment Guide

## Quick Start Commands

### Development Environment

**Launch Reflex Web Interface** (Recommended):
```bash
cd src/arete/ui/reflex_app
reflex run
```

**Production RAG CLI**:
```bash
python chat_rag_clean.py "What is virtue?"
```

**Legacy CLI** (Mock responses):
```bash
python chat_fast.py "What is virtue?"
```

**Run Test Suite**:
```bash
# All tests
pytest

# With coverage report
pytest --cov=src/arete --cov-report=html

# Specific test file
pytest tests/unit/test_chunk_service.py

# Verbose output
pytest -v
```

**Code Quality Checks**:
```bash
# Lint code
ruff check .

# Format code
black .

# Type checking
mypy src/arete

# All quality checks
ruff check . && black --check . && mypy src/arete
```

## Environment Configuration

### Required Environment Variables

Create a `.env` file in the project root:

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password
NEO4J_DATABASE=neo4j

# Weaviate Configuration
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=  # Optional, for cloud deployment

# Redis Configuration (Optional)
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=  # Optional

# LLM Provider Configuration
KG_LLM_PROVIDER=openai  # Options: openai, anthropic, gemini, openrouter, ollama

# OpenAI (if KG_LLM_PROVIDER=openai)
OPENAI_API_KEY=sk-your_openai_key
OPENAI_MODEL=gpt-5-mini  # or gpt-4, gpt-3.5-turbo

# Anthropic (if KG_LLM_PROVIDER=anthropic)
ANTHROPIC_API_KEY=your_anthropic_key
ANTHROPIC_MODEL=claude-3-opus-20240229

# Google Gemini (if KG_LLM_PROVIDER=gemini)
GOOGLE_API_KEY=your_google_key
GEMINI_MODEL=gemini-pro

# OpenRouter (if KG_LLM_PROVIDER=openrouter)
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=anthropic/claude-3-opus

# Ollama (if KG_LLM_PROVIDER=ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Embedding Provider Configuration
EMBEDDING_PROVIDER=openai  # Options: openai, gemini, openrouter, anthropic, ollama

# OpenAI Embeddings (if EMBEDDING_PROVIDER=openai)
OPENAI_EMBEDDING_MODEL=text-embedding-3-small  # 1536 dimensions

# Gemini Embeddings (if EMBEDDING_PROVIDER=gemini)
GEMINI_EMBEDDING_MODEL=text-embedding-004  # 768 dimensions

# Application Settings
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
ENVIRONMENT=development  # development, staging, production
```

### Provider-Specific Models

**OpenAI Models**:
- `gpt-5-mini`: Advanced reasoning (recommended for Arete)
- `gpt-4-turbo`: Fast, high quality
- `gpt-4`: Standard GPT-4
- `gpt-3.5-turbo`: Cost-effective

**OpenAI Embeddings**:
- `text-embedding-3-small`: 1536d, cost-effective (recommended)
- `text-embedding-3-large`: 3072d, highest quality
- `text-embedding-ada-002`: 1536d, legacy

**Anthropic Models**:
- `claude-3-opus-20240229`: Most capable
- `claude-3-sonnet-20240229`: Balanced
- `claude-3-haiku-20240307`: Fast, cost-effective

**Gemini Models**:
- `gemini-pro`: Standard Gemini
- `gemini-pro-vision`: With vision capabilities
- `text-embedding-004`: 768d embeddings

## Database Setup

### Neo4j Setup

**Option 1: Docker** (Recommended):
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  -v $PWD/neo4j/data:/data \
  neo4j:latest
```

**Option 2: Local Installation**:
1. Download Neo4j Desktop: https://neo4j.com/download/
2. Create new database
3. Start database
4. Update `.env` with connection details

**Verify Connection**:
```bash
python -c "from arete.database.neo4j_client import Neo4jClient; client = Neo4jClient(); print('Connected!' if client.verify_connectivity() else 'Failed')"
```

### Weaviate Setup

**Option 1: Docker** (Recommended):
```bash
docker run -d \
  --name weaviate \
  -p 8080:8080 \
  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
  -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
  -v $PWD/weaviate/data:/var/lib/weaviate \
  semitechnologies/weaviate:latest
```

**Option 2: Weaviate Cloud**:
1. Sign up at https://console.weaviate.cloud/
2. Create cluster
3. Update `.env` with cluster URL and API key

**Verify Connection**:
```bash
python -c "from arete.database.weaviate_client import WeaviateClient; client = WeaviateClient(); print('Connected!' if client.is_ready() else 'Failed')"
```

### Redis Setup (Optional)

**Docker**:
```bash
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:latest
```

**Verify Connection**:
```bash
python -c "import redis; r = redis.Redis(); r.ping() and print('Connected!')"
```

## Data Ingestion

### Ingest Classical Texts

**Ingest AI-Restructured Content**:
```bash
python ingest_restructured_text.py content/plato/republic_ai_restructured.md
```

**Ingest Standard Markdown**:
```bash
python ingest_text.py content/plato/apology.md
```

**Verify Ingestion**:
```bash
python quick_verify.py
```

Expected output:
```
=== Database Verification ===
Documents: 1
Chunks: 227
Entities: 83
Relationships: 109
Embeddings: 227
```

### Content Preparation

**Convert PDF to Markdown**:
```bash
python scripts/convert_pdf.py input.pdf output.md
```

**Enhance Text with Metadata**:
```bash
python scripts/enhance_text.py input.md enhanced_output.md
```

**Restructure for GraphRAG**:
```bash
python scripts/restructure_enhanced_text.py enhanced_input.md ai_restructured_output.md
```

## Docker Deployment

### Full Stack with Docker Compose

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:latest
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/your_password
    volumes:
      - neo4j_data:/data

  weaviate:
    image: semitechnologies/weaviate:latest
    ports:
      - "8080:8080"
    environment:
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: /var/lib/weaviate
    volumes:
      - weaviate_data:/var/lib/weaviate

  redis:
    image: redis:latest
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  arete:
    build: .
    ports:
      - "3000:3000"
    depends_on:
      - neo4j
      - weaviate
      - redis
    environment:
      NEO4J_URI: bolt://neo4j:7687
      WEAVIATE_URL: http://weaviate:8080
      REDIS_URL: redis://redis:6379
    env_file:
      - .env

volumes:
  neo4j_data:
  weaviate_data:
  redis_data:
```

**Launch Stack**:
```bash
docker-compose up -d
```

**View Logs**:
```bash
docker-compose logs -f arete
```

**Stop Stack**:
```bash
docker-compose down
```

### Build Application Container

**Dockerfile**:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3000

CMD ["reflex", "run", "--port", "3000"]
```

**Build Image**:
```bash
docker build -t arete:latest .
```

**Run Container**:
```bash
docker run -d \
  --name arete \
  -p 3000:3000 \
  --env-file .env \
  arete:latest
```

## Production Deployment

### Environment-Specific Configurations

**Development**:
- Local databases
- Debug logging enabled
- Hot reload for UI
- Mock data for testing

**Staging**:
- Cloud databases
- Info-level logging
- Production build
- Limited test data

**Production**:
- Production databases with replicas
- Warning-level logging
- Optimized builds
- Full content corpus
- HTTPS enforced
- API rate limiting
- Monitoring enabled

### Security Checklist

- [ ] All API keys in environment variables (not committed)
- [ ] Database passwords rotated
- [ ] HTTPS/TLS enabled for all connections
- [ ] CORS properly configured
- [ ] Input validation on all endpoints
- [ ] Rate limiting implemented
- [ ] Security headers configured
- [ ] Regular dependency updates
- [ ] Automated security scanning

### Performance Optimization

**Database Indexes**:
```cypher
// Neo4j indexes
CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name);
CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.entity_type);
CREATE INDEX chunk_document IF NOT EXISTS FOR (c:Chunk) ON (c.document_id);
```

**Weaviate Schema Optimization**:
- Use appropriate vectorizers
- Configure sharding for large datasets
- Enable compression for embeddings
- Set appropriate replication factors

**Application Tuning**:
```python
# Connection pooling
NEO4J_MAX_CONNECTION_POOL_SIZE=50
WEAVIATE_CONNECTION_POOL_SIZE=20

# Caching
REDIS_CACHE_TTL=3600
QUERY_CACHE_ENABLED=true

# Batch sizes
EMBEDDING_BATCH_SIZE=100
INGESTION_BATCH_SIZE=50
```

## Monitoring & Logging

### Application Logs

**Configure Logging**:
```python
# config/logging.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/arete.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'default',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file'],
    },
}
```

### Health Check Endpoint

```python
@app.get("/health")
async def health_check():
    """Check application and dependency health."""
    return {
        "status": "healthy",
        "database": {
            "neo4j": neo4j_client.verify_connectivity(),
            "weaviate": weaviate_client.is_ready(),
            "redis": redis_client.ping()
        },
        "version": "8.5.0"
    }
```

### Metrics Collection

**Prometheus Integration**:
```python
from prometheus_client import Counter, Histogram

query_counter = Counter('rag_queries_total', 'Total RAG queries')
query_duration = Histogram('rag_query_duration_seconds', 'RAG query duration')
```

## Troubleshooting

### Common Issues

**Port Already in Use**:
```bash
# Find process using port
lsof -ti:3000

# Kill process
kill -9 <PID>
```

**Database Connection Failed**:
```bash
# Check database status
docker ps | grep neo4j
docker logs neo4j

# Restart database
docker restart neo4j
```

**Out of Memory**:
```bash
# Increase Docker memory limit
# Docker Desktop → Settings → Resources → Memory

# Or use cloud embeddings instead of local Ollama
EMBEDDING_PROVIDER=openai
```

**Import Errors**:
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

For more troubleshooting guidance, see [Troubleshooting Guide](.claude/troubleshooting.md).

---

**Last Updated**: 2025-11-05
**Related**: [Architecture](.claude/architecture.md), [Troubleshooting](.claude/troubleshooting.md)
