# Arete - Graph-RAG AI Tutoring System

## Overview

**Arete** is a Graph-RAG (Retrieval-Augmented Generation) AI tutoring system for classical philosophical texts. It combines Neo4j knowledge graphs, Weaviate vector embeddings, and multi-provider LLM support to deliver accurate, well-cited philosophical education.

## Quick Start

### Launch the Application

**Modern Web Interface** (Recommended):
```bash
cd src/arete/ui/reflex_app
reflex run
```

**Production RAG CLI**:
```bash
python chat_rag_clean.py "What is virtue?"
```

**Legacy CLI** (Mock responses only):
```bash
python chat_fast.py "What is virtue?"
```

### System Requirements

- Python 3.10+
- Neo4j database
- Weaviate vector database
- Redis (optional, for caching)
- OpenAI API key (or other LLM provider)

### Environment Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure `.env` with database credentials and API keys
4. Run database migrations (if applicable)
5. Launch the application (see commands above)

## Current Status

**Phase**: 8.5 - UI Redesign (Classical Aesthetic + Knowledge Chat Template)
**System Status**: Production Ready
**Last Updated**: 2025-10-04

### Active Development

Currently implementing classical philosophical aesthetic with:
- Classical color palette (Deep Navy Blue, Warm Gold, Cream Parchment)
- Enhanced typography (Cinzel, EB Garamond, GFS Didot)
- Knowledge-chat template architecture
- Conversation history and citation panels

See [planning/todo.md](../planning/todo.md) for detailed sprint plan.

### Content Status

**Currently Ingested**:
- Plato's Apology + Charmides
- 51,383 words
- 227 semantic chunks
- 83 philosophical entities
- 109 relationships

**Ready for Ingestion**:
- Plato's Republic (AI-restructured, 1.56MB, 15,242 lines)
- Expected: ~800-1000 additional chunks

## Common Commands

### Development
```bash
# Run tests
pytest

# Run specific test file
pytest tests/test_name.py

# Run with coverage
pytest --cov=src/arete

# Lint code
ruff check .

# Format code
black .
```

### Database Operations
```bash
# Verify database content
python quick_verify.py

# Ingest new content
python ingest_restructured_text.py path/to/text.md

# Reset databases (caution!)
python scripts/reset_databases.py
```

### Git Workflow
```bash
# Standard workflow
git status
git add .
git commit -m "feat: description"
git push

# Create new branch
git checkout -b feature-name
```

## Project Structure

```
arete/
├── .claude/              # Project documentation
├── planning/             # Sprint plans and design specs
├── src/arete/            # Main application code
│   ├── database/         # Database clients
│   ├── models/           # Pydantic models
│   ├── services/         # Business logic
│   ├── rag/              # RAG pipeline
│   ├── ui/               # Reflex web interface
│   └── ...
├── tests/                # Test suites
├── content/              # Classical texts
└── .memory/              # Knowledge base memories

```

## Key Features

- **Hybrid RAG Pipeline**: Combines sparse (BM25/SPLADE), dense (vector embeddings), and graph-based retrieval
- **Multi-Provider LLM**: Support for OpenAI, Anthropic, Gemini, OpenRouter, Ollama
- **Knowledge Graph**: Neo4j-based entity relationships and philosophical concept mapping
- **Citation System**: Accurate source tracking with relevance scores and position tracking
- **Modern UI**: Reflex-based web interface with responsive design and accessibility compliance
- **Production Ready**: Docker deployment, comprehensive testing, monitoring stack

## Documentation

- [Architecture & Design](.claude/architecture.md) - System design, tech stack, database schemas
- [Coding Conventions](.claude/conventions.md) - TDD methodology, development principles
- [Deployment](.claude/deployment.md) - Deployment procedures, environment configuration
- [Troubleshooting](.claude/troubleshooting.md) - Common issues, phase history

### Domain-Specific Docs

- [Database Documentation](../src/arete/database/DATABASE.md)
- [Models Documentation](../src/arete/models/MODELS.md)
- [Services Documentation](../src/arete/services/SERVICES.md)
- [RAG Pipeline Documentation](../src/arete/rag/RAG.md)

## Development Routines

**Start-Day Routine**:
1. Read project context (CLAUDE.md, planning/todo.md, .memory/)
2. Review current sprint status
3. Check for any blockers or dependencies

**End-Day Routine**:
1. Update project documentation
2. Commit changes with descriptive messages
3. Update sprint TODO if progress made

## Getting Help

- Check [Troubleshooting Guide](.claude/troubleshooting.md) for common issues
- Review [Architecture Documentation](.claude/architecture.md) for system design questions
- See [Conventions Guide](.claude/conventions.md) for development best practices

## License

[Add license information]

---

**Last Updated**: 2025-11-05
**Contributors**: [Add contributor list]
