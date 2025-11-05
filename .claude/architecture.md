# Arete System Architecture

## High-Level Overview

Arete is a Graph-RAG system that combines multiple retrieval strategies with knowledge graph integration to provide accurate, well-cited answers about classical philosophical texts.

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                    │
│  (Reflex Web App, CLI)                                      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                    RAG Pipeline Layer                        │
│  - Query Processing                                          │
│  - Hybrid Retrieval (Sparse + Dense + Graph)                │
│  - Re-ranking & Context Assembly                            │
│  - LLM Response Generation                                  │
└────────────┬───────────────────┬──────────────┬─────────────┘
             │                   │              │
┌────────────┴──────┐  ┌────────┴────────┐  ┌──┴──────────────┐
│  Vector Database  │  │ Knowledge Graph │  │  LLM Providers  │
│   (Weaviate)      │  │    (Neo4j)      │  │ (Multi-provider)│
│  - Embeddings     │  │  - Entities     │  │  - OpenAI       │
│  - Semantic Search│  │  - Relations    │  │  - Anthropic    │
└───────────────────┘  └─────────────────┘  │  - Gemini       │
                                             │  - OpenRouter   │
                                             │  - Ollama       │
                                             └─────────────────┘
```

## Core Components

### 1. Database Layer

**Neo4j (Knowledge Graph)**:
- Stores philosophical entities (concepts, persons, works)
- Relationship mapping between entities
- Temporal tracking of concept development
- Community detection and centrality analysis

**Weaviate (Vector Database)**:
- Semantic chunk embeddings (1536d for OpenAI, 768d for Gemini)
- Fast similarity search
- Metadata filtering capabilities
- Batch processing support

**Redis (Cache - Optional)**:
- Connection pooling
- Query result caching
- Session management

### 2. Processing Layer

**Text Processing Pipeline**:
- PDF extraction and cleaning
- Semantic chunking (context-aware boundaries)
- Entity recognition and extraction
- Relationship identification
- Metadata enrichment

**Embedding Services**:
- Multi-provider support (OpenAI, Gemini, OpenRouter, Anthropic, Ollama)
- Provider-based configuration via `EMBEDDING_PROVIDER` env variable
- Batch processing for efficiency
- Retry logic with exponential backoff

### 3. RAG Pipeline

**Hybrid Retrieval Strategy**:
1. **Sparse Retrieval**: BM25/SPLADE for keyword matching
2. **Dense Retrieval**: Vector similarity search
3. **Graph Retrieval**: Entity relationship traversal
4. **Re-ranking**: Cross-encoder scoring for relevance

**Context Assembly**:
- Chunk deduplication
- Relevance scoring and filtering
- Citation tracking with position markers
- Context window optimization

**Response Generation**:
- Multi-provider LLM integration
- Prompt engineering for philosophical accuracy
- Citation formatting and attribution
- Fallback mechanisms for service unavailability

### 4. User Interface Layer

**Reflex Web Application**:
- Component-based architecture
- Reactive state management
- Split-view layout (chat + document + citations)
- Real-time updates and interactions
- Responsive design (mobile, tablet, desktop)
- WCAG 2.1 AA accessibility compliance

**CLI Interfaces**:
- `chat_rag_clean.py`: Production RAG with full pipeline
- `chat_fast.py`: Legacy interface with mock responses

## Technology Stack

### Backend
- **Python 3.10+**: Core language
- **Neo4j**: Graph database
- **Weaviate**: Vector database
- **Redis**: Caching layer
- **Pydantic**: Data validation and type safety

### Frontend
- **Reflex**: Python-based reactive web framework
- **Tailwind CSS**: Utility-first styling
- **DaisyUI**: Component library
- **Custom Classical Theme**: Beige, gold, navy color palette

### LLM Providers
- **OpenAI**: GPT-5-mini for advanced reasoning
- **Anthropic**: Claude for nuanced analysis
- **Google Gemini**: Cost-effective alternative
- **OpenRouter**: Multi-model aggregator
- **Ollama**: Local model deployment

### Embedding Providers
- **OpenAI**: text-embedding-3-small (1536d)
- **Gemini**: text-embedding-004 (768d)
- **OpenRouter**: Multiple model access
- **Anthropic**: Feature-based fallback
- **Ollama**: Local embedding models

### Development Tools
- **pytest**: Testing framework (>80% coverage)
- **ruff**: Fast Python linter
- **black**: Code formatter
- **mypy**: Static type checking
- **Docker**: Containerization

## Data Models

### Chunk Model
```python
class Chunk:
    id: str
    document_id: str
    content: str
    position: float
    word_count: int
    metadata: dict
    embedding: List[float]
