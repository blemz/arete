# Memory System Migration Complete

Configuration management information has been migrated to the hybrid memory system.

## Configuration Information Now Located At:

- **Configuration Patterns**: `../.memory/architecture/patterns.md`
- **Configuration Learnings**: `../.memory/development/learnings.md` → [MemoryID: 20250810-MM19]
- **Multi-Provider Setup**: `../.memory/architecture/decisions.md` → [MemoryID: 20250810-MM01]

## Quick Reference - Current Config Files:
- `development.env` - Local development with multi-provider LLM support
- `production.env` - Production deployment settings
- `schemas/neo4j_schema.cypher` - Graph database schema
- `schemas/weaviate_schema.json` - Vector database schema


For detailed configuration documentation including:
- Environment-specific setup patterns
- Multi-provider LLM configuration
- Database schema design decisions
- Security considerations and validation

Refer to the hybrid memory system at `../.memory/`.


### production.env ✅ (COMPLETED - Enhanced with Multi-Provider Support)
**Purpose**: Production deployment settings with cloud provider integration
**Usage**: Loaded in production containers

```env
# Database connections for Docker service names
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j  
NEO4J_PASSWORD=password
WEAVIATE_URL=http://weaviate:8080

# LLM Provider Configuration
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=openhermes2.5-mistral

# Cloud Provider API Keys (via Docker secrets/env)
# OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
# GEMINI_API_KEY=${GEMINI_API_KEY}
# ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

# Provider Management (Production settings)
DEFAULT_LLM_PROVIDER=ollama
ENABLE_PROVIDER_FAILOVER=true
MAX_COST_PER_QUERY=0.05

# Production logging
LOG_LEVEL=INFO
DEBUG=false

# Production RAG settings (Higher concurrency)
MAX_CONTEXT_TOKENS=5000
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_CONCURRENT_REQUESTS=50
RESPONSE_TIMEOUT=60
```

### Key Configuration Principles

1. **Environment Parity**: Development and production use same structure
2. **Secret Management**: Sensitive data via environment variables only
3. **Validation**: All values validated by Pydantic Settings class
4. **Defaults**: Sensible defaults provided for all optional settings

## Database Schemas

### Neo4j Schema ✅ (COMPLETED)
**File**: `schemas/neo4j_schema.cypher`
**Purpose**: Define graph database structure, constraints, and indexes

#### Key Features Implemented:
```cypher
-- Node Constraints (Unique IDs)
CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT citation_id IF NOT EXISTS FOR (ct:Citation) REQUIRE ct.id IS UNIQUE;

-- Performance Indexes
CREATE INDEX document_title IF NOT EXISTS FOR (d:Document) ON (d.title);
CREATE INDEX document_author IF NOT EXISTS FOR (d:Document) ON (d.author);
CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name);
CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type);

-- Full-Text Search Indexes
CREATE FULLTEXT INDEX document_fulltext IF NOT EXISTS 
FOR (d:Document) ON EACH [d.title, d.content, d.author];
CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS 
FOR (e:Entity) ON EACH [e.name, e.description, e.properties];
```

#### Schema Design Decisions:
- **Unique Constraints**: Prevent duplicate entities and ensure data integrity
- **Property Indexes**: Optimize common query patterns (author, title, type)
- **Full-text Indexes**: Enable semantic search capabilities
- **Relationship Indexes**: Support graph traversal performance

### Weaviate Schema ✅ (COMPLETED)
**File**: `schemas/weaviate_schema.json`
**Purpose**: Define vector database classes for semantic search

#### Key Classes Defined:
1. **Document Class**: Full document storage with embeddings
2. **Chunk Class**: Text chunks with position and metadata
3. **Entity Class**: Named entities with confidence scores
4. **Concept Class**: Philosophical concepts with definitions

#### Example Class Definition:
```json
{
  "class": "Document",
  "description": "A philosophical document or text",
  "vectorizer": "text2vec-transformers",
  "moduleConfig": {
    "text2vec-transformers": {
      "poolingStrategy": "masked_mean",
      "vectorizeClassName": true
    }
  },
  "properties": [
    {
      "name": "title",
      "dataType": ["text"],
      "description": "The title of the document",
      "moduleConfig": {
        "text2vec-transformers": {
          "skip": false,
          "vectorizePropertyName": false
        }
      }
    }
  ]
}
```

#### Vectorization Strategy:
- **Model**: text2vec-transformers (sentence-transformers)
- **Pooling**: masked_mean for better philosophical text representation
- **Cross-references**: neo4j_id fields link to graph database

## Configuration Loading Pattern

### Integration with Pydantic Settings
```python
# src/arete/config.py integration
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="config/development.env",  # Default env file
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Environment-specific loading
    @classmethod
    def load_for_environment(cls, env: str = "development"):
        """Load settings for specific environment."""
        env_file = f"config/{env}.env"
        return cls(_env_file=env_file)
```

### Usage in Application
```python
# Automatic environment detection
import os
from arete.config import Settings

# Load based on ENV variable
environment = os.getenv("ENV", "development")
settings = Settings.load_for_environment(environment)

# Or use default development settings
settings = Settings()
```

## Planned Configuration Extensions

### testing.env (PLANNED)
```env
# Isolated test environment
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=test_user
NEO4J_PASSWORD=test_password
WEAVIATE_URL=http://localhost:8081
OLLAMA_BASE_URL=http://localhost:11435

# Test-specific settings
LOG_LEVEL=DEBUG
DEBUG=true
MAX_CONTEXT_TOKENS=1000  # Smaller for faster tests
CHUNK_SIZE=500
CHUNK_OVERLAP=100
```

### Prompt Templates (PLANNED)
**Directory**: `prompts/`

