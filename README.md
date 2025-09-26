# Arete: AI Philosophy Tutor with Graph-RAG

> *"Excellence is never an accident. It is always the result of high intention, sincere effort, and intelligent execution"* - Aristotle

**Arete** is a production-ready AI tutoring system for classical philosophical texts, combining Neo4j knowledge graphs, Weaviate vector search, and multi-provider LLM support to deliver accurate, well-cited philosophical education.

## 🚀 Current Status: Phase 8.1 Complete

### ✅ **FULLY OPERATIONAL** - Three Working Interfaces:
1. **Modern Reflex Web Interface** - Complete RAG integration with real philosophical responses
2. **Production RAG CLI** - GPT-5-mini powered with citations from actual texts
3. **Legacy Streamlit Interface** - Original UI still available

### 📊 Live System Capabilities:
- **227 semantic chunks** from Plato's Apology & Charmides
- **83 philosophical entities** with 109 relationships
- **74-82% relevance scores** in vector search
- **Real-time citations** with position tracking
- **Multi-provider support** for LLMs and embeddings

---

## 📦 Installation

### Prerequisites
- Python 3.11+ (tested with 3.12.8)
- Docker Desktop 4.0+ (for database services)
- 8GB RAM minimum
- API Keys (optional but recommended for best performance)

### Step 1: Clone and Setup Environment

```bash
# Clone repository
git clone https://github.com/arete-ai/arete.git
cd arete

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure API Keys (Recommended)

Create a `.env` file in the project root:

```bash
# For best performance with OpenAI
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=your_openai_key_here
SELECTED_LLM_PROVIDER=openai
SELECTED_LLM_MODEL=gpt-5-mini

# Alternative: OpenRouter (cost-effective)
# EMBEDDING_PROVIDER=openrouter
# OPENROUTER_API_KEY=your_openrouter_key_here
# SELECTED_LLM_PROVIDER=openrouter
# SELECTED_LLM_MODEL=openai/gpt-4o-mini

# Alternative: Local Ollama (no API keys needed)
# EMBEDDING_PROVIDER=sentence_transformers
# SELECTED_LLM_PROVIDER=ollama
# SELECTED_LLM_MODEL=llama3.2
```

### Step 3: Start Database Services

```bash
# Start Neo4j and Weaviate
docker-compose up -d neo4j weaviate

# Verify services are running
docker-compose ps

# Services should be available at:
# Neo4j Browser: http://localhost:7474 (user: neo4j, password: password)
# Weaviate: http://localhost:8080
```

### Step 4: Quick Test

```bash
# Test the production RAG CLI immediately
python chat_rag_clean.py "What is virtue?"

# You should see a detailed philosophical response with citations
```

---

## 🎯 Usage Guide

### Option 1: Modern Reflex Web Interface (Recommended)

The Reflex interface provides a modern, responsive web experience with real RAG integration.

```bash
# Navigate to Reflex app directory
cd src/arete/ui/reflex_app

# Install Reflex dependencies (first time only)
pip install reflex

# Start the Reflex web server
reflex run

# Open browser to http://localhost:3000
```

**Features:**
- Split-view layout with chat and document viewer
- Interactive citation previews with hover tooltips
- Document library with "Read" buttons for texts
- Real-time RAG responses with GPT-5-mini
- Graph analytics dashboard
- Mobile-responsive design

### Option 2: Production RAG CLI

Perfect for quick philosophical queries and testing.

```bash
# Single query mode
python chat_rag_clean.py "What is Socrates being accused of?"

# Interactive mode
python chat_rag_clean.py
>>> What is the relationship between knowledge and virtue?
>>> How does Charmides define temperance?
>>> exit
```

**Example Output:**
```
Question: What is virtue?
Answer: According to the philosophical texts, virtue (arete in Greek) represents
excellence of character and the fulfillment of one's potential. In the Charmides,
temperance (sophrosyne) is explored as a key virtue involving self-knowledge...

Citations:
[1] Charmides, Position 146.0 (82.3% relevance): "Temperance is self-knowledge..."
[2] Apology, Position 23.5 (78.1% relevance): "The unexamined life is not worth living..."
```

### Option 3: Legacy Interfaces

```bash
# Streamlit UI (original interface)
streamlit run src/arete/ui/streamlit_app.py
# Open http://localhost:8501

# Fast CLI (mock responses for testing)
python chat_fast.py "What is justice?"
```

---

## 🔧 Configuration

### Environment Variables

All configuration is managed through the `.env` file:

```bash
# LLM Provider Options
SELECTED_LLM_PROVIDER=openai|openrouter|gemini|anthropic|ollama
SELECTED_LLM_MODEL=gpt-5-mini|gpt-4o-mini|claude-3-opus|llama3.2

# Embedding Provider Options
EMBEDDING_PROVIDER=openai|openrouter|gemini|anthropic|sentence_transformers|ollama
EMBEDDING_MODEL=text-embedding-3-small|all-MiniLM-L6-v2

# Database Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
WEAVIATE_URL=http://localhost:8080