```

### Entity Model
```python
class Entity:
    id: str
    name: str
    entity_type: str  # CONCEPT, PERSON, WORK, etc.
    description: str
    canonical_form: str
    properties: dict
```

### Relationship Model
```python
class Relationship:
    source_id: str
    target_id: str
    relationship_type: str
    properties: dict
    confidence: float
```

## System Architecture Phases (Completed)

### Phase 1: Foundation ✅
- Database clients (Neo4j, Weaviate, Redis)
- Core models and schemas
- Configuration management

### Phase 2: Text Processing ✅
- Semantic chunking
- PDF extraction
- Embedding generation
- Citation tracking

### Phase 3: Retrieval Systems ✅
- BM25/SPLADE sparse retrieval
- Dense vector search
- Re-ranking mechanisms

### Phase 4: LLM Integration ✅
- Multi-provider support
- Prompt engineering
- Response generation

### Phase 5: User Interface ✅
- Chat interface
- Document viewer
- Accessibility features
- Responsive design

### Phase 6: Advanced Analytics ✅
- Centrality analysis (degree, betweenness, closeness, eigenvector, PageRank)
- Community detection
- Influence networks
- Historical development tracking

### Phase 7: Production Pipeline ✅
- Data ingestion pipeline
- Multi-provider embeddings
- Production RAG CLI
- GPT-5-mini integration

### Phase 8: Reflex Migration & Redesign ✅ (In Progress)
- Complete Streamlit → Reflex migration
- Classical aesthetic implementation
- Knowledge-chat template
- Enhanced citation system

## Key Technical Decisions

### Repository Pattern
- Clean separation of data access from business logic
- Consistent interfaces across all database operations
- Easy testing with mock repositories

### Multi-Provider Architecture
- User-controlled provider selection via environment variables
- Graceful fallbacks when services unavailable
- Cost optimization through provider choice

### Hybrid Retrieval Strategy
- Combines strengths of sparse, dense, and graph methods
- Higher accuracy than single-strategy approaches
- Flexible re-ranking for different query types

### Test-Driven Development
- Strict Red-Green-Refactor cycle
- >90% test coverage requirement
- Contract-based testing approach
- Quality over quantity principle

### Type Safety
- Comprehensive type hints throughout codebase
- Pydantic validation for all data models
- Static type checking with mypy

## Performance Optimizations

### Database
- Connection pooling for all database clients
- Batch operations for ingestion
- Query result caching
- Index optimization on frequently queried fields

### Embedding Generation
- Batch processing (100 chunks per batch for OpenAI)
- Retry logic with exponential backoff
- Cloud APIs to avoid local resource exhaustion
- Provider-specific optimizations

### UI Performance
- Lazy loading for conversation history
- Virtual scrolling for long lists
- Debounced search queries
- Optimized re-renders with Reflex state management

### RAG Pipeline
- Context window optimization
- Chunk deduplication
- Relevance threshold filtering
- Extended timeouts for reasoning models (180s for GPT-5-mini)

## Scalability Considerations

### Current Capacity
- 500+ concurrent users (Reflex vs 50 with Streamlit)
- ~1,000 chunks indexed (expandable to 100,000+)
- Sub-second vector search queries
- 25-35s end-to-end RAG response time

### Future Scaling
- Horizontal scaling with Docker orchestration
- Database sharding for larger corpora
- CDN integration for static assets
- Read replicas for Neo4j and Weaviate

## Security

- Environment-based secrets management
- API key rotation support
- Input validation and sanitization
- HTTPS enforcement in production
- CORS configuration for web interface

## Monitoring & Observability

- Prometheus metrics collection
- Grafana dashboards
- Structured logging throughout application
- Error tracking and alerting
- Performance profiling

---

**Last Updated**: 2025-11-05
**Related**: [Conventions](.claude/conventions.md), [Deployment](.claude/deployment.md)
