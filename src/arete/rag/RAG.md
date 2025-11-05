# RAG Pipeline Documentation

## Overview

The RAG (Retrieval-Augmented Generation) pipeline is the core of Arete's question-answering system. It combines hybrid retrieval strategies with knowledge graph integration and LLM generation to produce accurate, well-cited philosophical responses.

## Pipeline Architecture

```
User Question
     │
     ▼
┌────────────────────┐
│ Query Processing   │ - Embedding generation
│                    │ - Query expansion
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Hybrid Retrieval   │ - Vector similarity (Weaviate)
│                    │ - Entity matching (Neo4j)
│                    │ - Sparse retrieval (optional)
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Context Assembly   │ - Chunk deduplication
│                    │ - Relevance filtering
│                    │ - Context ranking
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ LLM Generation     │ - Prompt construction
│                    │ - Response generation
│                    │ - Citation extraction
└────────┬───────────┘
         │
         ▼
    Final Answer
    with Citations
```

## Core Components

### Query Processor

**Purpose**: Transform user questions into embeddings and expanded queries.

**File**: `rag/query_processor.py`

**Responsibilities**:
- Clean and normalize questions
- Generate query embeddings
- Expand queries with synonyms
- Extract key concepts

**Key Methods**:
```python
class QueryProcessor:
    """Process user queries for retrieval."""

    def __init__(self, embedding_service: EmbeddingService):
        self.embeddings = embedding_service

    def process_query(self, question: str) -> ProcessedQuery:
        """Process question into structured query.

        Args:
            question: Raw user question

        Returns:
            ProcessedQuery with embedding and metadata
        """
        # Clean question
        cleaned = self.clean_text(question)

        # Generate embedding
        embedding = self.embeddings.embed_text(cleaned)

        # Extract concepts
        concepts = self.extract_concepts(cleaned)

        return ProcessedQuery(
            original=question,
            cleaned=cleaned,
            embedding=embedding,
            concepts=concepts
        )
```

**Usage**:
```python
from arete.rag import QueryProcessor

processor = QueryProcessor(embedding_service)

# Process question
query = processor.process_query("What is Socrates' view on virtue?")

print(f"Cleaned: {query.cleaned}")
print(f"Concepts: {query.concepts}")  # ['socrates', 'virtue']
print(f"Embedding dim: {len(query.embedding)}")
```

### Hybrid Retriever

**Purpose**: Retrieve relevant chunks using multiple strategies.

**File**: `rag/hybrid_retriever.py`

**Responsibilities**:
- Vector similarity search (dense)
- Entity-based retrieval (graph)
- BM25/SPLADE retrieval (sparse, optional)
- Result fusion and ranking

**Key Methods**:
```python
class HybridRetriever:
    """Hybrid retrieval combining multiple strategies."""

    def __init__(
        self,
        chunk_repository: ChunkRepository,
        entity_repository: EntityRepository,
        use_sparse: bool = False
    ):
        self.chunk_repo = chunk_repository
        self.entity_repo = entity_repository
        self.use_sparse = use_sparse

    async def retrieve(
        self,
        query: ProcessedQuery,
        max_results: int = 10,
        min_score: float = 0.7
    ) -> List[RetrievalResult]:
        """Retrieve relevant chunks using hybrid strategy.

        Args:
            query: Processed query with embedding
            max_results: Maximum results to return
            min_score: Minimum relevance threshold

        Returns:
            List of RetrievalResult objects ranked by relevance
        """
        # 1. Dense retrieval (vector similarity)
        dense_results = await self.dense_retrieval(
            query.embedding,
            limit=max_results * 2
        )

        # 2. Graph retrieval (entity matching)
        graph_results = await self.graph_retrieval(
            query.concepts,
            limit=max_results
        )

        # 3. Sparse retrieval (optional BM25)
        sparse_results = []
        if self.use_sparse:
            sparse_results = await self.sparse_retrieval(
                query.cleaned,
                limit=max_results
            )

        # 4. Fuse results
        fused = self.fuse_results(
            dense_results,
            graph_results,
            sparse_results
        )

        # 5. Filter and rank
        filtered = [r for r in fused if r.score >= min_score]
        ranked = sorted(filtered, key=lambda r: r.score, reverse=True)

        return ranked[:max_results]
```

