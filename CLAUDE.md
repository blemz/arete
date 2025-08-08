# Arete Project - Claude Memory & Instructions

## Project Overview

**Arete** is a Graph-RAG (Retrieval-Augmented Generation) AI tutoring system specifically designed for classical philosophical texts. The system combines Neo4j knowledge graphs, Weaviate vector embeddings, and local LLM inference through Ollama to provide accurate, well-cited philosophical education.

## Development Principles

### Core Philosophy
- **Test-Driven Development (TDD)**: All tests written before implementation
- **Quality First**: >90% test coverage, comprehensive validation
- **Accuracy Over Speed**: Philosophical accuracy is paramount
- **Educational Focus**: Responses must be pedagogically valuable

### Development Workflow
1. **Red**: Write failing tests first
2. **Green**: Implement minimal code to pass tests  
3. **Refactor**: Improve code quality and performance
4. **Document**: Update documentation and memory files

## Project Structure & Memory

```
arete/
├── CLAUDE.md                 # This file - project-level memory
├── src/arete/               # Main application code
│   ├── CLAUDE.md            # Source code memory & conventions
│   ├── config.py ✅         # Configuration management (COMPLETED)
│   ├── models/              # Data models (IN PROGRESS)
│   │   └── CLAUDE.md        # Models memory & patterns
│   ├── graph/               # Neo4j operations (PENDING)
│   │   └── CLAUDE.md        # Graph operations memory
│   ├── rag/                 # RAG system (PENDING)
│   │   └── CLAUDE.md        # RAG system memory
│   ├── services/            # Business logic (PENDING)
│   │   └── CLAUDE.md        # Services memory
│   └── ui/                  # User interface (PENDING)
│       └── CLAUDE.md        # UI memory & patterns
├── tests/                   # Test suite
│   ├── CLAUDE.md            # Testing memory & conventions
│   └── test_config.py ✅    # Config tests (COMPLETED)
├── config/                  # Configuration files
│   ├── CLAUDE.md            # Configuration memory
│   ├── development.env ✅    # Dev environment config
│   ├── production.env ✅     # Prod environment config
│   └── schemas/             # Database schemas
│       ├── neo4j_schema.cypher ✅
│       └── weaviate_schema.json ✅
└── docs/                    # Documentation
    ├── CLAUDE.md            # Documentation memory
    ├── development_progress.md ✅
    └── README.md ✅
```

## Current Development Status

### Phase 1: Foundation and Infrastructure (15% Complete)
- ✅ **Docker Configuration**: All services configured and tested
- ✅ **Database Schemas**: Neo4j and Weaviate schemas created
- ✅ **Configuration System**: Pydantic-based config with full test coverage
- 🔄 **Core Data Models**: Document model tests in progress
- ⏳ **Database Connections**: Next priority

### Technology Stack Decisions

**Databases:**
- **Neo4j 5-community**: Knowledge graph storage with APOC plugins
- **Weaviate 1.23.7**: Vector embeddings with text2vec-transformers
- **Redis**: Caching layer (planned)

**LLM Infrastructure:**
- **Ollama**: Local LLM inference server with GPU support
- **OpenHermes-2.5**: Primary model for philosophical reasoning
- **sentence-transformers**: Embeddings for semantic similarity

**Backend Framework:**
- **FastAPI**: Async API server (planned)
- **Pydantic**: Data validation and settings management ✅
- **Streamlit**: Development UI (planned)

**Development Tools:**
- **pytest**: Testing framework with >90% coverage requirement ✅
- **black**: Code formatting (88 char lines) ✅
- **flake8**: Linting with strict configuration ✅
- **mypy**: Type checking with strict mode ✅

## Key Implementation Patterns

### Configuration Management (COMPLETED)
```python
# Pattern: Pydantic Settings with validation
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )
    
    # Database configs with validation
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_password: str = Field(repr=False)  # Security: hidden in repr
    
    # Custom validation
    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, v, info):
        # Validation logic here
        return v
```

### Test-Driven Development Pattern
```python
# 1. RED: Write failing test first
def test_document_creation_with_valid_data():
    document = Document(title="Republic", author="Plato", content="...")
    assert document.title == "Republic"

# 2. GREEN: Minimal implementation
class Document(BaseModel):
    title: str
    author: str
    content: str

# 3. REFACTOR: Add validation and features
class Document(BaseModel):
    title: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    
    @property
    def word_count(self) -> int:
        return len(self.content.split())
```

## Database Schema Memory

### Neo4j Schema (COMPLETED)
- **Nodes**: Document, Entity, Chunk, Citation
- **Relationships**: MENTIONS, RELATES_TO, CONTAINS, CITES, SUPPORTS
- **Indexes**: Performance indexes on all key properties
- **Constraints**: Unique IDs and required properties
- **Full-text**: Advanced text search capabilities

### Weaviate Schema (COMPLETED)
- **Classes**: Document, Chunk, Entity, Concept
- **Vectorizer**: text2vec-transformers for all text fields
- **Properties**: Rich metadata with cross-references to Neo4j
- **Configuration**: Optimized for philosophical text processing

## Quality Standards

### Test Coverage Requirements
- **Minimum**: 90% coverage for all new code
- **Target**: 95% coverage for critical paths
- **Categories**: Unit, integration, end-to-end tests
- **Mocking**: External dependencies mocked appropriately

### Code Quality Standards
- **Type Hints**: Required for all functions and methods
- **Docstrings**: Google-style documentation for public APIs
- **Error Handling**: Comprehensive exception handling
- **Logging**: Structured logging with correlation IDs

## Common Commands

### Development Setup
```bash
# Install in development mode
pip install -e ".[dev,all]"

# Start database services
docker-compose up -d neo4j weaviate ollama

# Run tests with coverage
pytest tests/ -v --cov=src/arete --cov-report=html

# Code quality checks
black src/ tests/
flake8 src/ tests/
mypy src/
```

### Database Management
```bash
# Initialize schemas
python scripts/init_databases.py

# Reset databases (development)
python scripts/reset_databases.py

# Backup production data
python scripts/backup_databases.py
```

## Critical Reminders

### Security Considerations
- Never commit credentials to version control
- Use environment variables for all secrets
- Implement input validation for all user inputs
- Sanitize all database queries to prevent injection

### Performance Considerations  
- Implement caching for expensive operations
- Use batch processing for large datasets
- Monitor database query performance
- Implement connection pooling

### Philosophical Accuracy
- All responses must be backed by citations
- Implement expert validation workflow
- Bias detection and mitigation required
- Multi-perspective representation essential

## Next Priority Tasks

1. **Complete Document Model**: Finish tests and implementation
2. **Entity Model**: Create with full relationship support
3. **Database Connections**: Neo4j and Weaviate clients
4. **Text Processing**: PDF and TEI-XML parsers
5. **RAG Pipeline**: Hybrid retrieval system

## Contact & Resources

- **Primary Documentation**: docs/development_progress.md
- **Task Tracking**: planning/TODO.md  
- **Architecture**: planning/PRD.md
- **Contributing**: CONTRIBUTING.md
- **Issues**: Use GitHub issues for tracking

---

**Last Updated**: 2025-08-08  
**Phase**: 1 (Foundation) - 15% Complete  
**Next Milestone**: Complete data models with 95% test coverage