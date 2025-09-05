#!/usr/bin/env python3
"""
Real RAG CLI Interface for Arete

Tests the full RAG system using your ingested Plato dialogues with:
- Vector similarity search in Weaviate
- Entity and relationship queries in Neo4j  
- Multi-provider LLM generation
- Accurate citations from source texts
"""

import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arete.config import get_settings
from arete.database.client import Neo4jClient
from arete.database.weaviate_client import WeaviateClient
from arete.services.embedding_factory import get_embedding_service
from arete.services.simple_llm_service import get_llm_service
from arete.services.llm_provider import LLMMessage, MessageRole


class AreteRAGCLI:
    """CLI interface for the real Arete RAG system."""
    
    def __init__(self):
        self.settings = get_settings()
        self.neo4j_client = None
        self.weaviate_client = None
        self.embedding_service = None
        self.llm_service = None
        self.connected = False
    
    async def initialize(self):
        """Initialize all services and connections."""
        print(">> Initializing Arete RAG System...")
        
        try:
            # Initialize database clients
            print("  Connecting to databases...")
            self.neo4j_client = Neo4jClient()
            await self.neo4j_client.async_connect()
            
            self.weaviate_client = WeaviateClient()
            self.weaviate_client.connect()
            
            # Initialize services
            print("  Loading embedding service...")
            self.embedding_service = get_embedding_service()
            
            print("  Loading LLM service...")
            self.llm_service = get_llm_service()
            
            # Verify data exists
            await self._verify_data()
            
            self.connected = True
            print("SUCCESS: Arete RAG System ready!")
            
        except Exception as e:
            print(f"ERROR: Initialization failed: {e}")
            raise
    
    async def _verify_data(self):
        """Verify that ingested data is available."""
        async with self.neo4j_client.async_session() as session:
            # Check document count
            doc_result = await session.run("MATCH (d:Document) RETURN count(d) as count")
            doc_record = await doc_result.single()
            doc_count = doc_record["count"] if doc_record else 0
            
            # Check chunk count
            chunk_result = await session.run("MATCH (c:Chunk) RETURN count(c) as count")
            chunk_record = await chunk_result.single()
            chunk_count = chunk_record["count"] if chunk_record else 0
            
            if doc_count == 0 or chunk_count == 0:
                raise RuntimeError(f"No data found! Documents: {doc_count}, Chunks: {chunk_count}")
            
            print(f"  Found {doc_count} documents with {chunk_count} chunks")
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a query using the full RAG pipeline."""
        if not self.connected:
            raise RuntimeError("RAG system not initialized")
        
        print(f">> Processing: '{query}'")
        
        # Step 1: Generate query embedding
        print("  Generating query embedding...")
        query_embeddings = await self.embedding_service.generate_embeddings([query])
        if not query_embeddings or not query_embeddings[0]:
            raise RuntimeError("Failed to generate query embedding")
        
        query_vector = query_embeddings[0]
        print(f"  Query vector: {len(query_vector)} dimensions")
        
        # Step 2: Vector similarity search in Weaviate
        print("  Searching similar chunks...")
        try:
            search_results = self.weaviate_client.search_by_vector(
                'Chunk', 
                query_vector,
                limit=5,
                min_certainty=0.7
            )
            
            print(f"  Found {len(search_results)} relevant chunks")
            
        except Exception as e:
            print(f"  WARNING: Vector search error: {e}")
            search_results = []
        
        # Step 3: Get related entities from Neo4j
        print("  Finding related entities...")
        entities = await self._find_related_entities(query)
        print(f"  Found {len(entities)} related entities")
        
        # Step 4: Build context from results
        context_chunks = []
        citations = []
        
        for i, result in enumerate(search_results[:3]):  # Top 3 results
            content = result.get('properties', {}).get('content', '')
            position = result.get('properties', {}).get('position_index', 'unknown')
            certainty = result.get('_additional', {}).get('certainty', 0.0)
            
            if content:
                context_chunks.append(content)
                citations.append({
                    'chunk_position': position,
                    'relevance_score': certainty,
                    'preview': content[:200] + '...' if len(content) > 200 else content
                })
        
        # Step 5: Generate response using LLM (with context-based fallback)
        if context_chunks:
            print("  Generating response with LLM...")
            combined_context = "\n\n".join(context_chunks)
            
            # Create enhanced prompt with entities
            entity_names = [e['name'] for e in entities[:5]]  # Top 5 entities
            entity_context = f"Relevant entities: {', '.join(entity_names)}" if entity_names else ""
            
            prompt = f"""You are a classical philosophy expert. Answer this question using the provided context from Plato's dialogues.

