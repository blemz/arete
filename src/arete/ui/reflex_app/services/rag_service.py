"""
RAG Service for Reflex UI Integration

Provides direct integration with the existing RAG pipeline components
instead of subprocess calls to chat_rag_clean.py.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the arete source to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from src.arete.config import Settings
from src.arete.database.client import Neo4jClient
from src.arete.database.weaviate_client import WeaviateClient
from src.arete.models import CitationWithScore
from src.arete.services.embedding_factory import get_embedding_service
from src.arete.services.simple_llm_service import get_llm_service

logger = logging.getLogger(__name__)

class RAGService:
    """
    Service for handling RAG queries with direct pipeline integration.
    Provides async methods suitable for Reflex integration.
    """

    def __init__(
        self,
        neo4j_client=None,
        weaviate_client=None,
        embedding_service=None,
        llm_service=None,
        settings=None
    ):
        """
        Initialize RAG Service with optional dependency injection.

        Args:
            neo4j_client: Neo4j client instance (optional, for testing)
            weaviate_client: Weaviate client instance (optional, for testing)
            embedding_service: Embedding service instance (optional, for testing)
            llm_service: LLM service instance (optional, for testing)
            settings: Settings instance (optional, for testing)
        """
        self.settings = settings or Settings()
        self.neo4j_client = neo4j_client
        self.weaviate_client = weaviate_client
        self.embedding_service = embedding_service
        self.llm_service = llm_service
        self._initialized = bool(neo4j_client and weaviate_client and embedding_service)

    async def initialize(self) -> bool:
        """
        Initialize all RAG components asynchronously.
        Returns True if successful, False if fallback needed.

        If dependencies were injected via constructor, this is a no-op.
        Otherwise, creates clients and services.
        """
        if self._initialized:
            return True

        try:
            # Initialize clients only if not injected
            if not self.neo4j_client:
                self.neo4j_client = Neo4jClient(self.settings)

            if not self.weaviate_client:
                self.weaviate_client = WeaviateClient(self.settings)

            # Initialize services using factory functions only if not injected
            if not self.embedding_service:
                self.embedding_service = get_embedding_service()

            if not self.llm_service:
                self.llm_service = get_llm_service()

            # Test connectivity only for non-injected dependencies
            if not self._initialized:
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

    async def get_rag_response(self, question: str) -> tuple[str, list[CitationWithScore]]:
        """
        Get RAG response for a question with citations.

        Args:
            question: The user's question

        Returns:
            Tuple of (response_text, citations)
        """
        if not self._initialized and not await self.initialize():
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

    def _execute_rag_pipeline(self, question: str) -> tuple[str, list[CitationWithScore]]:
        """Execute the RAG pipeline synchronously."""
        # Step 1: Generate query embedding
        query_embeddings = self.embedding_service.get_embeddings([question])
        query_vector = query_embeddings[0]

        # Step 2: Vector similarity search in Weaviate
        search_results = self.weaviate_client.search_by_vector(
            'Chunk',
            query_vector,
            limit=5,
            min_certainty=0.7
        )

        # Step 3: Build context and citations from results
        context_parts = []
        citations = []

        for result in search_results[:3]:  # Top 3 results
            content = result.get('properties', {}).get('content', '')
            position = result.get('properties', {}).get('position_index', 'unknown')
            certainty = result.get('_additional', {}).get('certainty', 0.0)

            if content:
                context_parts.append(content)
                citations.append(CitationWithScore(
                    source_title="Plato",  # TODO: Extract from result
                    content=content[:5000],  # Extended preview as in chat_rag_clean.py
                    position=str(position),
                    relevance_score=certainty,
                    chunk_id=""  # TODO: Extract chunk_id if available
                ))

        context = "\n\n".join(context_parts)

        # Step 4: Generate response using LLM
        prompt = self._create_prompt(question, context)
        response = self.llm_service.generate_text(
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
        import re  # noqa: PLC0415
        response = re.sub(r"&[a-zA-Z0-9#]+;", "", response)
        response = re.sub(r"<[^>]+>", "", response)
        return response.strip()

    def _get_fallback_response(self, question: str) -> tuple[str, list[CitationWithScore]]:
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
