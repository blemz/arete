# Arete Graph-RAG Architecture Analysis

## Overview
Arete is a production-ready Graph-RAG system for classical philosophical texts, combining Neo4j knowledge graphs, Weaviate vector embeddings, and multi-provider LLM support. Here's the architecture breakdown for your AI K5-K9 Tutor project:

---

## 🏗️ Core Architecture (3-Tier Design)

### 1. **Configuration Layer** (`src/arete/config.py`)
- **Pydantic Settings** with `.env` integration
- Multi-provider API key management (OpenAI, OpenRouter, Gemini, Anthropic, Ollama)
- Dedicated KG extraction LLM configuration (`KG_LLM_PROVIDER`, `KG_LLM_MODEL`)
- Embedding provider selection (sentence-transformers, Ollama, OpenAI, etc.)
- RAG parameters (chunk size, retrieval limits, similarity thresholds)

### 2. **Database Layer**
#### **Neo4j Client** (`src/arete/database/client.py`)
- Async/sync support with context managers
- Model-aware operations (Document, Entity, Chunk)
- Batch operations for performance
- Retry logic with exponential backoff
- Health checks and connection pooling

#### **Weaviate Client** (`src/arete/database/weaviate_client.py`)
- Modern Weaviate v4+ API
- Vector similarity search
- Batch document/entity storage
- GraphQL-based retrieval

### 3. **Service Layer** (Business Logic)
#### **RAG Pipeline Service** (`src/arete/services/rag_pipeline_service.py`)
- **7-stage pipeline**: query processing → retrieval → re-ranking → diversification → context composition → response generation → validation
- Hybrid retrieval (dense + sparse + graph traversal)
- Configurable weights and thresholds
- Performance metrics tracking

#### **Embedding Services** (`src/arete/services/embedding_factory.py`)
- **Provider factory pattern** with 6 providers:
  - OpenAI (text-embedding-3-small, 1536d)
  - Gemini (text-embedding-004, 768d)
  - Ollama (local models)
  - OpenRouter, Anthropic, sentence-transformers
- Batch processing and caching

#### **LLM Services** (`src/arete/services/simple_llm_service.py`)
- **Multi-provider support**: OpenAI, Anthropic, Gemini, OpenRouter, Ollama
- Environment-based provider selection
- Async response generation
- Health monitoring and fallback systems

---

## 📦 Data Models (Pydantic + SQLAlchemy)

Located in `src/arete/models/`:
- **Document**: Title, author, content, metadata, processing status
- **Chunk**: Semantic text chunks with position tracking and embeddings
- **Entity**: Philosophical concepts with types (PERSON, CONCEPT, WORK, PLACE)
- **Citation**: Source references with preview and relevance scores

All models have:
- UUID primary keys
- `to_neo4j_dict()` / `to_weaviate_dict()` methods
- Timestamp tracking
- Type-safe validation

---

## 🔄 Data Ingestion Pipeline

**Script**: `ingest_restructured_text.py` (1,542 lines)

### Features:
1. **Auto-format detection** (PDF → Markdown conversion)
2. **LLM Graph Transformer** integration for entity/relationship extraction
3. **Semantic chunking** (preserves argument structure)
4. **Embedding generation** in batches
5. **Dual storage** (Neo4j + Weaviate) with transaction support

### Pipeline Steps:
```python
1. File conversion (PDF → Markdown)
2. Metadata extraction
3. Semantic chunking (AI-structured sections)
4. Entity extraction (LLM + regex hybrid)
5. Relationship extraction (causal chains, NLP patterns)
6. Embedding generation (batch processing)
7. Database storage (Neo4j graph + Weaviate vectors)
```

### Key Classes:
- `RestructuredTextParser`: Extracts entities/relationships from philosophical texts
- `LLMGraphTransformerService`: Uses LangChain for advanced extraction

---

## 🔍 RAG Query Flow

**Entry Point**: `chat_rag_clean.py`

```python
1. User Query → Query Embedding
2. Vector Search (Weaviate) → Top-K chunks
3. Entity Matching (Neo4j) → Related concepts
4. Context Assembly → LLM Prompt
5. Response Generation (with citations)
6. Citation Cleanup → User Display
```

**Key Services**:
- `DenseRetrievalService`: Semantic vector search
- `GraphTraversalService`: Neo4j relationship traversal
- `ContextCompositionService`: Intelligent prompt building
- `ResponseGenerationService`: LLM integration with validation

---

## 🎯 Reusable Components for Your K5-K9 Tutor

### **Must-Have Components**:

1. **Configuration System**
```python
from arete.config import Settings, get_settings
settings = get_settings()  # Auto-loads from .env
```