**Retrieval Strategies**:

**Dense Retrieval (Vector Similarity)**:
```python
async def dense_retrieval(
    self,
    embedding: List[float],
    limit: int
) -> List[RetrievalResult]:
    """Retrieve using vector similarity."""
    chunks = await self.chunk_repo.search_by_similarity(
        embedding=embedding,
        limit=limit
    )
    return [
        RetrievalResult(
            chunk=chunk,
            score=chunk.similarity_score,
            source="dense"
        )
        for chunk in chunks
    ]
```

**Graph Retrieval (Entity Matching)**:
```python
async def graph_retrieval(
    self,
    concepts: List[str],
    limit: int
) -> List[RetrievalResult]:
    """Retrieve chunks via entity relationships."""
    # Find entities matching concepts
    entities = []
    for concept in concepts:
        found = await self.entity_repo.search_by_name(concept)
        entities.extend(found)

    # Get chunks discussing these entities
    chunks = []
    for entity in entities:
        related = await self.chunk_repo.find_by_entity(entity.id)
        chunks.extend(related)

    # Deduplicate and score
    unique_chunks = self.deduplicate(chunks)
    return [
        RetrievalResult(
            chunk=chunk,
            score=self.calculate_entity_score(chunk, entities),
            source="graph"
        )
        for chunk in unique_chunks[:limit]
    ]
```

**Result Fusion**:
```python
def fuse_results(
    self,
    dense: List[RetrievalResult],
    graph: List[RetrievalResult],
    sparse: List[RetrievalResult]
) -> List[RetrievalResult]:
    """Fuse results from multiple strategies.

    Uses Reciprocal Rank Fusion (RRF) algorithm.
    """
    # Combine all results
    all_results = {}

    # Add dense results (weight: 0.5)
    for rank, result in enumerate(dense, 1):
        chunk_id = result.chunk.id
        rrf_score = 0.5 / (60 + rank)
        if chunk_id in all_results:
            all_results[chunk_id].score += rrf_score
        else:
            result.score = rrf_score
            all_results[chunk_id] = result

    # Add graph results (weight: 0.3)
    for rank, result in enumerate(graph, 1):
        chunk_id = result.chunk.id
        rrf_score = 0.3 / (60 + rank)
        if chunk_id in all_results:
            all_results[chunk_id].score += rrf_score
        else:
            result.score = rrf_score
            all_results[chunk_id] = result

    # Add sparse results (weight: 0.2)
    for rank, result in enumerate(sparse, 1):
        chunk_id = result.chunk.id
        rrf_score = 0.2 / (60 + rank)
        if chunk_id in all_results:
            all_results[chunk_id].score += rrf_score
        else:
            result.score = rrf_score
            all_results[chunk_id] = result

    return list(all_results.values())
```

### Context Assembler

**Purpose**: Assemble retrieved chunks into coherent context for LLM.

**File**: `rag/context_assembler.py`

**Responsibilities**:
- Deduplicate chunks
- Rank by relevance
- Format citations
- Manage context window size

**Key Methods**:
```python
class ContextAssembler:
    """Assemble context from retrieved chunks."""

    def assemble_context(
        self,
        results: List[RetrievalResult],
        max_tokens: int = 4000
    ) -> AssembledContext:
        """Assemble context from retrieval results.

        Args:
            results: Retrieved chunks with scores
            max_tokens: Maximum context tokens

        Returns:
            AssembledContext with formatted text and citations
        """
        # Deduplicate
        unique = self.deduplicate_results(results)

        # Sort by relevance
        ranked = sorted(unique, key=lambda r: r.score, reverse=True)

        # Build context within token limit
        context_chunks = []
        total_tokens = 0

        for result in ranked:
            chunk_tokens = self.count_tokens(result.chunk.content)
            if total_tokens + chunk_tokens <= max_tokens:
                context_chunks.append(result)
                total_tokens += chunk_tokens
            else:
                break

        # Format context
        formatted_text = self.format_context(context_chunks)

        # Build citations
        citations = self.build_citations(context_chunks)

        return AssembledContext(
            text=formatted_text,
            citations=citations,
            chunks_used=len(context_chunks),
            total_tokens=total_tokens
        )
```