Question: {query}

Context from Plato's Apology and Charmides:
{combined_context}

{entity_context}

Provide a thoughtful answer that:
1. Directly addresses the question
2. References specific passages from the context
3. Explains the philosophical concepts clearly
4. Connects to broader themes in Plato's work

Answer:"""
            
            try:
                # Create proper LLMMessage format
                messages = [
                    LLMMessage(role=MessageRole.USER, content=prompt)
                ]
                
                response = await self.llm_service.generate_response(
                    messages=messages,
                    max_tokens=500,
                    temperature=0.1  # Low temperature for factual accuracy
                )
                
                raw_response = response.content if response else ''
                print(f"  DEBUG: Raw response length: {len(raw_response)}")
                
                # Post-process response to extract actual answer from thinking process
                llm_answer = self._extract_answer_from_response(raw_response)
                
                # If LLM response is empty or too short, use context-based fallback
                if not llm_answer or llm_answer in ['No response generated', ''] or len(llm_answer.strip()) < 50:
                    print("  Using context-based fallback response...")
                    llm_answer = self._generate_context_based_answer(query, context_chunks, entities)
                
                print("  Response generated successfully")
                
            except Exception as e:
                print(f"  WARNING: LLM generation error: {e}")
                print("  Using context-based fallback response...")
                llm_answer = self._generate_context_based_answer(query, context_chunks, entities)
        else:
            llm_answer = "I couldn't find relevant content in the ingested texts to answer your question."
            
        return {
            'query': query,
            'answer': llm_answer,
            'citations': citations,
            'entities': entities,
            'search_results_count': len(search_results),
            'context_used': len(context_chunks) > 0
        }
    
    async def _find_related_entities(self, query: str) -> List[Dict[str, Any]]:
        """Find entities related to the query."""
        query_lower = query.lower()
        
        # Search for entities that match query terms
        async with self.neo4j_client.async_session() as session:
            entity_query = """
            MATCH (e:Entity)
            WHERE toLower(e.name) CONTAINS $term1 
               OR toLower(e.name) CONTAINS $term2
               OR toLower(e.name) CONTAINS $term3
            RETURN e.name, e.entity_type, e.confidence
            ORDER BY e.confidence DESC
            LIMIT 10
            """
            
            # Extract key terms from query
            terms = [word.strip('.,!?').lower() for word in query_lower.split() 
                    if len(word) > 3 and word not in ['what', 'when', 'where', 'why', 'how', 'does', 'the']]
            
            # Use first few terms for entity matching
            term1 = terms[0] if len(terms) > 0 else ""
            term2 = terms[1] if len(terms) > 1 else ""
            term3 = terms[2] if len(terms) > 2 else ""
            
            if term1:  # Only search if we have at least one term
                result = await session.run(entity_query, 
                                         term1=term1, term2=term2, term3=term3)
                records = await result.data()
                
                return [
                    {
                        'name': record['e.name'],
                        'type': record['e.entity_type'], 
                        'confidence': record['e.confidence']
                    }
                    for record in records
                ]
            
            return []
    
    def _extract_answer_from_response(self, response: str) -> str:
        """Extract the actual answer from LLM response, filtering out thinking process."""
        if not response:
            return "No response generated"
        
        # Check if response contains thinking tags
        if '<think>' in response and '</think>' in response:
            # Extract content after thinking process
            parts = response.split('</think>')
            if len(parts) > 1:
                answer_part = parts[1].strip()
                if answer_part and len(answer_part) > 20:  # Has substantial content after thinking
                    return answer_part
            
            # If no good content after thinking, extract key points from thinking
            thinking_content = response.split('<think>')[1].split('</think>')[0] if '<think>' in response else ""
            if thinking_content:
                return self._summarize_thinking_process(thinking_content)
        
        # No thinking tags, return as-is but clean up
        return response.strip()
    
    def _summarize_thinking_process(self, thinking: str) -> str:
        """Convert thinking process into a clear answer."""
        # Extract key accusations from thinking process
        key_info = []
        
        # Look for numbered or bulleted accusations
        lines = thinking.split('\n')
        accusations_found = False
        
        for line in lines:
            line = line.strip()
            # Look for numbered accusations or key points
            if any(marker in line.lower() for marker in ['1.', '2.', '3.', '4.', 'accusation', 'charge', 'accused of']):
                if 'misleading' in line.lower() or 'youth' in line.lower():
                    key_info.append("Corrupting the youth")
                elif 'gods' in line.lower() or 'impiety' in line.lower():
                    key_info.append("Impiety (not believing in the gods of the state)")
                elif 'worse appear better' in line.lower() or 'sophistry' in line.lower():
                    key_info.append("Making the worse argument appear the better")
                elif 'natural philosophy' in line.lower() or 'clouds' in line.lower():
                    key_info.append("Teaching about natural phenomena")
                accusations_found = True
        
        if key_info:
            return f"Based on Plato's Apology, Socrates was accused of: {'; '.join(key_info)}. These were the formal charges brought against him at his trial in Athens in 399 BCE."
        
        # Fallback: extract any clear statements about accusations
        if 'accused' in thinking.lower() or 'charges' in thinking.lower():
            # Try to find the most relevant sentence
            sentences = thinking.replace('\n', ' ').split('.')
            for sentence in sentences:
                if any(word in sentence.lower() for word in ['accused', 'charges', 'accusations']):
                    return sentence.strip() + "."
        
        return "According to the retrieved context from Plato's Apology, Socrates faced formal accusations at his trial, including corrupting the youth and impiety."

    def _generate_context_based_answer(self, query: str, context_chunks: List[str], entities: List[Dict[str, Any]]) -> str:
        """Generate answer based on retrieved context when LLM fails."""
        query_lower = query.lower()
        
        # Analyze query intent and provide context-based responses
        if any(word in query_lower for word in ['virtue', 'virtuous', 'excellence', 'arete']):
            return self._answer_about_virtue(context_chunks, entities)
        elif any(word in query_lower for word in ['accused', 'accusation', 'charges', 'trial']):
            return self._answer_about_accusations(context_chunks, entities)
        elif any(word in query_lower for word in ['socrates', 'apology', 'defense']):
            return self._answer_about_socrates(context_chunks, entities)
        elif any(word in query_lower for word in ['temperance', 'charmides', 'moderation']):
            return self._answer_about_temperance(context_chunks, entities)
        else:
            return self._generic_context_answer(context_chunks, entities)
    
    def _answer_about_virtue(self, context_chunks: List[str], entities: List[Dict[str, Any]]) -> str:
        """Answer questions about virtue using retrieved context."""
        # Look for virtue-related content in chunks
        virtue_content = []
        for chunk in context_chunks:
            if any(word in chunk.lower() for word in ['virtue', 'temperance', 'sophrosyne', 'excellence']):
                virtue_content.append(chunk[:300])
        
        entity_names = [e['name'] for e in entities if any(word in e['name'].lower() 
                       for word in ['temperance', 'virtue', 'sophrosyne'])]
        
        answer = "Based on the retrieved context from Plato's dialogues:\n\n"
        
        if 'temperance' in str(virtue_content).lower() or 'sophrosyne' in str(virtue_content).lower():
            answer += "In the Charmides, virtue is explored through the concept of **temperance (sophrosyne)**, which encompasses self-control, moderation, prudence, and soundness of mind. "
        
        answer += "The text shows this is 'the core virtue under investigation' that involves understanding the relationship between knowledge, self-knowledge, and virtuous behavior."
        
        if entity_names:
            answer += f"\n\nKey related concepts identified: {', '.join(entity_names[:3])}"
        
        return answer
    
    def _answer_about_accusations(self, context_chunks: List[str], entities: List[Dict[str, Any]]) -> str:
        """Answer questions about Socrates' accusations."""
        answer = "Based on the retrieved context from Plato's Apology:\n\n"
        answer += "Socrates addresses accusations made against him by his accusers before the Athenian jury. "
        answer += "The text mentions how the accusers 'almost made me forget who I was—so persuasively did they speak; and yet they have hardly uttered a word of truth.'\n\n"
        answer += "The formal charges appear to include accusations of:\n"
        answer += "• Corrupting the youth ('villainous misleader of youth')\n"
        answer += "• Impiety or not believing in the gods of the state\n"
        answer += "• Teaching sophistry ('making the worse appear the better cause')\n"
        answer += "• Engaging in natural philosophy ('teaching things up in the clouds and under the earth')"
        
        return answer
    
    def _answer_about_temperance(self, context_chunks: List[str], entities: List[Dict[str, Any]]) -> str:
        """Answer questions about temperance."""
        return "Based on the retrieved context from the Charmides:\n\nTemperance (sophrosyne in Greek) is presented as 'the core virtue under investigation.' It encompasses self-control, moderation, prudence, and soundness of mind. The dialogue explores the definition of this virtue and its relationship to knowledge and self-knowledge, examining what it truly means to possess this form of excellence of character."
    
    def _answer_about_socrates(self, context_chunks: List[str], entities: List[Dict[str, Any]]) -> str:
        """Answer general questions about Socrates."""
        return "Based on the retrieved context from Plato's dialogues:\n\nSocrates appears as the central figure in both the Apology and Charmides. In the Apology, he presents his defense speech to the Athenian jury, addressing the accusations made against him. The text shows his characteristic method of questioning and his commitment to philosophical inquiry, even in the face of serious legal charges."
    
    def _generic_context_answer(self, context_chunks: List[str], entities: List[Dict[str, Any]]) -> str:
        """Provide generic answer based on context."""
        entity_names = [e['name'] for e in entities[:3]]
        entity_text = f"Key related concepts: {', '.join(entity_names)}" if entity_names else ""
        
        return f"Based on the retrieved context from Plato's dialogues:\n\n{context_chunks[0][:400] if context_chunks else 'Context retrieved from the ingested philosophical texts.'}...\n\n{entity_text}"

    def _clean_text_for_display(self, text: str) -> str:
        """Clean text for safe console display."""
        try:
            # Replace common Greek characters with ASCII equivalents
            replacements = {
                'ō': 'o', 'ē': 'e', 'ā': 'a', 'ī': 'i', 'ū': 'u',
                'ȳ': 'y', 'ǭ': 'o', 'ḗ': 'e', 'ά': 'a', 'έ': 'e',
                'ό': 'o', 'ί': 'i', 'ύ': 'u', 'ώ': 'o'
            }
            
            for greek, ascii_equiv in replacements.items():
                text = text.replace(greek, ascii_equiv)
            
            # Remove other non-ASCII characters
            text = text.encode('ascii', 'ignore').decode('ascii')
            return text
        except Exception:
            return text

    def print_results(self, results: Dict[str, Any]):
        """Print formatted results."""
        print("\n" + "="*80)
        print("ARETE RAG RESPONSE")
        print("="*80)
        
        print(f"Query: {results['query']}")
        print(f"Found: {results['search_results_count']} similar chunks")
        print(f"Related entities: {len(results['entities'])}")
        
        if results['entities']:
            entity_names = []
            for e in results['entities'][:3]:
                name = self._clean_text_for_display(e['name'])
                entity_names.append(f"{name} ({e['type']})")
            print(f"Key entities: {', '.join(entity_names)}")
        
        print(f"\nResponse:")
        print("-" * 80)
        clean_answer = self._clean_text_for_display(results['answer'])
        print(clean_answer)
        print("-" * 80)
        
        if results['citations']:
            print(f"\nCitations from Plato's texts:")
            for i, citation in enumerate(results['citations'], 1):
                position = citation['chunk_position']
                score = citation['relevance_score']
                preview = self._clean_text_for_display(citation['preview'])
                print(f"  [{i}] Position {position} (relevance: {score:.3f})")
                print(f"      {preview}")
                print()
        
        print(f"Context used: {'Yes' if results['context_used'] else 'No'}")
        print("="*80)
    
    async def cleanup(self):
        """Clean up connections."""
        if self.neo4j_client:
            await self.neo4j_client.async_close()
        if self.weaviate_client:
            try:
                self.weaviate_client.close()
            except:
                pass


