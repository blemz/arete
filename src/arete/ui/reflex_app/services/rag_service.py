"""
RAG Service for Reflex UI Integration

Provides direct integration with the existing RAG pipeline components
instead of subprocess calls to chat_rag_clean.py.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sys

# Add the arete source to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from src.arete.core.config.settings import Settings
from src.arete.retrieval.hybrid_retriever import HybridRetriever
from src.arete.llm.llm_service import LLMServiceFactory
from src.arete.data.models import ChatMessage, CitationWithScore
from src.arete.core.graph.neo4j_client import Neo4jClient
from src.arete.core.vector.weaviate_client import WeaviateClient
from src.arete.embeddings.embedding_service import EmbeddingServiceFactory

logger = logging.getLogger(__name__)

class RAGService:
    """
    Service for handling RAG queries with direct pipeline integration.
    Provides async methods suitable for Reflex integration.
    """
    
    def __init__(self):
        self.settings = Settings()
        self.neo4j_client = None
        self.weaviate_client = None
        self.hybrid_retriever = None
        self.llm_service = None
        self.embedding_service = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """
        Initialize all RAG components asynchronously.
        Returns True if successful, False if fallback needed.
        """
        if self._initialized:
            return True
            
        try:
            # Initialize clients
            self.neo4j_client = Neo4jClient(self.settings)
            self.weaviate_client = WeaviateClient(self.settings)
            
            # Initialize services
            self.embedding_service = EmbeddingServiceFactory.get_embedding_service(
                provider=self.settings.embedding_provider
            )
            self.llm_service = LLMServiceFactory.get_llm_service(
                provider=self.settings.kg_llm_provider
            )
            
            # Initialize retriever
            self.hybrid_retriever = HybridRetriever(
                neo4j_client=self.neo4j_client,
                weaviate_client=self.weaviate_client,
                embedding_service=self.embedding_service
            )
            
            # Test connectivity
            await asyncio.get_event_loop().run_in_executor(
                None, self._test_connectivity
            )
            
            self._initialized = True
            logger.info("RAG Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG Service: {e}")
            return False
    
    def _test_connectivity(self) -> None:
        """Test connectivity to all services."""
        # Test Neo4j
        with self.neo4j_client.get_session() as session:
            session.run("RETURN 1").single()
        
        # Test Weaviate
        self.weaviate_client.client.is_ready()
        
        # Test embedding service
        self.embedding_service.get_embeddings(["test"])
    
    async def get_rag_response(self, question: str) -> Tuple[str, List[CitationWithScore]]:
        """
        Get RAG response for a question with citations.
        
        Args:
            question: The user's question
            
        Returns:
            Tuple of (response_text, citations)
        """
        if not self._initialized:
            if not await self.initialize():
                return self._get_fallback_response(question)
        
        try:
            # Run RAG pipeline in executor to avoid blocking
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._execute_rag_pipeline, question
            )
            return result
            
        except Exception as e:
            logger.error(f"RAG pipeline failed: {e}")
            return self._get_fallback_response(question)
    
    def _execute_rag_pipeline(self, question: str) -> Tuple[str, List[CitationWithScore]]:
        """Execute the RAG pipeline synchronously."""
        # Retrieve relevant context
        results = self.hybrid_retriever.retrieve(
            query=question,
            limit=5,
            vector_weight=0.7,
            sparse_weight=0.3
        )
        
        # Prepare context for LLM
        context_parts = []
        citations = []
        
        for result in results:
            context_parts.append(f"Source: {result.source_title}\n{result.content}")
            citations.append(CitationWithScore(
                source_title=result.source_title,
                content=result.content[:5000],  # Extended preview as in chat_rag_clean.py
                position=getattr(result, 'position', 0),
                relevance_score=result.score,
                chunk_id=getattr(result, 'chunk_id', '')
            ))
        
        context = "\n\n".join(context_parts)
        
        # Generate response using LLM
        prompt = self._create_prompt(question, context)
        response = self.llm_service.generate_response(
            prompt=prompt,
            max_tokens=4000,
            temperature=0.1
        )
        
        # Clean up response if needed
        response_text = self._clean_response(response)
        
        return response_text, citations
    
    def _create_prompt(self, question: str, context: str) -> str:
        """Create the prompt for the LLM."""
        return f"""You are a knowledgeable tutor specializing in classical philosophy. Answer the user's question using only the provided context from classical philosophical texts.

Instructions:
1. Provide a comprehensive, scholarly answer based on the given context
2. Reference specific philosophical concepts and terminology when relevant
3. Maintain academic rigor while being accessible
4. If the context doesn't fully address the question, acknowledge limitations
5. Do not make up information not present in the context

Context:
{context}

Question: {question}

Answer:"""
    
    def _clean_response(self, response: str) -> str:
        """Clean up the LLM response."""
        # Remove XML tags and entities as in chat_rag_clean.py
        import re
        response = re.sub(r'&[a-zA-Z0-9#]+;', '', response)
        response = re.sub(r'<[^>]+>', '', response)
        return response.strip()
    
    def _get_fallback_response(self, question: str) -> Tuple[str, List[CitationWithScore]]:
        """Provide fallback response when RAG pipeline is unavailable."""
        fallback_responses = {
            "virtue": "Virtue (arete) is excellence of character in classical philosophy. According to Aristotle, virtue is a disposition to choose the mean between extremes of excess and deficiency. Plato views virtue as harmony of the soul's parts, with wisdom, courage, temperance, and justice as cardinal virtues.",
            "socrates": "Socrates (470-399 BCE) was an ancient Greek philosopher known for his method of questioning (elenchus) to examine life and expose ignorance. He believed that 'the unexamined life is not worth living' and that virtue is knowledge.",
            "justice": "Justice (dikaiosyne) is a central concept in Plato's philosophy. In the Republic, Plato defines justice as harmony - in the soul, it's when reason rules over spirit and appetite; in the state, it's when each class performs its proper function.",
            "happiness": "Happiness (eudaimonia) is the highest good according to Aristotle. It's not a feeling but a way of living well, achieved through the practice of virtue and the fulfillment of human potential through rational activity.",
            "knowledge": "Knowledge (episteme) is distinguished from opinion (doxa) in Platonic philosophy. True knowledge is of eternal, unchanging Forms, accessible through reason rather than sensory experience."
        }
        
        # Find best matching fallback
        question_lower = question.lower()
        for key, response in fallback_responses.items():
            if key in question_lower:
                return response, []
        
        # Default fallback
        return ("I apologize, but the RAG system is currently unavailable. This is a placeholder response. "
                "The question about classical philosophy would normally be answered using our knowledge graph "
                "of philosophical texts including Plato, Aristotle, and other classical sources."), []

# Global RAG service instance
_rag_service = None

async def get_rag_service() -> RAGService:
    """Get the global RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service