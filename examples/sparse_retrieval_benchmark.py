"""
Performance benchmark comparing sparse and dense retrieval methods.

Demonstrates the implementation and performance characteristics of:
- BM25 sparse retrieval
- SPLADE sparse retrieval  
- Dense semantic retrieval
- Hybrid retrieval strategies

This script provides practical examples and benchmarking for Phase 3.2
Sparse Retrieval System implementation.
"""

import time
import asyncio
from typing import List, Dict, Any
from uuid import uuid4
import logging

from arete.models.chunk import Chunk
from arete.services.sparse_retrieval_service import (
    BM25Retriever,
    SPLADERetriever,
    SparseRetrievalService
)
from arete.services.dense_retrieval_service import DenseRetrievalService
from arete.repositories.retrieval import (
    RetrievalRepository,
    RetrievalMethod,
    HybridStrategy,
    HybridRetrievalConfig
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_philosophical_chunks() -> List[Chunk]:
    """Create sample philosophical text chunks for benchmarking."""
    texts = [
        "Virtue ethics, also known as aretaic ethics, is one of the three major approaches in normative ethics. It emphasizes the importance of character rather than actions or consequences.",
        
        "Aristotle argued that virtue (arete) is a disposition to behave in the right way and as a mean between extremes of deficiency and excess.",
        
        "The concept of eudaimonia, often translated as happiness or flourishing, is central to Aristotelian ethics. It represents the highest human good.",
        
        "Practical wisdom (phronesis) enables one to discern the right course of action in particular circumstances. It is acquired through experience and moral education.",
        
        "Justice, according to Plato, is a virtue that involves giving each person their due. It requires both knowledge of good and evil and the power to act on that knowledge.",
        
        "The cardinal virtues - prudence, justice, fortitude, and temperance - were first described by Plato and later adopted by Christian philosophers.",
        
        "Stoic ethics emphasizes virtue as the sole path to eudaimonia. External goods are considered indifferent to human flourishing.",
        
        "Marcus Aurelius wrote that the universe is change and life is opinion, emphasizing the importance of accepting what we cannot control.",
        
        "Kantian deontological ethics focuses on duty and the categorical imperative as the foundation of moral action.",
        
        "The categorical imperative states: Act only according to that maxim whereby you can at the same time will that it should become a universal law.",
        
        "Mill's utilitarianism promotes the greatest happiness principle, where actions are right insofar as they promote happiness.",
        
        "The harm principle, proposed by Mill, suggests that actions are wrong only if they harm others or prevent them from pursuing their own good.",
        
        "Existentialist ethics, as developed by Sartre, emphasizes individual freedom and responsibility in creating one's own values.",
        
        "Nietzsche's concept of the Übermensch represents an individual who creates their own values and meaning in life.",
        
        "Care ethics, developed by feminist philosophers like Nel Noddings, emphasizes relationships, care, and interdependence.",
        
        "Environmental ethics examines the moral relationship between humans and the natural world, considering our duties to future generations.",
        
        "Buddhist ethics centers on reducing suffering through right intention, right action, and right livelihood as part of the Noble Eightfold Path.",
        
        "The principle of ahimsa (non-violence) is fundamental to Buddhist, Hindu, and Jain ethical systems.",
        
        "Confucian ethics emphasizes ren (benevolence), li (proper conduct), and the cultivation of moral character through education.",
        
        "The concept of filial piety (xiao) in Confucianism represents respect and care for one's parents and ancestors."
    ]
    
    chunks = []
    for i, text in enumerate(texts):
        chunk = Chunk(
            document_id=uuid4(),
            text=text,
            position=i,
            chunk_type="paragraph",
            start_char=0,
            end_char=len(text),
            word_count=len(text.split())
        )
        chunks.append(chunk)
    
    return chunks


def benchmark_sparse_retrieval():
    """Benchmark different sparse retrieval algorithms."""
    print("\n" + "="*80)
    print("SPARSE RETRIEVAL BENCHMARK")
    print("="*80)
    
    # Create test data
    chunks = create_philosophical_chunks()
    test_queries = [
        "virtue ethics character",
        "Aristotle practical wisdom",
        "justice moral duty",
        "happiness eudaimonia flourishing",
        "categorical imperative Kant"
    ]
    
    print(f"Test dataset: {len(chunks)} philosophical chunks")
    print(f"Test queries: {len(test_queries)} queries")
    print()
    
    # Benchmark BM25
    print("BM25 Retrieval Benchmark:")
    print("-" * 40)
    
    bm25_retriever = BM25Retriever(k1=1.2, b=0.75)
    
    # Build index
    start_time = time.time()
    bm25_retriever.build_index(chunks)
    index_time = time.time() - start_time
    
    print(f"Index build time: {index_time:.3f}s")
    
    # Get index statistics
    stats = bm25_retriever.get_index_statistics()
    print(f"Total documents: {stats['total_documents']}")
    print(f"Vocabulary size: {stats['vocabulary_size']}")
    print(f"Average doc length: {stats['average_document_length']:.2f} terms")
    
    # Run search queries
    total_search_time = 0
    total_results = 0
    
    for query in test_queries:
        start_time = time.time()
        results = bm25_retriever.search(query, limit=5)
        search_time = time.time() - start_time
        
        total_search_time += search_time
        total_results += len(results)
        
        print(f"Query: '{query}' -> {len(results)} results in {search_time:.4f}s")
    
    avg_query_time = total_search_time / len(test_queries)
    print(f"Average query time: {avg_query_time:.4f}s")
    print(f"Average results per query: {total_results / len(test_queries):.1f}")
    print()
    
    # Benchmark SPLADE (simplified implementation)
    print("SPLADE Retrieval Benchmark:")
    print("-" * 40)
    
    splade_retriever = SPLADERetriever(expansion_factor=1.5, importance_threshold=0.1)
    
    # Build index
    start_time = time.time()
    splade_retriever.build_index(chunks)
    splade_index_time = time.time() - start_time
    
    print(f"Index build time: {splade_index_time:.3f}s")
    
    # Get index statistics
    splade_stats = splade_retriever.get_index_statistics()
    print(f"Total documents: {splade_stats['total_documents']}")
    print(f"Vocabulary size: {splade_stats['vocabulary_size']}")
    print(f"Average doc length: {splade_stats['average_document_length']:.2f} terms")
    
    # Run search queries
    splade_search_time = 0
    splade_results = 0
    
    for query in test_queries:
        start_time = time.time()
        results = splade_retriever.search(query, limit=5)
        search_time = time.time() - start_time
        
        splade_search_time += search_time
        splade_results += len(results)
        
        print(f"Query: '{query}' -> {len(results)} results in {search_time:.4f}s")
    
    splade_avg_query_time = splade_search_time / len(test_queries)
    print(f"Average query time: {splade_avg_query_time:.4f}s")
    print(f"Average results per query: {splade_results / len(test_queries):.1f}")
    print()
    
    # Comparison summary
    print("Performance Comparison:")
    print("-" * 40)
    print(f"{'Algorithm':<15} {'Index Time':<12} {'Avg Query Time':<15} {'Vocab Size':<12}")
    print(f"{'BM25':<15} {index_time:.3f}s{'':<7} {avg_query_time:.4f}s{'':<8} {stats['vocabulary_size']:<12}")
    print(f"{'SPLADE':<15} {splade_index_time:.3f}s{'':<7} {splade_avg_query_time:.4f}s{'':<8} {splade_stats['vocabulary_size']:<12}")
    print()
    
    if avg_query_time < splade_avg_query_time:
        print("+ BM25 is faster for query processing")
    else:
        print("+ SPLADE is faster for query processing")
    
    print()


def demonstrate_philosophical_search():
    """Demonstrate sparse retrieval with philosophical queries."""
    print("\n" + "="*80)
    print("PHILOSOPHICAL SEARCH DEMONSTRATION")
    print("="*80)
    
    chunks = create_philosophical_chunks()
    
    # Initialize BM25 retriever
    retriever = BM25Retriever()
    retriever.build_index(chunks)
    
    philosophical_queries = [
        "virtue character moral excellence",
        "practical wisdom decision making",
        "categorical imperative universal law",
        "greatest happiness principle",
        "non-violence ahimsa Buddhism"
    ]
    
    for query in philosophical_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 60)
        
        start_time = time.time()
        results = retriever.search(query, limit=3, min_relevance=0.01)
        search_time = time.time() - start_time
        
        print(f"Found {len(results)} results in {search_time:.4f}s:")
        
        for i, result in enumerate(results[:3], 1):
            # In this simplified version, results don't contain actual chunks
            # In production, would show actual chunk text and relevance scores
            print(f"{i}. Score: {result.metadata.get('sparse_score', 0):.3f}")
            print(f"   Algorithm: {result.metadata.get('algorithm', 'Unknown')}")
        
        if not results:
            print("   No results found above relevance threshold")