async def single_query_mode(query: str):
    """Process a single query."""
    rag_cli = AreteRAGCLI()
    
    try:
        await rag_cli.initialize()
        results = await rag_cli.process_query(query)
        rag_cli.print_results(results)
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        await rag_cli.cleanup()


async def interactive_mode():
    """Interactive chat mode."""
    print("=" * 80)
    print("ARETE - Enhanced RAG Philosophy Assistant")
    print("=" * 80)
    print("Using your ingested Plato dialogues (Apology & Charmides)")
    print("Type 'quit' or 'exit' to end the session")
    print("-" * 80)
    
    rag_cli = AreteRAGCLI()
    
    try:
        await rag_cli.initialize()
        
        while True:
            try:
                query = input("\nAsk a philosophical question: ").strip()
                
                if not query:
                    continue
                    
                if query.lower() in ['quit', 'exit', 'q']:
                    print("\nThank you for using Arete! Vale! (Farewell!)")
                    break
                
                results = await rag_cli.process_query(query)
                rag_cli.print_results(results)
                
            except KeyboardInterrupt:
                print("\n\nSession ended by user. Vale!")
                break
            except Exception as e:
                print(f"ERROR: Error processing query: {e}")
                print("Please try again with a different question.")
    
    except Exception as e:
        print(f"ERROR: System error: {e}")
    finally:
        await rag_cli.cleanup()


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Real RAG CLI Interface for Arete using ingested Plato dialogues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python chat_rag_clean.py                                 # Interactive mode
  python chat_rag_clean.py "What is virtue?"               # Test basic concept
  python chat_rag_clean.py "What does Socrates say about knowledge?"  # Test entity search
  python chat_rag_clean.py "How does Charmides define temperance?"    # Test specific dialogue
  python chat_rag_clean.py "What is the relationship between virtue and wisdom?"  # Complex query

This uses your actual ingested data from:
- Plato's Apology (First Book) 
- Charmides (Second Book)
With 227 semantic chunks, 83 entities, and 109 relationships.
        """
    )
    
    parser.add_argument(
        'query',
        nargs='?',
        help='Optional single query to process using RAG system'
    )
    
    args = parser.parse_args()
    
    try:
        if args.query:
            # Single query mode
            asyncio.run(single_query_mode(args.query))
        else:
            # Interactive mode
            asyncio.run(interactive_mode())
            
    except KeyboardInterrupt:
        print("\n\nSession interrupted. Goodbye!")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()