2. **Database Clients**
```python
from arete.database.client import Neo4jClient
from arete.database.weaviate_client import WeaviateClient

# Async/sync support with context managers
async with Neo4jClient() as neo4j:
    await neo4j.async_save_document(doc)
```

3. **Embedding Factory**
```python
from arete.services.embedding_factory import get_embedding_service

# Auto-selects provider from env
embeddings_service = get_embedding_service()
vectors = await embeddings_service.generate_embeddings(texts)
```

4. **LLM Service**
```python
from arete.services.simple_llm_service import get_llm_service

llm = get_llm_service()
response = await llm.generate_response(
    messages=[{"role": "user", "content": query}],
    provider="openai",  # or auto from env
    model="gpt-4o-mini"
)
```

5. **RAG Pipeline**
```python
from arete.services.rag_pipeline_service import RAGPipelineService

pipeline = RAGPipelineService(
    dense_retrieval_service=...,
    context_composition_service=...,
    response_generation_service=...
)
result = await pipeline.execute_pipeline(query)
```

6. **Ingestion Pipeline**
```python
from ingest_restructured_text import ingest_restructured_text, store_in_databases

# Process educational content
result = await ingest_restructured_text("path/to/k5_science.pdf")
await store_in_databases(result)
```

---

## 📝 Environment Configuration (.env)

**Critical Variables**:
```bash
# Databases
NEO4J_URI=bolt://localhost:7687
WEAVIATE_URL=http://localhost:8080

# LLM Selection
SELECTED_LLM_PROVIDER=openai
SELECTED_LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...

# Embeddings
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small

# Knowledge Graph Extraction (dedicated LLM)
KG_LLM_PROVIDER=openai
KG_LLM_MODEL=gpt-4o-mini

# RAG Parameters
CHUNK_SIZE=2048
CHUNK_OVERLAP=512
TOP_K_PASSAGES=5
```

---

## 🚀 Adaptation Strategy for K5-K9 Tutor

### **1. Content Ingestion**
- **Reuse**: `ingest_restructured_text.py` with PDF support
- **Modify**: Entity types for educational content (TOPIC, SKILL, STANDARD, CONCEPT)
- **Add**: Grade-level metadata and curriculum alignment

### **2. Knowledge Graph Schema**
- **Reuse**: Neo4j client and entity/relationship models
- **Modify**: Add nodes for (Student, Lesson, Standard, Skill)
- **Add**: Relationships like PREREQUISITE, TEACHES, ASSESSES

### **3. RAG Retrieval**
- **Reuse**: Hybrid retrieval (vector + graph)
- **Modify**: Grade-level filtering in vector search
- **Add**: Difficulty-based re-ranking

### **4. Response Generation**
- **Reuse**: LLM service with multi-provider support
- **Modify**: Age-appropriate prompt templates
- **Add**: Readability scoring and simplification

### **5. Models to Copy**
```
src/arete/models/document.py  → educational_content.py
src/arete/models/entity.py    → concept.py
src/arete/models/chunk.py     → lesson_chunk.py
src/arete/config.py           → tutor_config.py
```

---

## 📊 Architecture Diagram (Text)

```
┌──────────────────────────────────────────────────┐
│              User Interface Layer                │
│  (Reflex Web App / CLI / API Endpoints)          │
└───────────────────┬──────────────────────────────┘
                    │
┌───────────────────▼──────────────────────────────┐
│              RAG Pipeline Service                │
│  Query → Retrieval → Rerank → Compose → LLM     │
└───┬───────────────┬──────────────────┬───────────┘
    │               │                  │
┌───▼───┐      ┌────▼────┐      ┌─────▼─────┐
│Neo4j  │      │Weaviate │      │LLM Service│
│(Graph)│      │(Vectors)│      │Multi-Prov │
└───┬───┘      └────┬────┘      └─────┬─────┘
    │               │                  │
┌───▼───────────────▼──────────────────▼───────┐
│          Data Ingestion Pipeline             │
│  PDF→MD → Chunk → Embed → Store (Dual DB)   │
└──────────────────────────────────────────────┘
```

---

## 🎓 Key Learnings for Your Project

1. **Separation of Concerns**: Config → Models → Services → Repositories
2. **Multi-Provider Design**: Never lock into single LLM/embedding provider
3. **Batch Operations**: Essential for production ingestion performance
4. **Dual Storage**: Graph (relationships) + Vector (similarity) = superior retrieval
5. **Type Safety**: Pydantic models catch errors early
6. **Async-First**: All I/O operations support async for scalability

---

## 📁 File Structure Reference