# Performance Tuning
MAX_TOKENS=4000
TEMPERATURE=0.7
TIMEOUT_SECONDS=180
```

### Provider-Specific Setup

#### OpenAI (Recommended for quality)
```bash
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...
SELECTED_LLM_MODEL=gpt-5-mini  # Best reasoning
```

#### Ollama (Free, local)
```bash
# Install Ollama first: https://ollama.ai
ollama pull llama3.2
ollama pull nomic-embed-text

EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
SELECTED_LLM_PROVIDER=ollama
SELECTED_LLM_MODEL=llama3.2
```

#### OpenRouter (Cost-effective)
```bash
EMBEDDING_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-...
SELECTED_LLM_MODEL=openai/gpt-4o-mini
```

---

## 📚 Features

### Core Capabilities

#### 🎓 Philosophical Expertise
- **Classical Texts**: Plato's Apology & Charmides (more coming)
- **Accurate Citations**: Every response backed by source text
- **Greek Terms**: Proper handling of philosophical terminology
- **Conceptual Relationships**: Knowledge graph of philosophical concepts

#### 🔍 Advanced RAG System
- **Hybrid Search**: Vector similarity + knowledge graph traversal
- **Entity Recognition**: 83 philosophical entities mapped
- **Relationship Extraction**: 109 conceptual relationships
- **Relevance Scoring**: 74-82% accuracy on queries

#### 💻 Multiple Interfaces
- **Modern Web**: Reflex-based responsive interface
- **Production CLI**: Fast command-line access
- **API Access**: Programmatic integration options

#### 🔄 Multi-Provider Support
- **LLM Providers**: OpenAI, Anthropic, Google, Ollama, OpenRouter
- **Embedding Services**: Multiple vector embedding options
- **Automatic Fallbacks**: Graceful degradation when services unavailable
- **Cost Optimization**: Intelligent provider selection

### Advanced Features

#### Graph Analytics
- Centrality analysis of philosophical concepts
- Community detection in idea networks
- Historical development tracking
- Cross-dialogue concept mapping

#### Quality Assurance
- Hallucination detection
- Citation verification
- Multi-model consensus validation
- Expert review integration

---

## 🧪 Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_database/ -v        # Database tests
pytest tests/test_rag/ -v            # RAG pipeline tests
pytest tests/test_ui/ -v             # UI tests

# Check test coverage
pytest --cov=src/arete --cov-report=html
```

### Project Structure

```
arete/
├── src/
│   └── arete/
│       ├── database/         # Neo4j, Weaviate clients
│       ├── rag/             # RAG pipeline components
│       ├── llm/             # Multi-provider LLM services
│       ├── embeddings/      # Embedding services
│       ├── ui/              # User interfaces
│       │   ├── reflex_app/ # Modern web interface
│       │   └── streamlit/   # Legacy interface
│       └── utils/           # Shared utilities
├── data/
│   └── restructured_ai/     # Processed philosophical texts
├── tests/                   # Test suite
├── docker-compose.yml       # Database services
├── chat_rag_clean.py       # Production RAG CLI
├── chat_fast.py            # Quick test CLI
└── .env                    # Configuration
```

### Adding New Texts

```bash
# Ingest a new philosophical text
python ingest_restructured_text.py \
    --file data/restructured_ai/plato_republic.txt \
    --author "Plato" \
    --title "Republic"

# Verify ingestion
python verify_database_content.py
```

---

## 🐛 Troubleshooting

### Common Issues

#### Docker not starting
```bash
# Windows: Make sure Docker Desktop is running
# Check Docker status
docker version

# If services won't start
docker-compose down
docker-compose up -d --force-recreate
```

#### API Key errors
```bash
# Verify .env file exists and has correct format
cat .env

# Test API key directly
python -c "import openai; openai.api_key='your_key'; print('OK')"
```

#### Slow responses
```bash
# Increase timeout in .env
TIMEOUT_SECONDS=300

# Use faster model
SELECTED_LLM_MODEL=gpt-4o-mini  # Faster than gpt-5-mini
```

#### Memory issues
```bash
# Use cloud embeddings instead of local
EMBEDDING_PROVIDER=openai  # Instead of sentence_transformers

# Reduce batch size
EMBEDDING_BATCH_SIZE=50
```

### Getting Help

1. Check the [FAQ](docs/faq.md)
2. Search [existing issues](https://github.com/arete-ai/arete/issues)
3. Join our [Discord community](https://discord.gg/arete-ai)
4. Create a [new issue](https://github.com/arete-ai/arete/issues/new)

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run the test suite (`pytest tests/`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Priority Areas
- 📚 Adding more philosophical texts
- 🌍 Multi-language support
- 🎨 UI/UX improvements
- 🧪 Test coverage expansion
- 📖 Documentation improvements

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Perseus Digital Library** - Classical text digitization
- **Stanford Encyclopedia of Philosophy** - Philosophical expertise
- **Open Source Community** - Amazing tools and libraries

---

## 📞 Support

- 📧 Email: support@arete.ai
- 💬 Discord: [Arete Community](https://discord.gg/arete-ai)
- 🐛 Issues: [GitHub Issues](https://github.com/arete-ai/arete/issues)
- 📖 Docs: [Documentation](docs/)

---

*"The unexamined life is not worth living." - Socrates*

**Built with ❤️ for philosophical inquiry and educational excellence.**