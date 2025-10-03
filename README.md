# Arete: AI Philosophy Tutor with Graph-RAG

> *"Excellence is never an accident. It is always the result of high intention, sincere effort, and intelligent execution"* - Aristotle

**Arete** is a production-ready Graph-RAG AI tutoring system for classical philosophical texts. It combines Neo4j knowledge graphs, Weaviate vector embeddings, and multi-provider LLM support to deliver accurate, well-cited philosophical education.

## ✨ What Makes Arete Special

- **📚 Real Citations**: Every answer backed by exact passages from ingested texts with relevance scores
- **🧠 Knowledge Graph**: Neo4j stores 83+ philosophical entities and 109+ relationships
- **🔍 Hybrid Search**: Vector similarity + graph traversal for comprehensive retrieval
- **🎨 Modern UI**: Fast Reflex web interface with thinking indicators and structured responses
- **🌐 Multi-Provider**: Works with OpenAI, OpenRouter, Gemini, Anthropic, or local Ollama
- **⚡ Production-Ready**: Complete with WebSocket reconnection, error handling, and monitoring

## 📋 Current Content

**Ingested Texts** (Ready to query):
- ✅ Plato's **Apology** - Socrates' defense trial
- ✅ Plato's **Charmides** - Dialogue on temperance and self-knowledge
- 📊 **Total**: 51,383 words → 227 semantic chunks → 83 entities → 109 relationships

**Ready for Ingestion**:
- 📚 Plato's **Republic** (1.56MB, 15,242 lines, AI-restructured with GraphRAG optimization)
- Expected: ~800-1000 new chunks, ~400-500 entities

**Technology Stack**:
- 🧠 **LLMs**: OpenAI GPT-5-mini, OpenRouter, Gemini, Anthropic, Ollama
- 📈 **Knowledge Graph**: Neo4j with entity relationships and Cypher queries
- 🔗 **Vector Store**: Weaviate with 1536d embeddings (OpenAI text-embedding-3-small)
- 🎨 **Web UI**: Reflex framework (50-90% faster than Streamlit)
- 🐍 **Backend**: Async Python with Pydantic validation

## 🚀 Getting Started (Step-by-Step)

### Step 1: Install Prerequisites

