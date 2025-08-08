Below is an end-to-end blueprint you can use to build a Graph-RAG system whose primary role is to act as an AI study-companion / tutor for classical philosophical texts (Plato, Aristotle, Kant, Śaṅkara, Nāgārjuna, etc.).
The design is distilled from the most recent open-source implementations and research prototypes (Plato² , VedantaNY-10M , KG-RAG AI-Tutor ).
----
1.  Architecture at a Glance
----
┌────────────────────────┐
│  Ingest & Pre-process  │  (PDFs, TEI-XML, Markdown)
└────────┬───────────────┘
         ▼
┌────────────────────────┐
│ Knowledge Graph Builder│  Neo4j / Memgraph
│  • Entities: Person,   │  Concepts: “Substance”, “Ātman”
│  • Relations: criticizes, sublates │
└────────┬───────────────┘
         ▼
┌────────────────────────┐
│ Dual-Index Retriever   │  Weaviate / Qdrant (dense)
│  • Dense (embeddings)  │  • Sparse (BM25 or SPLADE)
│  • Graph traversal     │  (Cypher queries)
└────────┬───────────────┘
         ▼
┌────────────────────────┐
│ Context Composer       │  LangChain / LlamaIndex
│  • Re-rank + prune     │  • Passage-window stitching
└────────┬───────────────┘
         ▼
┌────────────────────────┐
│ LLM Generator          │  Local: Ollama (OpenHermes-2.5)
│  • System prompt:      │  “You are a philosophy tutor…”
│  • Citation injection  │  (source text + line numbers)
└────────┬───────────────┘
         ▼
┌────────────────────────┐
│ Chat / Notebook UI     │  Streamlit / Gradio
└────────────────────────┘

----
2.  Tech Stack & Why
----
Layer	Library / Service	Rationale
Graph DB	Neo4j (community) or Memgraph	Mature Cypher, excellent visual browser, proven in Plato² [^2^]
Vector DB	Weaviate or Qdrant	Open-source, hybrid dense-sparse, easy Docker deployment
LLM serving	Ollama (GPU)	Runs quantized 8–34 B models locally, zero external calls [^2^]
RAG glue	LangChain + LlamaIndex	Standard pipelines, flexible retriever/chain abstractions
Embedding	`sentence-transformers/all-mpnet-base-v2`	Balanced size vs. quality, supports long contexts
NLP utilities	spaCy + `transformers`	Fast sentence-split, coreference, multilingual NER for Greek/Sanskrit
Front-end	Streamlit	30-line chat UI, can embed collapsible primary-text panes
----
3.  Data Ingestion Pipeline
----
1.  Text extraction
Use pymupdf4llm or marker-pdf to convert scanned PDF → Markdown with page anchors.
TEI-XML sources (Perseus, GRETIL) are parsed directly into Document objects.
2.  Chunking
•  1 000-token windows with 200-token overlap.
•  Preserve structural metadata: Book / Chapter / Stephanus page / verse number.
•  Store in LlamaIndex nodes with metadata={"source":"Republic_473c"}.
3.  Knowledge-graph extraction
•  Prompt Qwen-2.5-7B with few-shot examples:
From the passage, extract triples in [Entity1, Relation, Entity2] format.
Example: [Socrates, refutes, Thrasymachus]

•  Output → CSV → LOAD CSV into Neo4j.
•  Expert validation step as in  (philology PhD corrects 5 % of edges).
----
4.  Dual-Retriever Design
----
•  Dense index
•  Each chunk embedded with all-mpnet-base-v2.
•  Stored in Weaviate class Passage with property stephanus_page.
•  Sparse index
•  Use SPLADE for philosophy-specific terms (“ἀρετή”, “nirvikalpa”).
•  Weighted hybrid score:
S = 0.7 * dense_sim + 0.3 * sparse_sim (mirrors VedantaNY-10M ).
•  Graph traversal
•  When user query mentions an entity (e.g., “Plato’s critique of poetry”),
run Cypher:
MATCH (p:Person {name:"Plato"})-[r:CRITIQUES]->(c:Concept)
RETURN c.name, r.quote

•  Merge retrieved triples with top-k passages from vector DB.
----
5.  Context Composer (RAG Chain)
----
LangChain template:
template = """
You are a philosophy tutor. Use ONLY the passages below to answer.
Cite Stephanus or verse numbers inline.

{context}

Question: {question}
Answer:
"""

•  Insert up to 5 000 tokens of ranked context.
•  If context > 5 000 tokens, use Map-Rerank to select best 3 chunks.
----
6.  Evaluation & Human-in-the-Loop
----
•  Automatic:
•  Faithfulness & citation-precision via ALCE metrics .
•  Graph accuracy: % of triples confirmed by domain expert.
•  Human:
•  Weekly sessions with philosophy grad students rating usefulness 1-5.
•  Use feedback to fine-tune retrieval weights λ and prompt instructions.
----
7.  Deployment Recipe (Docker-Compose)
----
services:
  neo4j:
    image: neo4j:5-community
    ports: ["7474:7474", "7687:7687"]
    environment: [NEO4J_AUTH=neo4j/password]
  weaviate:
    image: semitechnologies/weaviate:latest
    ports: ["8080:8080"]
  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    volumes: ["./models:/root/.ollama"]

Front-end: streamlit run app.py mounts the same Docker network.
----
8.  Extending Beyond English
----
•  Sanskrit / Greek:
•  Swap embedding model to greek-bert or indic-bert.
•  Add language tag in metadata; filter in retriever.
•  Multimodal:
•  Link diagrams (e.g., Aristotelian square of opposition) in Neo4j as :Image nodes, store CLIP embedding in Weaviate.
----
9.  Starter GitHub Skeleton
----
graph-philosophy-tutor/
├── data/
│   ├── raw_pdfs/
│   └── tei_xml/
├── pipelines/
│   ├── ingest.py
│   └── extract_triples.py
├── graph/
│   └── schema.cypher
├── rag/
│   ├── dense_retriever.py
│   └── chain.py
├── ui/
│   └── streamlit_app.py
└── docker-compose.yml

Clone, docker compose up, ingest one dialogue (≈ 15 min on CPU), start chatting.
----
Key References
•  Plato² implementation (Neo4j + Ollama + LangChain) 
•  VedantaNY-10M hybrid retrieval tricks 
•  KG-RAG AI-Tutor validation workflow
