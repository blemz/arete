"""RAG system integration for document retrieval and citation linking."""

import reflex as rx
from typing import List, Dict, Optional, Any, Tuple
from ..state.document_state import DocumentState, Citation, DocumentMetadata
from ..state.chat_state import ChatState
import asyncio
import json


class RAGIntegrationState(rx.State):
    """State for RAG system integration with document viewer."""
    
    # RAG service connection status
    rag_connected: bool = False
    rag_error: str = ""
    
    # Document corpus management
    corpus_documents: List[Dict[str, Any]] = []
    indexed_documents: int = 0
    
    # Citation linking
    active_citations: List[str] = []  # Citation IDs currently highlighted
    citation_context: Dict[str, Any] = {}  # Additional context for citations
    
    # Search and retrieval
    semantic_search_results: List[Dict[str, Any]] = []
    entity_matches: List[Dict[str, Any]] = []
    
    async def initialize_rag_connection(self):
        """Initialize connection to RAG system."""
        try:
            # Connect to existing RAG services
            await self._connect_to_weaviate()
            await self._connect_to_neo4j()
            await self._load_corpus_metadata()
            self.rag_connected = True
            self.rag_error = ""
        except Exception as e:
            self.rag_connected = False
            self.rag_error = f"Failed to connect to RAG system: {str(e)}"
    
    async def _connect_to_weaviate(self):
        """Connect to Weaviate vector database."""
        # Implementation would connect to existing Weaviate instance
        # from src/arete/services/vector_service.py
        pass
    
    async def _connect_to_neo4j(self):
        """Connect to Neo4j knowledge graph."""
        # Implementation would connect to existing Neo4j instance
        # from src/arete/services/knowledge_graph_service.py
        pass
    
    async def _load_corpus_metadata(self):
        """Load document corpus metadata from RAG system."""
        # Implementation would query existing document store
        self.corpus_documents = await self._fetch_corpus_documents()
        self.indexed_documents = len(self.corpus_documents)
    
    async def _fetch_corpus_documents(self) -> List[Dict[str, Any]]:
        """Fetch document metadata from corpus."""
        # Mock implementation - would connect to actual RAG system
        return [
            {
                "id": "plato_apology_full",
                "title": "Apology",
                "author": "Plato", 
                "chunks": 47,
                "entities": 15,
                "word_count": 12843,
                "file_path": "data/processed/plato_apology.json"
            },
            {
                "id": "plato_charmides_full", 
                "title": "Charmides",
                "author": "Plato",
                "chunks": 32,
                "entities": 12,
                "word_count": 8967,
                "file_path": "data/processed/plato_charmides.json"
            }
        ]
    
    async def load_document_from_rag(self, document_id: str) -> Optional[DocumentMetadata]:
        """Load full document content from RAG system."""
        try:
            # Find document in corpus
            corpus_doc = next((d for d in self.corpus_documents if d["id"] == document_id), None)
            if not corpus_doc:
                return None
            
            # Load full content with citations
            content = await self._load_document_content(corpus_doc["file_path"])
            citations = await self._load_document_citations(document_id)
            
            # Convert to DocumentMetadata format
            return self._convert_to_document_metadata(corpus_doc, content, citations)
            
        except Exception as e:
            self.rag_error = f"Failed to load document: {str(e)}"
            return None
    
    async def _load_document_content(self, file_path: str) -> Dict[str, Any]:
        """Load document content from processed file."""
        # Implementation would load from actual file system
        # Mock data for now
        return {
            "paragraphs": [
                {
                    "id": "para_1",
                    "text": "When I heard this oracle, I thought to myself: What can the god mean?",
                    "position": 1,
                    "citations": ["cite_wisdom_1"]
                },
                {
                    "id": "para_2", 
                    "text": "The unexamined life is not worth living for a human being.",
                    "position": 2,
                    "citations": ["cite_examined_life"]
                }
            ],
            "sections": [
                {"id": "intro", "title": "Introduction", "level": 1, "position": 0},
                {"id": "defense", "title": "The Defense", "level": 1, "position": 50}
            ]
        }
    
    async def _load_document_citations(self, document_id: str) -> List[Citation]:
        """Load citations for document from knowledge graph."""
        # Implementation would query Neo4j for citations and entities
        return [
            Citation(
                id="cite_wisdom_1",
                text="wise",
                preview_text="Human wisdom is of little or no value...",
                full_text="I am conscious that I am not wise either much or little. What then does he mean by saying that I am the wisest?",
                author="Plato",
                work="Apology",
                section="21b",
                page="28",
                position=150
            ),
            Citation(
                id="cite_examined_life",
                text="examined life",
                preview_text="The unexamined life is not worth living...",
                full_text="The unexamined life is not worth living for a human being. This is what I have learned from the god.",
                author="Plato", 
                work="Apology",
                section="38a",
                page="42",
                position=850
            )
        ]
    
    def _convert_to_document_metadata(self, corpus_doc: Dict[str, Any], content: Dict[str, Any], citations: List[Citation]) -> DocumentMetadata:
        """Convert RAG data to DocumentMetadata format."""
        from ..state.document_state import DocumentSection, DocumentParagraph, DocumentContent
        
        # Convert sections
        sections = [
            DocumentSection(
                id=section["id"],
                title=section["title"], 
                level=section["level"],
                position=section["position"]
            )
            for section in content["sections"]
        ]
        
        # Convert paragraphs with citation linking
        paragraphs = []
        for para_data in content["paragraphs"]:
            # Parse paragraph text and insert citations
            para_content = self._parse_paragraph_with_citations(
                para_data["text"], 
                para_data.get("citations", []),
                citations
            )
            
            paragraphs.append(DocumentParagraph(
                id=para_data["id"],
                content=para_content,
                position=para_data["position"]
            ))
        
        return DocumentMetadata(
            id=corpus_doc["id"],
            title=corpus_doc["title"],
            author=corpus_doc["author"],
            date="399 BCE",  # Would come from metadata
            word_count=corpus_doc["word_count"],
            type="Dialogue",  # Would come from metadata
            description="",  # Would come from metadata
            sections=sections,
            paragraphs=paragraphs,
            citations=citations
        )
    
    def _parse_paragraph_with_citations(self, text: str, citation_ids: List[str], all_citations: List[Citation]) -> List[object]:
        """Parse paragraph text and insert citation objects."""
        from ..state.document_state import DocumentContent
        
        # Find citations that appear in this paragraph
        paragraph_citations = [c for c in all_citations if c.id in citation_ids]
        
        # Simple implementation - split text around citation terms
        content = []
        remaining_text = text
        
        for citation in paragraph_citations:
            # Find citation text in paragraph
            if citation.text in remaining_text:
                parts = remaining_text.split(citation.text, 1)
                
                # Add text before citation
                if parts[0]:
                    content.append(DocumentContent(parts[0], "text"))
                
                # Add citation
                content.append(DocumentContent(citation.text, "citation", citation_data=citation))
                
                # Continue with remaining text
                remaining_text = parts[1] if len(parts) > 1 else ""
        
        # Add any remaining text
        if remaining_text:
            content.append(DocumentContent(remaining_text, "text"))
        
        return content
    
    async def search_corpus_semantically(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic search across document corpus."""
        try:
            # Implementation would use existing vector search service
            # from src/arete/services/vector_service.py
            results = await self._vector_search(query, limit)
            self.semantic_search_results = results
            return results
        except Exception as e:
            self.rag_error = f"Semantic search failed: {str(e)}"
            return []
    
    async def _vector_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Execute vector similarity search."""
        # Mock implementation
        return [
            {
                "chunk_id": "chunk_42",
                "document_id": "plato_apology_full",
                "text": "The unexamined life is not worth living for a human being.",
                "similarity": 0.92,
                "position": 850,
                "metadata": {"section": "38a", "page": 42}
            },
            {
                "chunk_id": "chunk_15",
                "document_id": "plato_apology_full", 
                "text": "I am conscious that I am not wise either much or little.",
                "similarity": 0.87,
                "position": 150,
                "metadata": {"section": "21b", "page": 28}
            }
        ]
    
    async def find_related_entities(self, entity_name: str) -> List[Dict[str, Any]]:
        """Find entities related to the given entity in knowledge graph."""
        try:
            # Implementation would use existing Neo4j service
            # from src/arete/services/knowledge_graph_service.py
            entities = await self._knowledge_graph_query(entity_name)
            self.entity_matches = entities
            return entities
        except Exception as e:
            self.rag_error = f"Entity search failed: {str(e)}"
            return []
    
    async def _knowledge_graph_query(self, entity_name: str) -> List[Dict[str, Any]]:
        """Query knowledge graph for related entities."""
        # Mock implementation
        return [
            {
                "entity_id": "socrates",
                "name": "Socrates",
                "type": "Person",
                "relation": "MENTIONED_WITH",
                "documents": ["plato_apology_full", "plato_charmides_full"]
            },
            {
                "entity_id": "wisdom",
                "name": "Wisdom", 
                "type": "Concept",
                "relation": "DISCUSSES",
                "documents": ["plato_apology_full"]
            }
        ]
    
    def highlight_citations_for_query(self, query: str):
        """Highlight relevant citations based on chat query."""
        # Find citations that match query semantically
        # This would integrate with chat state to highlight relevant passages
        relevant_citation_ids = self._find_relevant_citations(query)
        self.active_citations = relevant_citation_ids
    
    def _find_relevant_citations(self, query: str) -> List[str]:
        """Find citation IDs relevant to query."""
        # Implementation would use semantic similarity
        # For now, simple keyword matching
        relevant = []
        query_lower = query.lower()
        
        # Check against semantic search results
        for result in self.semantic_search_results:
            if any(word in result["text"].lower() for word in query_lower.split()):
                # Find corresponding citation
                # This would be more sophisticated in production
                relevant.append(f"cite_{result['chunk_id']}")
        
        return relevant
    
    def clear_citation_highlighting(self):
        """Clear all citation highlighting."""
        self.active_citations = []
        self.citation_context = {}
    
    async def sync_with_chat_state(self, chat_state: ChatState):
        """Sync document viewer with chat conversation."""
        # Get last chat message for context
        if chat_state.messages:
            last_message = chat_state.messages[-1]
            if last_message.role == "user":
                # Highlight relevant citations for user query
                await self.highlight_citations_for_query(last_message.content)
                
                # Load related documents if needed
                await self._load_documents_for_query(last_message.content)
    
    async def _load_documents_for_query(self, query: str):
        """Load documents relevant to query."""
        # Perform semantic search to find relevant documents
        search_results = await self.search_corpus_semantically(query, 3)
        
        # Get unique document IDs from results
        doc_ids = list(set(result["document_id"] for result in search_results))
        
        # Update DocumentState with suggestions for relevant documents
        # This would trigger UI updates to suggest documents to open
        pass


def rag_status_indicator() -> rx.Component:
    """RAG connection status indicator."""
    return rx.cond(
        RAGIntegrationState.rag_connected,
        rx.hstack(
            rx.icon("database", color="green.500", size="sm"),
            rx.text("RAG Connected", color="green.600", font_size="sm"),
            rx.text(f"{RAGIntegrationState.indexed_documents} documents indexed", color="gray.500", font_size="xs"),
            spacing="2"
        ),
        rx.hstack(
            rx.icon("database", color="red.500", size="sm"),
            rx.text("RAG Disconnected", color="red.600", font_size="sm"),
            rx.cond(
                RAGIntegrationState.rag_error != "",
                rx.tooltip(
                    rx.icon("info", color="red.400", size="xs"),
                    label=RAGIntegrationState.rag_error
                )
            ),
            spacing="2"
        )
    )


def document_suggestions() -> rx.Component:
    """Document suggestions based on current chat context."""
    return rx.cond(
        RAGIntegrationState.semantic_search_results.length() > 0,
        rx.box(
            rx.heading("Relevant Documents", size="sm", color="gray.700"),
            rx.vstack(
                rx.foreach(
                    RAGIntegrationState.semantic_search_results[:3],  # Top 3 results
                    lambda result: rx.box(
                        rx.vstack(
                            rx.text(
                                result["document_id"].replace("_", " ").title(),
                                font_weight="bold",
                                color="blue.600"
                            ),
                            rx.text(
                                result["text"][:100] + "...",
                                font_size="sm",
                                color="gray.600"
                            ),
                            rx.text(
                                f"Relevance: {(result['similarity'] * 100):.0f}%",
                                font_size="xs",
                                color="gray.500"
                            ),
                            rx.button(
                                "Open Document",
                                size="xs",
                                variant="outline",
                                on_click=lambda: DocumentState.load_document(result["document_id"])
                            ),
                            align_items="start",
                            spacing="1"
                        ),
                        padding="3",
                        border="1px solid #e2e8f0",
                        border_radius="md",
                        _hover={"border_color": "blue.300"}
                    )
                ),
                spacing="2",
                width="100%"
            ),
            padding="4",
            background="blue.50",
            border_radius="md",
            margin_bottom="4"
        )
    )