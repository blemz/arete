# Classical Texts PDF Processing

This directory is for storing your classical philosophy PDF files that will be processed by the Arete system.

## Quick Start

1. **Place your PDFs here:**
   - `republic.pdf` - Plato's Republic
   - `nicomachean_ethics.pdf` - Aristotle's Nicomachean Ethics  
   - `socratic_dialogues.pdf` - Plato's Socratic Dialogues

2. **Process the PDFs using the existing Phase 2 pipeline:**
   ```bash
   python process_classical_texts.py "data/pdfs/Plato The Republic (Cambridge, Tom Griffith) Clean.pdf"
   python process_classical_texts.py "data/pdfs/Aristotle's Nicomachean Ethics.pdf"
   python process_classical_texts.py "data/pdfs/Socratis Dialogues.pdf"
   ```

3. **The script demonstrates:**
   - PDF text extraction using existing PDFExtractor
   - Document model creation with proper metadata
   - Intelligent chunking using ChunkingStrategy  
   - Knowledge graph extraction with run_kg_extraction()
   - Embedding generation using EmbeddingService
   - Database serialization preparation

## Supported Formats

The system automatically recognizes common classical texts:
- Files containing "republic" → The Republic by Plato
- Files containing "ethics" or "nicomachean" → Nicomachean Ethics by Aristotle
- Files containing "dialogue" or "socratic" → Socratic Dialogues by Plato

## Next Steps

Once processed, these documents will be:
1. Extracted for text content
2. Chunked for optimal retrieval
3. Embedded using SOTA models
4. Stored in Neo4j knowledge graph
5. Available for the document viewer
6. Searchable through the RAG pipeline
7. Accessible in the chat interface with proper citations

## Technical Details

The processing uses the existing Phase 2 data ingestion pipeline (97% complete):
- PDF extraction with PyMuPDF
- Intelligent text chunking
- Entity and relationship extraction
- Embedding generation
- Dual database storage (Neo4j + Weaviate)
- Citation network building

## File Naming Suggestions

For best automatic recognition:
- `plato_republic.pdf`
- `aristotle_nicomachean_ethics.pdf` 
- `plato_socratic_dialogues.pdf`
- `republic_translation_jowett.pdf`
- `ethics_aristotle_ross_translation.pdf`