**Context Formatting**:
```python
def format_context(self, chunks: List[RetrievalResult]) -> str:
    """Format chunks into context text."""
    sections = []

    for i, result in enumerate(chunks, 1):
        chunk = result.chunk
        metadata = chunk.metadata

        section = f"""
[Source {i}]
Dialogue: {metadata.get('dialogue', 'Unknown')}
Position: {chunk.position:.2f}
Relevance: {result.score:.2f}

{chunk.content}

---
"""
        sections.append(section)

    return "\n".join(sections)
```

### Response Generator

**Purpose**: Generate final response using LLM with assembled context.

**File**: `rag/response_generator.py`

**Responsibilities**:
- Construct prompts with context
- Call LLM API
- Extract and format citations
- Handle errors and fallbacks

**Key Methods**:
```python
class ResponseGenerator:
    """Generate responses using LLM."""

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    async def generate_response(
        self,
        question: str,
        context: AssembledContext
    ) -> GeneratedResponse:
        """Generate response with LLM.

        Args:
            question: User question
            context: Assembled context from retrieval

        Returns:
            GeneratedResponse with answer and citations
        """
        # Build prompt
        prompt = self.build_prompt(question, context)

        # Generate response
        try:
            answer = await self.llm.generate(
                prompt=prompt,
                max_tokens=2000,
                temperature=0.7
            )
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            answer = self.fallback_response(question, context)

        # Extract citations
        citations = self.extract_citations(answer, context.citations)

        return GeneratedResponse(
            answer=answer,
            citations=citations,
            context_used=context.chunks_used,
            tokens_used=context.total_tokens
        )
```

**Prompt Construction**:
```python
def build_prompt(self, question: str, context: AssembledContext) -> str:
    """Build LLM prompt with question and context."""
    system_prompt = """You are a knowledgeable tutor of classical philosophy,
specializing in Plato, Aristotle, and Socratic dialogues. Answer questions
accurately based on the provided source texts. Always cite your sources."""

    user_prompt = f"""
Question: {question}

Context from classical texts:
{context.text}

Instructions:
1. Answer the question based ONLY on the provided context
2. Cite specific sources using [Source N] references
3. Include Greek terms with transliterations when relevant
4. If the context doesn't contain enough information, say so
5. Provide complete philosophical arguments, not summaries

Answer:"""

    return f"{system_prompt}\n\n{user_prompt}"
```

## Production CLI: chat_rag_clean.py

**Purpose**: Production-ready CLI interface for RAG pipeline.

**Key Features**:
- Complete RAG pipeline integration
- GPT-5-mini reasoning model support
- Extended timeout handling (180s)
- Citation extraction and display
- Unicode handling for Greek terms

**Usage**:
```bash
# Single question
python chat_rag_clean.py "What is virtue according to Plato?"

# Interactive mode
python chat_rag_clean.py
```

**Pipeline Flow**:
```python
async def process_query(question: str) -> dict:
    """Process question through RAG pipeline."""
    # 1. Query processing
    query = query_processor.process_query(question)

    # 2. Hybrid retrieval
    results = await retriever.retrieve(
        query,
        max_results=10,
        min_score=0.7
    )

    # 3. Context assembly
    context = assembler.assemble_context(
        results,
        max_tokens=4000
    )

    # 4. Response generation
    response = await generator.generate_response(
        question,
        context
    )

    return {
        "answer": response.answer,
        "citations": response.citations,
        "chunks_used": response.context_used,
        "relevance_scores": [r.score for r in results]
    }
```