```
arete/
├── src/arete/
│   ├── config.py                    # Central configuration with Pydantic
│   ├── database/
│   │   ├── client.py                # Neo4j client (async/sync)
│   │   └── weaviate_client.py       # Weaviate client (v4+ API)
│   ├── models/
│   │   ├── document.py              # Document model
│   │   ├── chunk.py                 # Chunk model with embeddings
│   │   ├── entity.py                # Entity model (concepts, people)
│   │   └── citation.py              # Citation tracking
│   ├── services/
│   │   ├── rag_pipeline_service.py  # Main RAG orchestrator
│   │   ├── embedding_factory.py     # Multi-provider embeddings
│   │   ├── simple_llm_service.py    # LLM provider abstraction
│   │   ├── dense_retrieval_service.py
│   │   ├── context_composition_service.py
│   │   └── response_generation_service.py
│   ├── repositories/                # Data access layer
│   │   ├── document.py
│   │   ├── entity.py
│   │   └── retrieval.py
│   └── processing/
│       └── extractors.py            # PDF/text extraction
├── ingest_restructured_text.py      # Main ingestion script
├── chat_rag_clean.py                # RAG CLI interface
├── .env.example                     # Configuration template
└── docker-compose.yml               # Neo4j + Weaviate setup
```

---

## 🔧 Quick Start for New Project

### **1. Copy Core Infrastructure**
```bash
# Essential files to copy
cp -r src/arete/config.py new_project/
cp -r src/arete/database/ new_project/
cp -r src/arete/models/ new_project/
cp -r src/arete/services/embedding_factory.py new_project/
cp -r src/arete/services/simple_llm_service.py new_project/
cp .env.example new_project/.env
cp docker-compose.yml new_project/
```

### **2. Modify for Education Domain**
```python
# In models/entity.py
class EntityType(str, Enum):
    TOPIC = "topic"           # Math topic, Science concept
    SKILL = "skill"           # Reading skill, Math operation
    STANDARD = "standard"     # Common Core standard
    LEARNING_OBJECTIVE = "learning_objective"
    ASSESSMENT = "assessment"
```

### **3. Customize Ingestion**
```python
# In ingest_educational_content.py
def create_educational_chunks(text: str, grade_level: int) -> List[Chunk]:
    """Create grade-appropriate semantic chunks."""
    chunks = semantic_chunker.chunk(text)
    for chunk in chunks:
        chunk.metadata['grade_level'] = grade_level
        chunk.metadata['readability_score'] = calculate_readability(chunk.text)
    return chunks
```

### **4. Add Grade-Level Filtering**
```python
# In rag_pipeline_service.py
async def retrieve_for_grade(self, query: str, grade_level: int):
    """Retrieve content appropriate for student grade level."""
    where_filter = {
        "path": ["metadata", "grade_level"],
        "operator": "Equal",
        "valueInt": grade_level
    }
    return await self.weaviate_client.search_by_vector(
        collection_name="Chunk",
        query_vector=query_embedding,
        where_filter=where_filter
    )
```

---

## 📚 Additional Resources

### **Key Dependencies**
```toml
# pyproject.toml
[tool.poetry.dependencies]
python = "^3.11"
neo4j = "^5.23.0"
weaviate-client = "^4.9.0"
pydantic = "^2.9.2"
pydantic-settings = "^2.6.1"
openai = "^1.51.2"
anthropic = "^0.39.0"
google-generativeai = "^0.8.3"
sentence-transformers = "^3.2.1"
langchain = "^0.3.7"
pymupdf4llm = "^0.0.17"
reflex = "^0.6.4"
```

### **Database Setup**
```bash
# Start databases
docker-compose up -d neo4j weaviate

# Access Neo4j Browser
http://localhost:7474
Username: neo4j
Password: password

# Weaviate endpoint
http://localhost:8080
```

### **Testing RAG Pipeline**
```bash
# CLI test
python chat_rag_clean.py "What is virtue?"

# Web interface
cd src/arete/ui/reflex_app && reflex run
```

---

## 🎯 Migration Checklist for K5-K9 Tutor

- [ ] Copy database clients (Neo4j + Weaviate)
- [ ] Adapt configuration system for education domain
- [ ] Modify data models (Entity types, metadata fields)
- [ ] Update ingestion pipeline for curriculum content
- [ ] Add grade-level filtering to retrieval
- [ ] Customize prompt templates for age groups
- [ ] Implement readability scoring
- [ ] Add progress tracking models
- [ ] Create student profile management
- [ ] Build curriculum alignment mapping
- [ ] Test with sample K5-K9 content

---

**Created**: 2025-10-04
**Purpose**: Architecture documentation for adapting Arete Graph-RAG system to AI K5-K9 Tutor project
**Status**: Complete analysis with reusable components identified