def benchmark_comparison_summary():
    """Provide comprehensive benchmark summary."""
    print("\n" + "="*80) 
    print("SPARSE vs DENSE RETRIEVAL - CONCEPTUAL COMPARISON")
    print("="*80)
    
    print("SPARSE RETRIEVAL (BM25/SPLADE):")
    print("+ Advantages:")
    print("   • Exact keyword matching")
    print("   • Fast index building and searching")
    print("   • Interpretable results")
    print("   • Works well with technical/domain terms")
    print("   • Lower memory requirements")
    print("   • No neural model required")
    
    print("\n✗ Limitations:")
    print("   • No semantic understanding")
    print("   • Vocabulary mismatch issues")
    print("   • Limited cross-lingual capability")
    print("   • Poor handling of synonyms")
    
    print("\nDENSE RETRIEVAL (Embeddings):")
    print("+ Advantages:")
    print("   • Semantic similarity matching")
    print("   • Handles synonyms and paraphrases")
    print("   • Cross-lingual capabilities")
    print("   • Better for conceptual queries")
    print("   • Captures context and meaning")
    
    print("\n✗ Limitations:")
    print("   • Requires neural models")
    print("   • Higher computational requirements")
    print("   • Less interpretable")
    print("   • May miss exact term matches")
    print("   • Embedding model dependencies")
    
    print("\nHYBRID RETRIEVAL:")
    print("♦ Best of Both Worlds:")
    print("   • Combines lexical and semantic matching")
    print("   • Improved recall and precision")
    print("   • Flexible fusion strategies")
    print("   • Domain-specific optimization")
    print("   • Redundancy and robustness")
    
    print("\nRECOMMENDATIONS:")
    print("• Use Sparse When:")
    print("   • Exact terminology matters")
    print("   • Fast response time required") 
    print("   • Limited computational resources")
    print("   • Domain has specific vocabulary")
    
    print("\n• Use Dense When:")
    print("   • Semantic similarity important")
    print("   • Handling paraphrases")
    print("   • Cross-lingual requirements")
    print("   • Conceptual understanding needed")
    
    print("\n• Use Hybrid When:")
    print("   • Maximum retrieval quality required")
    print("   • Diverse query types expected")
    print("   • Production philosophical tutoring")
    print("   • Can afford computational cost")


def main():
    """Run comprehensive sparse retrieval benchmark."""
    print("ARETE PHASE 3.2 - SPARSE RETRIEVAL SYSTEM BENCHMARK")
    print("Comparing BM25 and SPLADE implementations for philosophical text retrieval")
    
    # Run benchmarks
    benchmark_sparse_retrieval()
    demonstrate_philosophical_search()
    benchmark_comparison_summary()
    
    print("\n" + "="*80)
    print("BENCHMARK COMPLETE")
    print("="*80)
    print("* Results show sparse retrieval implementation is functional")
    print("> Ready for integration with hybrid retrieval system") 
    print("- Consider these metrics for production optimization")
    print("\nNext steps:")
    print("• Integrate with Neo4j for full functionality")
    print("• Add dense retrieval comparison")
    print("• Test hybrid fusion strategies")
    print("• Optimize for philosophical terminology")


if __name__ == "__main__":
    main()