## Performance Optimization

### Caching

```python
from functools import lru_cache
import redis

# Memory cache for embeddings
@lru_cache(maxsize=1000)
def get_cached_embedding(text: str) -> List[float]:
    """Cache embeddings in memory."""
    return embedding_service.embed_text(text)

# Redis cache for queries
def cached_query(question: str) -> Optional[dict]:
    """Cache full RAG responses in Redis."""
    redis_client = RedisClient()
    cache_key = f"rag:query:{hash(question)}"

    # Check cache
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Execute query
    result = process_query(question)

    # Cache for 1 hour
    redis_client.set(cache_key, json.dumps(result), ex=3600)

    return result
```

### Batch Processing

```python
async def process_multiple_queries(questions: List[str]) -> List[dict]:
    """Process multiple questions in parallel."""
    # Generate embeddings in batch
    embeddings = embedding_service.embed_batch(questions)

    # Process queries concurrently
    tasks = [
        process_query_with_embedding(q, e)
        for q, e in zip(questions, embeddings)
    ]

    results = await asyncio.gather(*tasks)
    return results
```

### Context Window Management

```python
def optimize_context_window(
    chunks: List[RetrievalResult],
    max_tokens: int,
    min_chunks: int = 3
) -> List[RetrievalResult]:
    """Optimize context to fit token budget."""
    selected = []
    total_tokens = 0

    # Sort by relevance
    sorted_chunks = sorted(chunks, key=lambda r: r.score, reverse=True)

    # Add chunks until budget exhausted
    for chunk in sorted_chunks:
        chunk_tokens = count_tokens(chunk.content)

        if total_tokens + chunk_tokens <= max_tokens:
            selected.append(chunk)
            total_tokens += chunk_tokens
        elif len(selected) < min_chunks:
            # Truncate chunk to fit
            truncated = truncate_to_tokens(chunk.content, max_tokens - total_tokens)
            chunk.chunk.content = truncated
            selected.append(chunk)
            break

    return selected
```

## Error Handling

### Graceful Degradation

```python
async def robust_rag_pipeline(question: str) -> dict:
    """RAG pipeline with fallback strategies."""
    try:
        # Try full RAG pipeline
        return await process_query(question)

    except VectorSearchError as e:
        logger.warning(f"Vector search failed: {e}")
        # Fall back to entity-only retrieval
        return await process_query_graph_only(question)

    except LLMError as e:
        logger.error(f"LLM generation failed: {e}")
        # Return context without LLM generation
        return {
            "answer": "Unable to generate response. Here are relevant passages:",
            "citations": context.citations,
            "error": str(e)
        }

    except Exception as e:
        logger.error(f"RAG pipeline failed: {e}", exc_info=True)
        # Generic fallback
        return {
            "answer": "I encountered an error processing your question.",
            "error": str(e)
        }
```

## Testing

### Pipeline Testing

```python
import pytest
from arete.rag import RAGPipeline

@pytest.mark.asyncio
async def test_rag_pipeline_end_to_end():
    """Test complete RAG pipeline."""
    pipeline = RAGPipeline()

    result = await pipeline.process_query("What is virtue?")

    assert "answer" in result
    assert len(result["citations"]) > 0
    assert result["chunks_used"] > 0
    assert all(score > 0.7 for score in result["relevance_scores"])

@pytest.mark.asyncio
async def test_rag_pipeline_handles_no_results():
    """Test pipeline when no relevant chunks found."""
    pipeline = RAGPipeline()

    result = await pipeline.process_query("Who won the 2024 World Series?")

    assert "answer" in result
    assert "no relevant" in result["answer"].lower()
```

---

**Related Documentation**:
- [Services Documentation](../services/SERVICES.md)
- [Database Documentation](../database/DATABASE.md)
- [Architecture Overview](../../../.claude/architecture.md)
- [Troubleshooting](../../../.claude/troubleshooting.md)