#### philosophy_tutor.txt
```text
You are Arete, an AI philosophy tutor specializing in classical philosophical texts.

Your role:
- Provide accurate, well-cited responses to philosophical questions
- Guide students through Socratic questioning
- Explain complex concepts clearly and pedagogically
- Always cite specific sources with page/section references

Guidelines:
- Use the provided context documents to support your answers
- Include direct quotes when appropriate
- Explain the historical and philosophical significance
- Encourage deeper thinking through follow-up questions

Context documents:
{context_documents}

Student question: {question}

Response:
```

#### citation_generation.txt
```text
Generate accurate citations for philosophical sources.

Format requirements:
- Author. "Title." In Collection/Work, edited by Editor. Publisher, Year. Page/Section.
- For classical texts: Author. Title. Book/Chapter.Section (Stephanus/Bekker pagination if available).
- Include original language references where relevant

Source information:
{source_metadata}

Citation:
```

### Data Configuration Files (PLANNED)

#### entity_types.yaml
```yaml
# Philosophical entity type hierarchy
entity_types:
  Person:
    description: "Individual philosophers, historical figures"
    properties:
      - birth_year
      - death_year
      - nationality
      - philosophical_school
    
  Concept:
    description: "Abstract philosophical concepts and ideas"
    properties:
      - definition
      - category
      - related_concepts
      - historical_development
    
  Work:
    description: "Philosophical texts, books, dialogues"
    properties:
      - author
      - date_written
      - genre
      - influence_score
    
  School:
    description: "Philosophical schools and movements"
    properties:
      - founder
      - key_principles
      - historical_period
      - geographical_origin
```

#### concept_hierarchy.yaml
```yaml
# Hierarchical organization of philosophical concepts
philosophical_domains:
  Ethics:
    subcategories:
      - Virtue Ethics
      - Deontological Ethics
      - Consequentialism
    key_concepts:
      - Justice
      - Virtue
      - Good
      - Duty
      - Happiness
      
  Metaphysics:
    subcategories:
      - Ontology
      - Philosophy of Mind
      - Free Will
    key_concepts:
      - Being
      - Substance
      - Causation
      - Identity
      - Consciousness
      
  Epistemology:
    subcategories:
      - Theory of Knowledge
      - Skepticism
      - Rationalism
      - Empiricism
    key_concepts:
      - Knowledge
      - Belief
      - Truth
      - Justification
      - Experience
```

## Security Considerations

### Environment Variable Security
```bash
# Never commit actual secrets to version control
# Use placeholder values in committed .env files
NEO4J_PASSWORD=password  # Override in production
OLLAMA_API_KEY=your_api_key_here

# Use Docker secrets for production
docker secret create neo4j_password /path/to/secret
```

### Configuration Validation
```python
# Automatic validation in Settings class
from pydantic import Field, validator

class Settings(BaseSettings):
    # Validate URIs
    neo4j_uri: str = Field(..., regex=r"^bolt://.*:\d+$")
    
    # Validate password complexity (production)
    neo4j_password: str = Field(..., min_length=8)
    
    @validator("neo4j_password")
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v
```

## Configuration Deployment

### Docker Integration
```dockerfile
# Dockerfile configuration loading
COPY config/ /app/config/
ENV ENV=production

# Load production environment
CMD ["python", "-m", "arete", "--env", "production"]
```

### Kubernetes ConfigMaps (PLANNED)
```yaml
# k8s-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: arete-config
data:
  production.env: |
    NEO4J_URI=bolt://neo4j-service:7687
    WEAVIATE_URL=http://weaviate-service:8080
    LOG_LEVEL=INFO
    DEBUG=false
```

## Monitoring Configuration

### Logging Configuration (IN PROGRESS)
```python
# Via settings.logging_config property
{
    "level": "INFO",
    "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
    "backtrace": False,  # Production setting
    "diagnose": False,   # Production setting
    "rotation": "10 MB",
    "retention": "1 week",
    "compression": "zip"
}
```

### Performance Monitoring (PLANNED)
```env
# Observability settings
METRICS_ENABLED=true
METRICS_PORT=9090
TRACING_ENABLED=true
JAEGER_ENDPOINT=http://jaeger:14268
```

## Configuration Testing

### Validation Tests
```python
# tests/test_config.py already validates:
def test_environment_loading():
    """Test loading from different environment files."""
    dev_settings = Settings.load_for_environment("development")
    prod_settings = Settings.load_for_environment("production")
    
    assert dev_settings.debug is True
    assert prod_settings.debug is False
```

### Schema Validation (PLANNED)
```python
def test_neo4j_schema_validity():
    """Test Neo4j schema can be executed without errors."""
    with open("config/schemas/neo4j_schema.cypher") as f:
        schema_commands = f.read()
    
    # Execute against test database
    session.run(schema_commands)
    
    # Verify constraints were created
    result = session.run("SHOW CONSTRAINTS")
    constraints = [record["name"] for record in result]
    
    assert "document_id" in constraints
    assert "entity_id" in constraints
```

## Next Configuration Priorities

1. **Testing Environment** (IMMEDIATE)
   - Create testing.env for isolated test runs
   - Configure test database connections
   - Add test-specific optimizations

2. **Prompt Templates** (WEEK 2)
   - Philosophy tutor prompts
   - Citation generation templates
   - Validation prompt templates

3. **Data Configuration** (WEEK 3)
   - Entity type definitions
   - Concept hierarchy mapping
   - Citation format specifications

4. **Production Hardening** (WEEK 4)
   - Secret management integration
   - Configuration validation enhancement
   - Monitoring configuration

---

**Last Updated**: 2025-08-08  
**Status**: Foundation configuration completed, prompt templates and data configs pending  
**Integration**: Fully integrated with Pydantic Settings system