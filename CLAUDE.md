# Arete Project Guide

## Quick Links

### Core Documentation
- [Overview & Quick Start](.claude/README.md) - Getting started, launch commands, project structure
- [Architecture & Design](.claude/architecture.md) - System design, tech stack, completed phases
- [Coding Conventions](.claude/conventions.md) - TDD methodology, code standards, best practices
- [Deployment Procedures](.claude/deployment.md) - Environment setup, Docker, database configuration
- [Troubleshooting](.claude/troubleshooting.md) - Common issues, debugging, memory system

### Module Documentation
- [Database Module](src/arete/database/DATABASE.md) - Neo4j, Weaviate, Redis clients and patterns
- [Models Module](src/arete/models/MODELS.md) - Pydantic models, validation, schemas
- [Services Module](src/arete/services/SERVICES.md) - Business logic, service patterns, testing
- [RAG Pipeline](src/arete/rag/RAG.md) - Retrieval-augmented generation, hybrid retrieval, optimization

## Current Sprint: Phase 8.5 UI Redesign

**Status**: Sprint 1 Phase 1 Complete ✅
**Branch**: `aesthetics`
**Next**: Sprint 2 - Conversation History Sidebar

### What's Complete
- ✅ Classical color palette integrated (Deep Navy #2C3E50, Warm Gold #D4A574, Cream Parchment #E8DCC8)
- ✅ Typography system (Cinzel, EB Garamond, GFS Didot)
- ✅ ThemeService with WCAG validation
- ✅ Updated tailwind.config.js and global.css
- ✅ 70+ tests, 100% pass rate
- ✅ WCAG AA compliance verified

### Next Tasks
See [planning/todo.md](planning/todo.md) for detailed Sprint 2-4 plan:
- Sprint 2 (5-6h): Chat architecture with conversation history and citation panels
- Sprint 3 (4-5h): Layout components with classical aesthetics
- Sprint 4 (4-5h): Advanced features (unified search, smart summaries)

## System Status

**Production Ready** 🚀

**Launch Options**:
```bash
# Modern Web Interface (Recommended)
cd src/arete/ui/reflex_app && reflex run

# Production RAG CLI
python chat_rag_clean.py "What is virtue?"

# Legacy CLI (Mock responses only)
python chat_fast.py "What is virtue?"
```

**Content**:
- Ingested: Apology + Charmides (227 chunks, 83 entities, 109 relationships)
- Ready: Republic AI-restructured (1.56MB, 15,242 lines)

## Common Commands

```bash
# Development
pytest                              # Run all tests
reflex run                          # Launch web interface
python chat_rag_clean.py "query"    # RAG CLI

# Code Quality
ruff check .                        # Lint code
black .                             # Format code
mypy src/arete                      # Type check

# Database
python quick_verify.py              # Verify database content
python ingest_restructured_text.py  # Ingest new texts

# Git
git status                          # Check status
git add . && git commit -m "msg"    # Commit changes
```

## Development Workflow

### Test-Driven Development (TDD)
**MANDATORY** for all development:
1. **Red**: Write failing test for new feature
2. **Green**: Write minimum code to pass test
3. **Refactor**: Improve code while keeping tests green

See [Conventions Guide](.claude/conventions.md) for complete TDD methodology.

### Daily Routines
- **Start-Day**: Read CLAUDE.md, planning/todo.md, check sprint status
- **End-Day**: Update documentation, commit changes, update TODO

## Key Technical Decisions

- **TDD Methodology**: Strict Red-Green-Refactor, >90% coverage required
- **Hybrid Architecture**: Neo4j + Weaviate + Redis for optimal performance
- **Multi-Provider LLM**: OpenAI, Anthropic, Gemini, OpenRouter, Ollama
- **Repository Pattern**: Clean data access separation across all components
- **Type Safety**: Comprehensive type hints and Pydantic validation

## Project Principles

1. **Clarity of Purpose**: Always aim for clear, maintainable, production-ready code
2. **No Test Compromise**: Never simplify tests to pass - fix the underlying code
3. **Test Quality**: Meaningful tests aligned with real-world use cases
4. **Feature Policy**: Every feature includes implementation + tests, committed together
5. **Educational Focus**: Pedagogical value prioritized, all responses citation-backed

## Documentation Benefits

This restructured documentation provides:
- **Reduced Token Usage**: Load only relevant context for your task
- **Faster Responses**: Less irrelevant information to process
- **Better Focus**: Domain-specific docs keep work on-track
- **Easier Maintenance**: Update specific sections without affecting everything

Navigate to specialized docs above for detailed information on each area.

---

**Last Updated**: 2025-11-05
**Current Phase**: 8.5 UI Redesign - Classical Aesthetic + Knowledge Chat Template
**System**: Production ready with full RAG integration
**Next Priority**: Sprint 2 (Conversation History Sidebar) → Republic Ingestion → Code Quality Fixes
