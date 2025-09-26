import reflex as rx
import asyncio
from typing import List, Dict, Optional, Any, AsyncGenerator
from datetime import datetime
import json
import logging
from uuid import uuid4

# Import existing RAG services
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from arete.services.llm_service import LLMService, LLMServiceFactory
from arete.services.retrieval_service import RetrievalService
from arete.services.embedding_service import get_embedding_service
from arete.database.weaviate_client import WeaviateClient
from arete.database.neo4j_client import Neo4jClient
from arete.core.config import get_settings
from arete.models.chat_models import Message, ConversationHistory, Citation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageType:
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system" 
    ERROR = "error"


class ChatMessage(rx.Base):
    """Enhanced chat message model with RAG integration"""
    id: str
    content: str
    message_type: str
    timestamp: datetime
    citations: List[Dict[str, Any]] = []
    is_loading: bool = False
    error_message: Optional[str] = None
    token_count: Optional[int] = None
    processing_time: Optional[float] = None
    retrieval_stats: Optional[Dict[str, Any]] = None


class ConversationMetadata(rx.Base):
    """Conversation metadata for persistence"""
    id: str
    title: str
    created_at: datetime
    last_updated: datetime
    message_count: int
    total_tokens: int
    topics: List[str] = []


class RAGChatState(rx.State):
    """Advanced state management for RAG-integrated chat interface"""
    
    # Core chat state
    messages: List[ChatMessage] = []
    current_input: str = ""
    is_processing: bool = False
    conversation_metadata: ConversationMetadata = None
    
    # RAG service instances - lazy loaded
    _services_initialized: bool = False
    _retrieval_service: Optional[RetrievalService] = None
    _llm_service: Optional[LLMService] = None
    _weaviate_client: Optional[WeaviateClient] = None
    _neo4j_client: Optional[Neo4jClient] = None
    
    # UI state management
    show_citations: bool = True
    show_retrieval_stats: bool = False
    auto_scroll: bool = True
    typing_indicator: bool = False
    selected_citation_id: Optional[str] = None
    citation_modal_open: bool = False
    
    # Search and filtering
    search_query: str = ""
    search_mode: str = "content"  # content, citations, metadata
    filtered_message_ids: List[str] = []
    
    # Performance and limits
    max_messages_per_conversation: int = 200
    max_context_messages: int = 10
    citation_preview_length: int = 5000
    retrieval_limit: int = 5
    similarity_threshold: float = 0.7
    
    # Conversation management
    saved_conversations: List[ConversationMetadata] = []
    current_conversation_id: str = ""
    
    # Export and settings
    export_format: str = "json"  # json, markdown, text
    include_citations_in_export: bool = True
    theme: str = "dark"
    
    # Performance monitoring
    last_query_time: Optional[float] = None
    average_response_time: float = 0.0
    total_queries: int = 0
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initialize_conversation()
    
    def _initialize_conversation(self):
        """Initialize a new conversation"""
        self.current_conversation_id = str(uuid4())
        self.conversation_metadata = ConversationMetadata(
            id=self.current_conversation_id,
            title="New Conversation",
            created_at=datetime.now(),
            last_updated=datetime.now(),
            message_count=0,
            total_tokens=0
        )
    
    @rx.var
    def filtered_messages(self) -> List[ChatMessage]:
        """Get messages filtered by search query"""
        if not self.search_query:
            return self.messages
        
        query_lower = self.search_query.lower()
        filtered = []
        
        for msg in self.messages:
            match = False
            
            if self.search_mode == "content":
                match = query_lower in msg.content.lower()
            elif self.search_mode == "citations":
                match = any(
                    query_lower in citation.get("text", "").lower() or 
                    query_lower in citation.get("source", "").lower()
                    for citation in msg.citations
                )
            elif self.search_mode == "metadata":
                match = (
                    query_lower in msg.message_type.lower() or
                    query_lower in msg.timestamp.strftime("%Y-%m-%d %H:%M").lower()
                )
            
            if match:
                filtered.append(msg)
        
        return filtered
    
    @rx.var
    def conversation_stats(self) -> Dict[str, Any]:
        """Get current conversation statistics"""
        if not self.messages:
            return {}
        
        user_msgs = [m for m in self.messages if m.message_type == MessageType.USER]
        assistant_msgs = [m for m in self.messages if m.message_type == MessageType.ASSISTANT]
        
        total_tokens = sum(m.token_count for m in self.messages if m.token_count)
        avg_response_time = sum(m.processing_time for m in assistant_msgs if m.processing_time) / len(assistant_msgs) if assistant_msgs else 0
        
        return {
            "total_messages": len(self.messages),
            "user_messages": len(user_msgs),
            "assistant_messages": len(assistant_msgs),
            "total_tokens": total_tokens,
            "average_response_time": avg_response_time,
            "conversation_duration": (datetime.now() - self.conversation_metadata.created_at).total_seconds() if self.conversation_metadata else 0
        }
    
    @rx.var
    def has_messages(self) -> bool:
        return len(self.messages) > 0
    
    @rx.var
    def can_regenerate(self) -> bool:
        """Check if last response can be regenerated"""
        return (
            len(self.messages) >= 2 and 
            self.messages[-1].message_type == MessageType.ASSISTANT and
            not self.is_processing
        )
    
    @rx.var
    def selected_citation(self) -> Optional[Dict[str, Any]]:
        """Get currently selected citation"""
        if not self.selected_citation_id:
            return None
        
        for message in self.messages:
            for citation in message.citations:
                if citation.get("id") == self.selected_citation_id:
                    return citation
        return None
    
    # Input and UI state methods
    def set_input(self, value: str):
        self.current_input = value
    
    def set_search_query(self, query: str):
        self.search_query = query
    
    def set_search_mode(self, mode: str):
        self.search_mode = mode
    
    def clear_search(self):
        self.search_query = ""
        self.filtered_message_ids = []
    
    def toggle_citations(self):
        self.show_citations = not self.show_citations
    
    def toggle_retrieval_stats(self):
        self.show_retrieval_stats = not self.show_retrieval_stats
    
    def toggle_auto_scroll(self):
        self.auto_scroll = not self.auto_scroll
    
    def open_citation_modal(self, citation_id: str):
        self.selected_citation_id = citation_id
        self.citation_modal_open = True
    
    def close_citation_modal(self):
        self.citation_modal_open = False
        self.selected_citation_id = None
    
    # Service initialization
    async def _initialize_services(self):
        """Initialize RAG services lazily"""
        if self._services_initialized:
            return
        
        try:
            logger.info("Initializing RAG services...")
            settings = get_settings()
            
            # Initialize database clients
            self._weaviate_client = WeaviateClient()
            self._neo4j_client = Neo4jClient()
            
            # Initialize embedding service
            embedding_service = get_embedding_service()
            
            # Initialize retrieval service
            self._retrieval_service = RetrievalService(
                weaviate_client=self._weaviate_client,
                neo4j_client=self._neo4j_client,
                embedding_service=embedding_service
            )
            
            # Initialize LLM service
            self._llm_service = LLMServiceFactory.create_service(settings.kg_llm_provider)
            
            self._services_initialized = True
            logger.info("RAG services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG services: {e}")
            raise
    
    # Message management
    def add_message(
        self, 
        content: str, 
        message_type: str, 
        citations: List[Dict[str, Any]] = None,
        **kwargs
    ) -> ChatMessage:
        """Add a new message to the conversation"""
        
        message = ChatMessage(
            id=str(uuid4()),
            content=content,
            message_type=message_type,
            timestamp=datetime.now(),
            citations=citations or [],
            **kwargs
        )
        
        # Maintain message limit
        if len(self.messages) >= self.max_messages_per_conversation:
            self.messages = self.messages[-(self.max_messages_per_conversation-1):]
        
        self.messages.append(message)
        
        # Update conversation metadata
        if self.conversation_metadata:
            self.conversation_metadata.message_count = len(self.messages)
            self.conversation_metadata.last_updated = datetime.now()
            if message.token_count:
                self.conversation_metadata.total_tokens += message.token_count
        
        return message
    
    def update_message(self, message_id: str, **updates):
        """Update an existing message"""
        for message in self.messages:
            if message.id == message_id:
                for key, value in updates.items():
                    setattr(message, key, value)
                break
    
    def remove_message(self, message_id: str):
        """Remove a message from the conversation"""
        self.messages = [msg for msg in self.messages if msg.id != message_id]
        
        if self.conversation_metadata:
            self.conversation_metadata.message_count = len(self.messages)
            self.conversation_metadata.last_updated = datetime.now()
    
    # Core RAG processing
    async def process_query_with_rag(self, query: str) -> Dict[str, Any]:
        """Process query through RAG pipeline"""
        start_time = datetime.now()
        
        try:
            await self._initialize_services()
            
            # Get conversation context
            context_messages = []
            recent_messages = self.messages[-self.max_context_messages:] if self.messages else []
            
            for msg in recent_messages:
                if not msg.is_loading and msg.message_type in [MessageType.USER, MessageType.ASSISTANT]:
                    context_messages.append({
                        "role": "user" if msg.message_type == MessageType.USER else "assistant",
                        "content": msg.content
                    })
            
            # Retrieve relevant content
            retrieval_result = await self._retrieval_service.retrieve(
                query=query,
                limit=self.retrieval_limit,
                similarity_threshold=self.similarity_threshold
            )
            
            # Process citations
            citations = []
            context_chunks = []
            
            for i, chunk_result in enumerate(retrieval_result.chunks):
                citation = {
                    "id": str(uuid4()),
                    "text": chunk_result.content[:self.citation_preview_length],
                    "full_text": chunk_result.content,
                    "source": chunk_result.metadata.get('source', 'Unknown'),
                    "position": chunk_result.metadata.get('position', 0),
                    "relevance_score": chunk_result.score,
                    "chunk_id": chunk_result.id,
                    "page": chunk_result.metadata.get('page'),
                    "section": chunk_result.metadata.get('section'),
                    "entities": chunk_result.metadata.get('entities', [])
                }
                citations.append(citation)
                context_chunks.append(chunk_result.content)
            
            # Generate response
            rag_context = "\n\n".join(context_chunks) if context_chunks else ""
            
            response = await self._llm_service.generate_response(
                query=query,
                context=rag_context,
                conversation_history=context_messages
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Prepare retrieval statistics
            retrieval_stats = {
                "chunks_retrieved": len(retrieval_result.chunks),
                "entities_found": len(retrieval_result.entities) if hasattr(retrieval_result, 'entities') else 0,
                "avg_relevance": sum(chunk.score for chunk in retrieval_result.chunks) / len(retrieval_result.chunks) if retrieval_result.chunks else 0,
                "processing_time": processing_time,
                "context_length": len(rag_context),
                "query_complexity": len(query.split())
            }
            
            return {
                "response": response,
                "citations": citations,
                "retrieval_stats": retrieval_stats,
                "processing_time": processing_time,
                "token_count": len(response.split()) * 1.3  # Rough token estimate
            }
            
        except Exception as e:
            logger.error(f"Error in RAG processing: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "response": f"I apologize, but I encountered an error processing your question: {str(e)}",
                "citations": [],
                "retrieval_stats": {"error": str(e), "processing_time": processing_time},
                "processing_time": processing_time,
                "error": str(e)
            }
    
    # Main chat actions
    async def send_message(self):
        """Send user message and get RAG response"""
        if not self.current_input.strip() or self.is_processing:
            return
        
        user_query = self.current_input.strip()
        self.current_input = ""
        self.is_processing = True
        self.typing_indicator = True
        
        try:
            # Add user message
            user_message = self.add_message(user_query, MessageType.USER)
            
            # Add loading assistant message
            assistant_message = self.add_message("", MessageType.ASSISTANT, is_loading=True)
            
            # Process through RAG
            result = await self.process_query_with_rag(user_query)
            
            # Update assistant message
            self.update_message(
                assistant_message.id,
                content=result["response"],
                citations=result["citations"],
                is_loading=False,
                processing_time=result["processing_time"],
                token_count=result.get("token_count"),
                retrieval_stats=result["retrieval_stats"],
                error_message=result.get("error")
            )
            
            # Update performance stats
            self.total_queries += 1
            self.last_query_time = result["processing_time"]
            self.average_response_time = (
                (self.average_response_time * (self.total_queries - 1) + result["processing_time"]) 
                / self.total_queries
            )
            
            # Auto-generate conversation title if first exchange
            if len(self.messages) == 2 and self.conversation_metadata.title == "New Conversation":
                # Use first few words of user query as title
                title_words = user_query.split()[:5]
                self.conversation_metadata.title = " ".join(title_words) + ("..." if len(title_words) == 5 else "")
            
        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            # Update the loading message with error
            if len(self.messages) > 0 and self.messages[-1].is_loading:
                self.update_message(
                    self.messages[-1].id,
                    content="I'm sorry, I encountered an error processing your request. Please try again.",
                    message_type=MessageType.ERROR,
                    error_message=str(e),
                    is_loading=False
                )
        
        finally:
            self.is_processing = False
            self.typing_indicator = False
    
    async def regenerate_last_response(self):
        """Regenerate the last assistant response"""
        if not self.can_regenerate:
            return
        
        # Find the user message that prompted the last response
        user_message = None
        for i in range(len(self.messages) - 2, -1, -1):
            if self.messages[i].message_type == MessageType.USER:
                user_message = self.messages[i]
                break
        
        if not user_message:
            return
        
        # Remove the last assistant message
        self.messages = self.messages[:-1]
        
        # Set input and regenerate
        self.current_input = user_message.content
        await self.send_message()
    
    # Message actions
    async def copy_message_content(self, message_id: str):
        """Copy message content (simulation - actual clipboard needs browser API)"""
        message = next((msg for msg in self.messages if msg.id == message_id), None)
        if message:
            # In a real implementation, this would use the browser clipboard API
            logger.info(f"Copied message: {message.content[:50]}...")
            return rx.toast.info("Message copied to clipboard")
    
    def branch_conversation_from_message(self, message_id: str):
        """Create a new conversation branch from a specific message"""
        message_index = next(
            (i for i, msg in enumerate(self.messages) if msg.id == message_id), 
            None
        )
        
        if message_index is not None:
            # Create new conversation with messages up to the branch point
            old_conversation = self.conversation_metadata
            self._initialize_conversation()
            
            # Copy messages up to branch point
            self.messages = self.messages[:message_index + 1].copy()
            
            # Update metadata
            self.conversation_metadata.title = f"Branch from: {old_conversation.title}"
            self.conversation_metadata.message_count = len(self.messages)
    
    # Conversation management
    def clear_conversation(self):
        """Clear current conversation"""
        if self.conversation_metadata:
            # Save current conversation before clearing
            self.saved_conversations.append(self.conversation_metadata)
        
        self.messages = []
        self._initialize_conversation()
        self.search_query = ""
        self.selected_citation_id = None
    
    def load_conversation(self, conversation_id: str):
        """Load a saved conversation"""
        # This would integrate with persistent storage in a real implementation
        saved_conv = next(
            (conv for conv in self.saved_conversations if conv.id == conversation_id), 
            None
        )
        
        if saved_conv:
            self.current_conversation_id = conversation_id
            self.conversation_metadata = saved_conv
            # In real implementation, load messages from storage
    
    def delete_conversation(self, conversation_id: str):
        """Delete a saved conversation"""
        self.saved_conversations = [
            conv for conv in self.saved_conversations 
            if conv.id != conversation_id
        ]
    
    # Export functionality
    def export_conversation(self) -> str:
        """Export conversation in specified format"""
        if self.export_format == "json":
            return self._export_as_json()
        elif self.export_format == "markdown":
            return self._export_as_markdown()
        elif self.export_format == "text":
            return self._export_as_text()
        else:
            return self._export_as_json()
    
    def _export_as_json(self) -> str:
        """Export as JSON format"""
        export_data = {
            "conversation_id": self.current_conversation_id,
            "metadata": {
                "title": self.conversation_metadata.title,
                "created_at": self.conversation_metadata.created_at.isoformat(),
                "last_updated": self.conversation_metadata.last_updated.isoformat(),
                "message_count": len(self.messages),
                "total_tokens": self.conversation_metadata.total_tokens
            },
            "messages": []
        }
        
        for msg in self.messages:
            msg_data = {
                "id": msg.id,
                "content": msg.content,
                "type": msg.message_type,
                "timestamp": msg.timestamp.isoformat(),
                "processing_time": msg.processing_time,
                "token_count": msg.token_count
            }
            
            if self.include_citations_in_export and msg.citations:
                msg_data["citations"] = [
                    {
                        "text": cite["text"],
                        "source": cite["source"],
                        "relevance_score": cite["relevance_score"],
                        "position": cite.get("position")
                    }
                    for cite in msg.citations
                ]
            
            if self.show_retrieval_stats and msg.retrieval_stats:
                msg_data["retrieval_stats"] = msg.retrieval_stats
            
            export_data["messages"].append(msg_data)
        
        return json.dumps(export_data, indent=2, default=str)
    
    def _export_as_markdown(self) -> str:
        """Export as Markdown format"""
        lines = [
            f"# {self.conversation_metadata.title}",
            f"*Created: {self.conversation_metadata.created_at.strftime('%Y-%m-%d %H:%M')}*",
            f"*Messages: {len(self.messages)} | Tokens: {self.conversation_metadata.total_tokens}*",
            "",
        ]
        
        for msg in self.messages:
            if msg.message_type == MessageType.USER:
                lines.extend([f"## User ({msg.timestamp.strftime('%H:%M')})", msg.content, ""])
            elif msg.message_type == MessageType.ASSISTANT:
                lines.extend([f"## Assistant ({msg.timestamp.strftime('%H:%M')})", msg.content])
                
                if self.include_citations_in_export and msg.citations:
                    lines.append("\n### Sources:")
                    for cite in msg.citations:
                        lines.append(f"- **{cite['source']}** ({cite['relevance_score']:.1%})")
                        lines.append(f"  > {cite['text'][:200]}...")
                
                lines.append("")
        
        return "\n".join(lines)
    
    def _export_as_text(self) -> str:
        """Export as plain text format"""
        lines = [
            f"Arete Conversation: {self.conversation_metadata.title}",
            f"Created: {self.conversation_metadata.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"Messages: {len(self.messages)} | Tokens: {self.conversation_metadata.total_tokens}",
            "=" * 50,
            ""
        ]
        
        for msg in self.messages:
            speaker = msg.message_type.title()
            timestamp = msg.timestamp.strftime('%H:%M')
            lines.extend([
                f"{speaker} [{timestamp}]:",
                msg.content,
                ""
            ])
            
            if self.include_citations_in_export and msg.citations:
                lines.append("Sources:")
                for cite in msg.citations:
                    lines.append(f"  - {cite['source']} ({cite['relevance_score']:.1%})")
                lines.append("")
        
        return "\n".join(lines)
    
    # Settings management
    def update_settings(self, **settings):
        """Update chat settings"""
        for key, value in settings.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def reset_settings(self):
        """Reset settings to defaults"""
        self.show_citations = True
        self.show_retrieval_stats = False
        self.auto_scroll = True
        self.max_context_messages = 10
        self.retrieval_limit = 5
        self.similarity_threshold = 0.7
        self.export_format = "json"
        self.include_citations_in_export = True