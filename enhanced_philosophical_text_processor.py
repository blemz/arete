#!/usr/bin/env python3
"""
Enhanced Philosophical Text Processing with PyMuPDF4LLM

Complete pipeline: PDF → Enhanced Markdown → Heading-Aware Chunking → Structural GraphRAG → Storage

This enhanced approach provides:
1. PyMuPDF4LLM for superior PDF → Markdown conversion  
2. YAML front-matter for rich philosophical metadata
3. Heading-aware chunking that respects argument structure
4. Structural GraphRAG (headings → nodes, cross-references → edges)
5. Human-in-the-loop quality enhancement opportunity

Usage:
    pip install -U pymupdf4llm pyyaml
    python enhanced_philosophical_text_processor.py "path/to/philosophical_text.pdf"
"""

import sys
import asyncio
import subprocess
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arete.processing.philosophical_converter import (
    PhilosophicalConverter, 
    PhilosophicalMetadata,
    PhilosophicalPeriod,
    TextType
)
from arete.processing.chunker import ChunkingStrategy
from arete.services.enhanced_kg_service import EnhancedKnowledgeGraphService
from arete.services.embedding_factory import get_embedding_service
from arete.models.document import Document, ProcessingStatus


async def enhanced_philosophical_processing(pdf_path: str, output_dir: str = "enhanced_philosophical_texts"):
    """
    Complete enhanced philosophical text processing pipeline.
    
    Flow:
    1. PyMuPDF4LLM: PDF → Enhanced Markdown with structure preservation
    2. YAML Front-matter: Rich philosophical metadata
    3. Human Review: Optional quality enhancement step
    4. Heading-Aware Chunking: Respect philosophical argument boundaries  
    5. Structural GraphRAG: Headings → nodes, references → edges
    6. Enhanced Knowledge Graph: Philosophical entities and relationships
    7. Superior Embeddings: From clean, structured text
    8. Production Storage: Ready for RAG queries
    """
    
    print("🏛️ Enhanced Philosophical Text Processing Pipeline")
    print("=" * 80)
    print(f"Processing: {Path(pdf_path).name}")
    print("Features:")
    print("  ✓ PyMuPDF4LLM superior PDF conversion")
    print("  ✓ YAML front-matter metadata")
    print("  ✓ Heading-aware chunking")
    print("  ✓ Structural GraphRAG preparation")
    print("  ✓ Enhanced knowledge graph extraction")
    print("  ✓ Production-ready storage")
    print()
    
    # Stage 1: Enhanced PDF → Markdown Conversion
    print("=== Stage 1: PyMuPDF4LLM PDF → Enhanced Markdown ===")
    
    converter = PhilosophicalConverter()
    
    # Create rich metadata for better processing
    sample_metadata = PhilosophicalMetadata(
        title=Path(pdf_path).stem,
        author="Classical Philosopher",
        philosophical_period=PhilosophicalPeriod.ANCIENT,
        text_type=TextType.TREATISE,
        major_themes=["virtue", "justice", "soul", "forms"],
        key_concepts=["wisdom", "courage", "temperance", "piety"],
        citation_style="classical"
    )
    
    try:
        markdown_file, metadata = await converter.convert_pdf_to_enhanced_markdown(
            pdf_path, 
            output_dir,
            sample_metadata
        )
        print(f"✅ Enhanced markdown created: {markdown_file}")
        
    except ImportError as e:
        print(f"❌ PyMuPDF4LLM not installed: {e}")
        print("Install with: pip install -U pymupdf4llm")
        return None
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return None
    
    # Stage 2: Human Review Option
    print(f"\n=== Stage 2: Human Review Opportunity ===")
    print(f"📝 Enhanced markdown available at: {markdown_file}")
    print(f"💡 Optional: Review and enhance the markdown for optimal RAG results:")
    print(f"   1. Fix any OCR errors")
    print(f"   2. Add philosophical structure markers")
    print(f"   3. Clean up citations (Republic 514a format)")  
    print(f"   4. Mark key relationships and cross-references")
    print(f"   5. Add semantic annotations")
    
    proceed = input(f"\nProceed with processing? (y/n): ")
    if proceed.lower() != 'y':
        print("⏸️ Processing paused for human review.")
        print(f"📁 Enhanced markdown saved at: {markdown_file}")
        return markdown_file
    
    # Stage 3: Read enhanced markdown
    print(f"\n=== Stage 3: Processing Enhanced Markdown ===")
    
    with open(markdown_file, 'r', encoding='utf-8') as f:
        enhanced_text = f.read()
    
    print(f"📖 Processing enhanced text: {len(enhanced_text):,} characters")
    
    # Stage 4: Heading-Aware Chunking 
    print(f"\n=== Stage 4: Heading-Aware Chunking ===")
    
    # Use heading-aware chunking for philosophical structure preservation
    chunker = ChunkingStrategy.get_chunker("heading_aware", max_chunk_size=2000)
    
    # Create document from enhanced markdown
    document = Document(
        title=metadata.title,
        author=metadata.author,
        content=enhanced_text,
        language=f"{metadata.original_language} ({metadata.translation_language})",
        source="Enhanced Philosophical Text",
        processing_status=ProcessingStatus.PROCESSING,
        word_count=len(enhanced_text.split())
    )
    
    # Create heading-aware chunks
    chunks = chunker.chunk_text(enhanced_text, document.id)
    
    print(f"✅ Created {len(chunks)} heading-aware chunks")
    print(f"   Average chunk size: {sum(len(c.text) for c in chunks) / len(chunks):.0f} characters")
    
    # Show chunk structure
    structural_chunks = [c for c in chunks if c.metadata and c.metadata.get('structural_type') == 'heading_aware']
    if structural_chunks:
        print(f"   Structural chunks: {len(structural_chunks)}")
        print(f"   Sample headings:")
        for chunk in structural_chunks[:3]:
            if chunk.metadata and 'heading_title' in chunk.metadata:
                level = chunk.metadata.get('heading_level', 1)
                title = chunk.metadata['heading_title']
                print(f"     {'  ' * (level-1)}{'#' * level} {title}")
    
    # Stage 5: Enhanced Knowledge Graph Extraction
    print(f"\n=== Stage 5: Enhanced Knowledge Graph Extraction ===")
    
    try:
        kg_service = EnhancedKnowledgeGraphService()
        
        print(f"Extracting philosophical entities and relationships...")
        entities, relationships = await kg_service.extract_knowledge_graph(
            text=enhanced_text,
            document_id=str(document.id),
            chunk_size=2000,
            max_chunks=None  # Process all chunks
        )
        
        print(f"✅ Enhanced extraction results:")
        print(f"   Entities: {len(entities)}")
        print(f"   Relationships: {len(relationships)}")
        
        # Show sample entities
        if entities:
            print(f"   Sample entities:")
            for entity in entities[:5]:
                entity_type = entity.entity_type.value if hasattr(entity.entity_type, 'value') else str(entity.entity_type)
                print(f"     • {entity.name} ({entity_type}) - confidence: {entity.confidence:.2f}")
        
    except Exception as e:
        print(f"⚠️ Knowledge graph extraction failed: {e}")
        entities, relationships = [], []
    
    # Stage 6: Structural Graph Elements
    print(f"\n=== Stage 6: Structural GraphRAG Elements ===")
    
    structural_elements = converter.get_structural_elements()
    cross_references = converter.get_cross_references()
    
    print(f"✅ Structural analysis complete:")
    print(f"   Structural elements: {len(structural_elements)} (headings → nodes)")
    print(f"   Cross-references: {len(cross_references)} (references → edges)")
    
    # Show structural hierarchy
    if structural_elements:
        print(f"   Document structure preview:")
        for element in structural_elements[:5]:
            indent = "  " * (element.level - 1)
            role_info = f" [{element.philosophical_role}]" if element.philosophical_role else ""
            print(f"     {indent}• {element.title}{role_info}")
    
    # Stage 7: Enhanced Embeddings Generation
    print(f"\n=== Stage 7: Enhanced Embeddings Generation ===")
    
    try:
        embedding_service = get_embedding_service()
        
        print(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings_generated = 0
        
        # Generate embeddings for all chunks
        if hasattr(embedding_service, 'generate_embeddings_batch'):
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = embedding_service.generate_embeddings_batch(chunk_texts)
            
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding_vector = embedding
                embeddings_generated += 1
        else:
            # Fallback: individual generation
            for chunk in chunks:
                embedding = embedding_service.generate_embedding(chunk.text)
                chunk.embedding_vector = embedding
                embeddings_generated += 1
        
        print(f"✅ Generated embeddings: {embeddings_generated}/{len(chunks)} chunks")
        
        if chunks and chunks[0].embedding_vector:
            embedding_dim = len(chunks[0].embedding_vector)
            print(f"   Embedding dimensions: {embedding_dim}")
            
    except Exception as e:
        print(f"⚠️ Embedding generation failed: {e}")
    
    # Stage 8: Production-Ready Results Summary
    print(f"\n=== Stage 8: Processing Complete - Production Ready ===")
    
    results = {
        'document': document,
        'enhanced_markdown': markdown_file,
        'metadata': metadata,
        'chunks': chunks,
        'structural_elements': structural_elements,
        'cross_references': cross_references,
        'entities': entities,
        'relationships': relationships,
        'processing_summary': {
            'original_pdf': pdf_path,
            'enhanced_markdown': markdown_file,
            'total_chunks': len(chunks),
            'heading_aware_chunks': len([c for c in chunks if c.chunk_type.value == 'heading_aware']),
            'structural_elements': len(structural_elements),
            'entities_extracted': len(entities),
            'relationships_found': len(relationships),
            'embeddings_generated': embeddings_generated,
            'cross_references': len(cross_references)
        }
    }
    
    print(f"🎉 Enhanced philosophical text processing complete!")
    print(f"")
    print(f"📊 Processing Summary:")
    print(f"   📄 Original PDF: {Path(pdf_path).name}")
    print(f"   📝 Enhanced Markdown: {Path(markdown_file).name}")
    print(f"   🧩 Heading-aware chunks: {len(chunks)}")
    print(f"   🏗️ Structural elements: {len(structural_elements)}")
    print(f"   🧠 Entities extracted: {len(entities)}")
    print(f"   🔗 Relationships: {len(relationships)}")
    print(f"   📐 Embeddings: {embeddings_generated}")
    print(f"   🔍 Cross-references: {len(cross_references)}")
    print(f"")
    print(f"🚀 Ready for:")
    print(f"   ✓ Production database storage")
    print(f"   ✓ RAG pipeline queries")
    print(f"   ✓ Scholarly citation responses")
    print(f"   ✓ Structural graph traversal")
    print(f"")
    print(f"🎯 Next Steps:")
    print(f"   1. Store in databases: python process_full_classical_texts.py")
    print(f"   2. Test RAG queries: streamlit run src/arete/ui/streamlit_app.py")
    print(f"   3. Query with philosophical questions for cited responses")
    
    return results


def main():
    """Process enhanced philosophical texts with complete pipeline."""
    
    if len(sys.argv) != 2:
        print("Enhanced Philosophical Text Processing Pipeline")
        print("=" * 50)
        print()
        print("Usage: python enhanced_philosophical_text_processor.py <path_to_pdf>")
        print()
        print("Features:")
        print("• PyMuPDF4LLM superior PDF conversion")  
        print("• YAML front-matter metadata")
        print("• Heading-aware chunking")
        print("• Structural GraphRAG preparation")
        print("• Enhanced knowledge extraction")
        print("• Production-ready processing")
        print()
        print("Examples:")
        print('  python enhanced_philosophical_text_processor.py "data/pdfs/Plato_Republic.pdf"')
        print('  python enhanced_philosophical_text_processor.py "data/pdfs/Aristotle_Ethics.pdf"')
        return
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"❌ ERROR: File not found: {pdf_path}")
        return
    
    # Check for PyMuPDF4LLM dependency
    try:
        import pymupdf4llm
    except ImportError:
        print("❌ PyMuPDF4LLM not found. Installing...")
        print("Running: pip install -U pymupdf4llm")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-U", "pymupdf4llm"], check=True)
            print("✅ PyMuPDF4LLM installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install PyMuPDF4LLM. Please install manually:")
            print("   pip install -U pymupdf4llm")
            return
    
    # Run enhanced processing
    result = asyncio.run(enhanced_philosophical_processing(pdf_path))
    
    if result:
        print(f"\n✨ Enhanced philosophical text processing completed successfully!")
        print(f"📁 Results saved to: enhanced_philosophical_texts/")


if __name__ == "__main__":
    main()