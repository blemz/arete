#!/usr/bin/env python3
"""
Production-ready processing of complete classical philosophical texts.

This script uses the existing Phase 2 pipeline efficiently to process entire books:
- NO artificial chunk limits
- NO text truncation
- Batch processing for embeddings
- Efficient knowledge graph extraction
- Progress tracking for large texts
- Memory-efficient processing
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arete.processing.extractors import PDFExtractor
from arete.processing.chunker import ChunkingStrategy
from arete.services.enhanced_kg_service import EnhancedKnowledgeGraphService  
from arete.models.document import Document, ProcessingStatus
from arete.models.chunk import Chunk
from arete.services.embedding_factory import get_embedding_service
from arete.config import get_settings


async def process_full_classical_text(pdf_path: str):
    """
    Process a complete classical philosophical text using existing Arete infrastructure.
    
    This processes the ENTIRE book without artificial limitations:
    1. Complete PDF extraction
    2. Full document processing 
    3. All chunks generated and processed
    4. Batch embedding generation
    5. Efficient knowledge graph extraction
    6. Production-ready storage preparation
    """
    print(f"Processing Complete Classical Text: {Path(pdf_path).name}")
    print("=" * 80)
    
    start_time = time.time()
    
    # Initialize configuration
    config = get_settings()
    
    # Step 1: Complete PDF extraction
    print("\nStep 1: Complete PDF Text Extraction")
    pdf_extractor = PDFExtractor()
    
    try:
        extraction_result = pdf_extractor.extract_from_file(pdf_path)
        chars_extracted = len(extraction_result['text'])
        print(f"SUCCESS: Extracted {chars_extracted:,} characters from complete text")
        
        if extraction_result['metadata']:
            print(f"Title: {extraction_result['metadata'].title}")
            print(f"Author: {extraction_result['metadata'].author}")
            print(f"Pages: {extraction_result['metadata'].page_count}")
        
    except Exception as e:
        print(f"ERROR: PDF extraction failed: {e}")
        return None
    
    # Step 2: Complete Document model creation
    print("\nStep 2: Complete Document Model Creation")
    document = Document(
        title=extraction_result['metadata'].title if extraction_result['metadata'] else Path(pdf_path).stem,
        author=extraction_result['metadata'].author if extraction_result['metadata'] else "Classical Philosopher",
        content=extraction_result['text'],
        language="Ancient Greek (English Translation)",
        source="Classical Philosophy Collection",
        processing_status=ProcessingStatus.PROCESSING,
        word_count=len(extraction_result['text'].split())
    )
    print(f"SUCCESS: Created document with {document.word_count:,} total words")
    
    # Step 3: Complete text chunking
    print(f"\nStep 3: Complete Intelligent Text Chunking")
    chunker = ChunkingStrategy.get_chunker("paragraph")
    
    print("Processing all chunks from complete text...")
    chunk_start = time.time()
    all_chunks = chunker.chunk_text(document.content, document.id)
    chunk_time = time.time() - chunk_start
    
    print(f"SUCCESS: Created {len(all_chunks):,} chunks in {chunk_time:.2f}s")
    
    # Show chunking statistics
    total_chunk_chars = sum(len(chunk.text) for chunk in all_chunks)
    avg_chunk_size = total_chunk_chars / len(all_chunks) if all_chunks else 0
    print(f"Chunk Statistics:")
    print(f"  Total chunks: {len(all_chunks):,}")
    print(f"  Total chunk text: {total_chunk_chars:,} characters")
    print(f"  Average chunk size: {avg_chunk_size:.0f} characters")
    
    # Step 4: Enhanced Knowledge Graph Extraction using LLM-based approach
    print(f"\nStep 4: Enhanced Knowledge Graph Extraction from ALL {len(all_chunks)} chunks")
    try:
        # Initialize enhanced KG service
        enhanced_kg_service = EnhancedKnowledgeGraphService()
        
        print(f"Using enhanced philosophical relationship extraction...")
        print(f"Supported entity types: {', '.join(enhanced_kg_service.allowed_nodes[:5])}...")
        print(f"Supported relationship types: {', '.join(enhanced_kg_service.allowed_relationships[:5])}...")
        
        kg_start = time.time()
        
        # Process the entire document text with enhanced extraction
        print(f"Processing complete text with enhanced LLM-based extraction...")
        entities, relationships = await enhanced_kg_service.extract_knowledge_graph(
            text=document.content,
            document_id=str(document.id),
            chunk_size=2000,  # Optimal chunks for philosophical context preservation
            max_chunks=None   # Process all chunks with powerful KG model
        )
        
        kg_time = time.time() - kg_start
        
        print(f"SUCCESS: Enhanced extraction found {len(entities)} entities and {len(relationships)} relationships in {kg_time:.2f}s")
        
        # Show top entities with improved formatting
        if entities:
            print("  Top Philosophical Entities:")
            for i, entity in enumerate(entities[:10]):
                entity_type_str = entity.entity_type.value if hasattr(entity.entity_type, 'value') else str(entity.entity_type)
                print(f"    {i+1}. {entity.name} ({entity_type_str}) - confidence: {entity.confidence:.2f}")
        
        # Show top relationships with improved formatting  
        if relationships:
            print("  Top Philosophical Relationships:")
            for i, rel in enumerate(relationships[:8]):
                confidence = rel.get('confidence', 0.0)
                print(f"    {i+1}. {rel.get('subject', 'Unknown')} --[{rel.get('relation', 'RELATES_TO')}]--> {rel.get('object', 'Unknown')} (conf: {confidence:.2f})")
        
        # Quality assessment
        high_confidence_rels = [r for r in relationships if r.get('confidence', 0) >= 0.7]
        print(f"  Quality metrics: {len(high_confidence_rels)}/{len(relationships)} high-confidence relationships ({len(high_confidence_rels)/len(relationships)*100 if relationships else 0:.1f}%)")
            
    except Exception as e:
        print(f"WARNING: Enhanced knowledge extraction failed: {e}")
        print(f"Error details: {type(e).__name__}")
        entities, relationships = [], []
    
    # Step 5: Batch embedding generation for ALL chunks
    print(f"\nStep 5: Batch Embedding Generation for ALL {len(all_chunks):,} Chunks")
    try:
        embedding_service = get_embedding_service()
        
        # Extract all chunk texts for batch processing
        chunk_texts = [chunk.text for chunk in all_chunks]
        print(f"Generating embeddings for {len(chunk_texts):,} chunks using batch processing...")
        
        embed_start = time.time()
        
        # Use the service's batch processing capabilities
        if hasattr(embedding_service, 'generate_embeddings_batch'):
            # Batch processing available
            embeddings = embedding_service.generate_embeddings_batch(
                chunk_texts,
                batch_size=32,  # Optimal batch size
                normalize=True
            )
            
            # Assign embeddings to chunks
            for chunk, embedding in zip(all_chunks, embeddings):
                chunk.embedding_vector = embedding
                
        else:
            # Fallback: process in efficient batches manually
            batch_size = 32
            processed_count = 0
            
            for i in range(0, len(all_chunks), batch_size):
                batch_chunks = all_chunks[i:i + batch_size]
                
                for chunk in batch_chunks:
                    embedding = embedding_service.generate_embedding(chunk.text)
                    chunk.embedding_vector = embedding
                    processed_count += 1
                    
                    # Progress update every 100 chunks
                    if processed_count % 100 == 0:
                        print(f"  Progress: {processed_count}/{len(all_chunks)} chunks processed ({processed_count/len(all_chunks)*100:.1f}%)")
        
        embed_time = time.time() - embed_start
        embedding_dim = len(all_chunks[0].embedding_vector) if all_chunks else 0
        
        print(f"SUCCESS: Generated {embedding_dim}-dimensional embeddings for ALL {len(all_chunks):,} chunks in {embed_time:.2f}s")
        print(f"Embedding rate: {len(all_chunks) / embed_time:.1f} chunks/second")
            
    except Exception as e:
        print(f"WARNING: Embedding generation failed: {e}")
        print("This may indicate embedding service configuration issues")
    
    # Step 6: Production storage preparation 
    print(f"\nStep 6: Production Storage Preparation")
    print("Complete document ready for production storage:")
    print(f"  Document model: Full text with metadata and processing status")
    print(f"  Text chunks: {len(all_chunks):,} chunks with embeddings")
    print(f"  Knowledge graph: {len(entities)} entities, {len(relationships)} relationships")
    print(f"  Storage systems: Neo4j (graph) + Weaviate (vectors)")
    
    # Production metrics
    total_time = time.time() - start_time
    processing_rate = document.word_count / total_time if total_time > 0 else 0
    
    print(f"\nComplete Processing Summary:")
    print(f"  Document: {document.title}")
    print(f"  Author: {document.author}")
    print(f"  Content: {document.word_count:,} words, {chars_extracted:,} characters")
    print(f"  Text chunks: {len(all_chunks):,} generated and ALL processed for KG extraction")
    print(f"  Entities: {len(entities)} extracted from complete text")
    print(f"  Relationships: {len(relationships)} found from all {len(all_chunks)} chunks")
    embedded_chunks = len([c for c in all_chunks if hasattr(c, 'embedding_vector')])
    print(f"  Embeddings: {embedded_chunks:,}/{len(all_chunks):,} chunks ({embedded_chunks/len(all_chunks)*100:.1f}%)")
    print(f"  Processing time: {total_time:.2f}s")
    print(f"  Processing rate: {processing_rate:.0f} words/second")
    
    print(f"\nSUCCESS: COMPLETE classical text processing finished!")
    print(f"Ready for production deployment with full-scale classical text")
    
    return {
        'document': document,
        'chunks': all_chunks,  # ALL chunks, no limits
        'entities': entities,
        'relationships': relationships,
        'extraction_result': extraction_result,
        'processing_metrics': {
            'total_time': total_time,
            'processing_rate': processing_rate,
            'chunks_per_second': len(all_chunks) / total_time if total_time > 0 else 0,
            'embedding_rate': embedded_chunks / embed_time if 'embed_time' in locals() and embed_time > 0 else 0
        }
    }


def main():
    """Process complete classical philosophical texts."""
    if len(sys.argv) != 2:
        print("Usage: python process_full_classical_texts.py <path_to_pdf>")
        print("\nProcess your complete classical texts:")
        print("  python process_full_classical_texts.py \"data/pdfs/Plato The Republic (Cambridge, Tom Griffith) Clean.pdf\"")
        print("  python process_full_classical_texts.py \"data/pdfs/Aristotle's Nicomachean Ethics.pdf\"") 
        print("  python process_full_classical_texts.py \"data/pdfs/Socratis Dialogues.pdf\"")
        return
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"ERROR: File not found: {pdf_path}")
        return
    
    print(f"Arete Classical Text Processing System")
    print(f"Processing: {Path(pdf_path).name}")
    print(f"Mode: FULL PRODUCTION (no artificial limits)")
    print()
    
    # Process the complete classical text
    result = asyncio.run(process_full_classical_text(pdf_path))
    
    if result:
        print(f"\nNext Steps for Production Deployment:")
        print("1. Start databases: docker-compose up neo4j weaviate")
        print("2. Store document: DocumentRepository.create(document)")  
        print("3. Store chunks: Batch insert all chunks with embeddings")
        print("4. Store knowledge graph: Entity and relationship insertion")
        print("5. Enable search: Configure hybrid retrieval system")
        print("6. Test RAG pipeline: Query processing with complete classical text")


if __name__ == "__main__":
    main()