**Required**:
- Python 3.11+ ([Download](https://www.python.org/downloads/))
- Docker Desktop ([Download](https://www.docker.com/products/docker-desktop/))
- 8GB RAM minimum

**Recommended** (for best performance):
- OpenAI API key ([Get one](https://platform.openai.com/api-keys)) - Best quality
- OR OpenRouter API key ([Get one](https://openrouter.ai/)) - Cost-effective, multiple models
- OR Google Gemini API key ([Get one](https://makersuite.google.com/app/apikey)) - Free tier available

**Alternative** (100% free, no API keys):
- Ollama installed ([Install](https://ollama.ai/)) - Runs models locally

---

### Step 2: Clone and Install

```bash
# Clone repository
git clone https://github.com/arete-ai/arete.git
cd arete

# Install Python dependencies (choose one)
uv pip install -r requirements.txt  # Using UV (faster, recommended)
# OR
pip install -r requirements.txt     # Using pip
```

---

### Step 3: Configure API Keys

```bash
# Create configuration file
cp .env.example .env

# Edit .env file and add your API key (choose one option below)
```

**Option A - OpenAI** (Best quality, recommended):
```bash
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key-here
SELECTED_LLM_PROVIDER=openai
SELECTED_LLM_MODEL=gpt-4o-mini
KG_LLM_PROVIDER=openai
KG_LLM_MODEL=gpt-4o-mini
```

**Option B - OpenRouter** (Cost-effective, many models):
```bash
EMBEDDING_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-your-openrouter-key-here
SELECTED_LLM_PROVIDER=openrouter
SELECTED_LLM_MODEL=x-ai/grok-4-fast:free
KG_LLM_PROVIDER=openrouter
KG_LLM_MODEL=x-ai/grok-4-fast:free
```

**Option C - Local Ollama** (100% free, no API keys):
```bash
EMBEDDING_PROVIDER=ollama
SELECTED_LLM_PROVIDER=ollama
SELECTED_LLM_MODEL=gemma3:12b-it-qat
KG_LLM_PROVIDER=ollama
KG_LLM_MODEL=gemma3:12b-it-qat

# Then run: ollama pull gemma3:12b-it-qat
```

---

### Step 4: Start Databases

```bash
# Start Neo4j and Weaviate using Docker
docker-compose up -d neo4j weaviate

# Verify services are running (wait ~30 seconds)
docker-compose ps
# Should show: neo4j (healthy), weaviate (healthy)
```

**Access Points** (verify databases are working):
- Neo4j Browser: http://localhost:7474 (username: `neo4j`, password: `password`)
- Weaviate API: http://localhost:8080

---

### Step 5: Ingest Content (Optional but Recommended)

```bash
# Ingest AI-restructured Republic (takes ~15-30 minutes)
python ingest_restructured_text.py "data/processed/Plato The Republic (Cambridge, Tom Griffith) Clean_ai_restructured.md"

# The system will:
# ✓ Parse metadata and create document record
# ✓ Create ~800-1000 semantic chunks
# ✓ Extract ~400-500 philosophical entities (Forms, Justice, etc.)
# ✓ Generate embeddings using your configured provider
# ✓ Store in Neo4j (graph) and Weaviate (vectors)
# ✓ Display progress and final statistics

# Verify ingestion (optional)
python quick_verify.py
# Should show: ~1000-1227 chunks, ~483-583 entities
```

---

### Step 6: Use Arete!

**Option A - Command-Line Interface** (Fastest):
```bash
# Ask philosophical questions with real citations
python chat_rag_clean.py "What is virtue?"
python chat_rag_clean.py "What is Socrates accused of in the Apology?"
python chat_rag_clean.py "Explain the Allegory of the Cave"

# Interactive mode
python chat_rag_clean.py
# Then type your questions
```

**Option B - Modern Web Interface** (Best experience):
```bash
# Navigate to Reflex app
cd src/arete/ui/reflex_app

# Start web server (takes ~30 seconds first time)
reflex run

# Open browser to: http://localhost:3000
# Features:
# - Chat with thinking indicator ("🏛️ Arete is thinking ● ● ●")
# - Structured responses with citations
# - Document viewer for reading source texts
# - Analytics dashboard with knowledge graph visualization
```

---

### Step 7: Verify Everything Works

**Test RAG Pipeline**:
```bash
python chat_rag_clean.py "What is temperance according to Charmides?"
# Should return: Answer with citations from Plato's Charmides dialogue
```

**Test Web Interface**:
1. Open http://localhost:3000
2. Type: "What is justice?"
3. Wait for "🏛️ Arete is thinking ● ● ●"
4. View structured response with citations

**Check Databases**:
```bash
python quick_verify.py
# Should show healthy database connections and content statistics
```

---

## 📚 Advanced Usage

### Adding Your Own Texts

```bash
# 1. Convert PDF to markdown (if needed)
python -m src.arete.processing.philosophical_converter \
  --input "data/raw/your_text.pdf" \
  --output "data/processed"

# 2. AI-restructure for GraphRAG (optional but recommended)
python restructure_enhanced_text.py \
  "data/processed/your_text_enhanced.md"

# 3. Ingest into system
python ingest_restructured_text.py \
  "data/processed/your_text_ai_restructured.md"
```

### Database Maintenance

```bash
# Verify database health and content
python quick_verify.py

# Check detailed statistics
python verify_databases.py

# Clear all data (reset)
python clear_databases.py

# Check Weaviate collections
python check_weaviate_data.py
```

### Testing Without Databases

```bash
# Fast mock mode (no database required)
python chat_fast.py "What is virtue?"
# Returns philosophical concepts without RAG pipeline
```

---

## 🧪 Development

**Run Tests**:
```bash
pytest tests/ -v --cov=src/arete --cov-report=html
```

**Test Methodology**: Contract-based TDD focusing on quality over quantity
- See `tests/CLAUDE.md` for complete methodology
- 98%+ reduction in test code while maintaining >90% coverage
- 80%+ faster execution times vs exhaustive testing

---

## 📊 Project Status

**Current Phase**: 8.4 In Progress - Organizational Milestone Complete

**Completed** ✅:
- Modern Reflex web interface with full RAG integration
- Production CLI with GPT-5-mini reasoning models
- Multi-provider LLM and embedding services
- Content ingestion pipeline with AI restructuring
- Republic text prepared (1.56MB, ready for ingestion)
- Portuguese presentation materials complete

**Next Priority** 🚀:
- Ingest Republic (~800-1000 chunks, ~400-500 entities)
- Code quality improvements (138 linting warnings remaining)
- Performance testing with expanded corpus

See [CLAUDE.md](CLAUDE.md) for complete development history and [TODO.md](TODO.md) for detailed roadmap.

---

## 🤝 Contributing

Contributions welcome from philosophers, developers, and educators!

**Quick Start**:
1. Fork the repository
2. Check [GitHub Issues](https://github.com/arete-ai/arete/issues)
3. Follow contract-based TDD methodology (see `tests/CLAUDE.md`)
4. Submit pull request with tests

**Development Process**: Contract-based TDD, code review, expert philosophical validation

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Perseus Digital Library** - Digitized classical texts
- **Stanford Encyclopedia of Philosophy** - Philosophical expertise
- **Open Source Community** - Amazing tools and frameworks

---

*"The unexamined life is not worth living." - Socrates*

**Built with ❤️ for philosophical inquiry and educational excellence.**