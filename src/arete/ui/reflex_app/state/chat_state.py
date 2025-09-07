"""Chat state management with split-view integration."""

import reflex as rx
from typing import List, Dict, Any, Optional
from datetime import datetime


class ChatMessage(rx.Base):
    """Chat message model."""
    id: str
    content: str
    role: str  # "user" or "assistant"
    timestamp: datetime
    citations: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}


class ChatState(rx.State):
    """State management for chat interface with split-view coordination."""
    
    # Chat messages
    messages: List[ChatMessage] = []
    current_input: str = ""
    is_loading: bool = False
    
    # Conversation management
    conversation_id: Optional[str] = None
    conversation_title: str = "New Conversation"
    
    # Citation context
    active_citation_context: Optional[str] = None
    citation_highlights: List[str] = []
    
    # Search context
    search_context: str = ""
    search_results: List[Dict[str, Any]] = []
    
    # Compact mode for split view
    compact_mode: bool = False
    
    # Auto-scroll behavior
    auto_scroll_enabled: bool = True
    scroll_position: float = 0.0
    
    # Performance optimization
    message_limit: int = 100
    
    def send_message(self, message: str):
        """Send a chat message."""
        if not message.strip():
            return
        
        # Create user message
        user_message = ChatMessage(
            id=f"msg_{len(self.messages)}_{datetime.now().timestamp()}",
            content=message.strip(),
            role="user",
            timestamp=datetime.now()
        )
        
        self.messages.append(user_message)
        self.current_input = ""
        self.is_loading = True
        
        # Process message asynchronously with RAG system
        import asyncio
        asyncio.create_task(self._process_message_async(message))
    
    async def _process_message_async(self, message: str):
        """Process message with RAG system."""
        try:
            from ..services.chat_service import get_chat_service
            
            # Get chat service and process message
            chat_service = get_chat_service()
            result = await chat_service.send_message(message)
            
            # Create assistant response with real RAG data
            assistant_message = ChatMessage(
                id=f"msg_{len(self.messages)}_{datetime.now().timestamp()}",
                content=result.get("response", "I apologize, but I couldn't generate a response."),
                role="assistant",
                timestamp=datetime.now(),
                citations=[
                    {
                        "id": f"cite_{i}",
                        "document_id": cite.get("document_id", "unknown"),
                        "text": cite.get("content", ""),
                        "position": cite.get("position", 0),
                        "relevance_score": cite.get("score", 0.0)
                    }
                    for i, cite in enumerate(result.get("citations", []))
                ],
                metadata={
                    "entities": result.get("entities", []),
                    "success": result.get("success", False)
                }
            )
            
            self.messages.append(assistant_message)
            
        except Exception as e:
            # Fallback error message
            error_message = ChatMessage(
                id=f"msg_{len(self.messages)}_{datetime.now().timestamp()}",
                content=f"I apologize, but I encountered an error: {str(e)}",
                role="assistant",
                timestamp=datetime.now(),
                citations=[],
                metadata={"error": True}
            )
            self.messages.append(error_message)
        
        finally:
            self.is_loading = False
            
            # Trigger auto-scroll if enabled
            if self.auto_scroll_enabled:
                self.scroll_to_bottom()
    
    def set_citation_context(self, citation_id: str):
        """Set citation context from document panel interaction."""
        self.active_citation_context = citation_id
        
        # Find related messages with this citation
        related_messages = [
            msg for msg in self.messages
            if any(cite["id"] == citation_id for cite in msg.citations)
        ]
        
        if related_messages:
            # Scroll to the most recent related message
            last_message = related_messages[-1]
            self.scroll_to_message(last_message.id)
    
    def set_search_context(self, query: str):
        """Set search context from document panel search."""
        self.search_context = query
        
        # Highlight relevant messages
        self.search_results = [
            {
                "message_id": msg.id,
                "relevance": self._calculate_relevance(msg.content, query),
                "highlights": self._extract_highlights(msg.content, query)
            }
            for msg in self.messages
            if self._calculate_relevance(msg.content, query) > 0.3
        ]
    
    def _calculate_relevance(self, text: str, query: str) -> float:
        """Calculate relevance score between text and query."""
        # Simple relevance calculation (would use proper semantic similarity)
        query_terms = query.lower().split()
        text_lower = text.lower()
        
        matches = sum(1 for term in query_terms if term in text_lower)
        return matches / len(query_terms) if query_terms else 0.0
    
    def _extract_highlights(self, text: str, query: str) -> List[Dict[str, Any]]:
        """Extract highlight positions for search query."""
        highlights = []
        query_terms = query.lower().split()
        text_lower = text.lower()
        
        for term in query_terms:
            start = 0
            while True:
                pos = text_lower.find(term, start)
                if pos == -1:
                    break
                highlights.append({
                    "start": pos,
                    "end": pos + len(term),
                    "text": text[pos:pos + len(term)]
                })
                start = pos + 1
        
        return highlights
    
    def scroll_to_bottom(self):
        """Scroll chat to bottom."""
        self.scroll_position = 1.0
    
    def scroll_to_message(self, message_id: str):
        """Scroll to specific message."""
        message_index = next(
            (i for i, msg in enumerate(self.messages) if msg.id == message_id),
            None
        )
        
        if message_index is not None and len(self.messages) > 0:
            self.scroll_position = message_index / len(self.messages)
    
    def toggle_compact_mode(self):
        """Toggle compact mode for split view."""
        self.compact_mode = not self.compact_mode
    
    def set_compact_mode(self, compact: bool):
        """Set compact mode state."""
        self.compact_mode = compact
    
    def clear_conversation(self):
        """Clear current conversation."""
        self.messages.clear()
        self.conversation_id = None
        self.conversation_title = "New Conversation"
        self.active_citation_context = None
        self.citation_highlights.clear()
        self.search_context = ""
        self.search_results.clear()
    
    def delete_message(self, message_id: str):
        """Delete a specific message."""
        self.messages = [msg for msg in self.messages if msg.id != message_id]
    
    def regenerate_response(self, message_id: str):
        """Regenerate response for a specific message."""
        message_index = next(
            (i for i, msg in enumerate(self.messages) if msg.id == message_id),
            None
        )
        
        if message_index is not None and message_index > 0:
            # Find the user message that prompted this response
            user_message = self.messages[message_index - 1]
            if user_message.role == "user":
                # Remove the old response and regenerate
                self.messages = self.messages[:message_index]
                self._process_message_async(user_message.content)
    
    def add_citation_highlight(self, citation_id: str):
        """Add citation highlight."""
        if citation_id not in self.citation_highlights:
            self.citation_highlights.append(citation_id)
    
    def remove_citation_highlight(self, citation_id: str):
        """Remove citation highlight."""
        if citation_id in self.citation_highlights:
            self.citation_highlights.remove(citation_id)
    
    def clear_citation_highlights(self):
        """Clear all citation highlights."""
        self.citation_highlights.clear()
    
    def export_conversation(self) -> str:
        """Export conversation as formatted text."""
        export_lines = [f"# {self.conversation_title}", ""]
        
        for message in self.messages:
            role_prefix = "**User:**" if message.role == "user" else "**Assistant:**"
            export_lines.append(f"{role_prefix} {message.content}")
            
            if message.citations:
                export_lines.append("\n**Citations:**")
                for cite in message.citations:
                    export_lines.append(f"- {cite['text'][:100]}...")
            
            export_lines.append("")
        
        return "\n".join(export_lines)
    
    # Computed properties
    
    @rx.var
    def message_count(self) -> int:
        """Get total message count."""
        return len(self.messages)
    
    @rx.var
    def user_message_count(self) -> int:
        """Get user message count."""
        return len([msg for msg in self.messages if msg.role == "user"])
    
    @rx.var
    def assistant_message_count(self) -> int:
        """Get assistant message count."""
        return len([msg for msg in self.messages if msg.role == "assistant"])
    
    @rx.var
    def has_messages(self) -> bool:
        """Check if conversation has messages."""
        return len(self.messages) > 0
    
    @rx.var
    def latest_message(self) -> Optional[ChatMessage]:
        """Get latest message."""
        return self.messages[-1] if self.messages else None
    
    @rx.var
    def citation_count(self) -> int:
        """Get total citation count across all messages."""
        return sum(len(msg.citations) for msg in self.messages)
    
    @rx.var
    def search_result_count(self) -> int:
        """Get search result count."""
        return len(self.search_results)
    
    @rx.var
    def is_at_message_limit(self) -> bool:
        """Check if at message limit."""
        return len(self.messages) >= self.message_limit