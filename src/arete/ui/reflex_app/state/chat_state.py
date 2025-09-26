"""
Advanced Chat State for Reflex UI with RAG Integration

Provides comprehensive chat functionality with direct RAG pipeline integration,
citation management, and advanced features.
"""

import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime
import reflex as rx

from services.rag_service import get_rag_service
from src.arete.data.models import ChatMessage, CitationWithScore

logger = logging.getLogger(__name__)

class ChatState(rx.State):
    """Advanced chat state with full RAG integration."""
    
    # Chat messages
    messages: List[ChatMessage] = []
    current_message: str = ""
    is_loading: bool = False
    
    # Citations and context
    current_citations: List[CitationWithScore] = []
    selected_citation: Optional[CitationWithScore] = None
    show_citation_modal: bool = False
    
    # Chat history and search
    chat_history: List[Dict] = []
    search_query: str = ""
    filtered_messages: List[ChatMessage] = []
    
    # UI state
    chat_panel_width: str = "60%"
    document_panel_width: str = "40%"
    show_document_panel: bool = True
    
    # Analytics
    response_time: Optional[float] = None
    rag_status: str = "ready"  # ready, processing, error, unavailable
    
    async def send_message(self):
        """Send a message and get RAG response asynchronously."""
        if not self.current_message.strip():
            return
        
        # Add user message to chat history for display
        user_chat_msg = {
            "content": self.current_message,
            "is_user": True,
            "timestamp": datetime.now().strftime("%H:%M")
        }
        self.chat_history.append(user_chat_msg)
        
        # Clear input and set loading
        query = self.current_message
        self.current_message = ""
        self.is_loading = True
        self.rag_status = "processing"
        self.current_citations = []
        
        try:
            start_time = datetime.now()
            
            # Get RAG service and response
            rag_service = await get_rag_service()
            response_text, citations = await rag_service.get_rag_response(query)
            
            # Calculate response time
            self.response_time = (datetime.now() - start_time).total_seconds()
            
            # Parse and format the response using ResponseParser
            from ..components.response_parser import ResponseParser
            parsed_response = ResponseParser.parse_response(response_text)
            
            # Create structured markdown response with sections
            formatted_content = self._format_structured_response(parsed_response)
            
            # Add assistant message to chat history for display
            assistant_chat_msg = {
                "content": formatted_content,
                "is_user": False,
                "timestamp": datetime.now().strftime("%H:%M")
            }
            self.chat_history.append(assistant_chat_msg)
            
            # Store original message objects
            user_msg = ChatMessage(
                role="user",
                content=query,
                timestamp=datetime.now(),
                citations=[]
            )
            assistant_msg = ChatMessage(
                role="assistant",
                content=response_text,
                timestamp=datetime.now(),
                citations=citations
            )
            self.messages.extend([user_msg, assistant_msg])
            self.current_citations = citations
            self.rag_status = "ready"
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            error_chat_msg = {
                "content": "I apologize, but I encountered an error processing your question. Please try again.",
                "is_user": False,
                "timestamp": datetime.now().strftime("%H:%M")
            }
            self.chat_history.append(error_chat_msg)
            self.rag_status = "error"
            
        finally:
            self.is_loading = False
    
    def _format_structured_response(self, parsed_response) -> str:
        """Format parsed response into structured markdown."""
        sections = []
        
        if parsed_response.direct_answer:
            sections.append(f"## 🏛️ Arete Response\n\n{parsed_response.direct_answer}")
        
        if parsed_response.detailed_explanation:
            sections.append(f"## Summary of the accusations (plain language)\n\n{parsed_response.detailed_explanation}")
        
        if parsed_response.broader_connections:
            sections.append(f"## Key terms explained simply\n\n{parsed_response.broader_connections}")
        
        if parsed_response.references:
            sections.append(f"## Citations\n\n{parsed_response.references}")
        
        # If no structured sections found, use the raw response
        if not sections and parsed_response.raw_response:
            return f"## 🏛️ Arete Response\n\n{parsed_response.raw_response}"
        
        return "\n\n".join(sections) if sections else "I apologize, but I couldn't format this response properly."
    
    def update_message(self, value: str):
        """Update the current message input."""
        self.current_message = value
    
    def clear_chat(self):
        """Clear all chat messages and state."""
        self.messages = []
        self.current_citations = []
        self.selected_citation = None
        self.show_citation_modal = False
        self.rag_status = "ready"
        self.response_time = None
    
    def select_citation(self, citation: CitationWithScore):
        """Select a citation for detailed view."""
        self.selected_citation = citation
        self.show_citation_modal = True
    
    def close_citation_modal(self):
        """Close the citation detail modal."""
        self.show_citation_modal = False
        self.selected_citation = None
    
    def toggle_document_panel(self):
        """Toggle the document panel visibility."""
        if self.show_document_panel:
            self.show_document_panel = False
            self.chat_panel_width = "100%"
            self.document_panel_width = "0%"
        else:
            self.show_document_panel = True
            self.chat_panel_width = "60%"
            self.document_panel_width = "40%"
    
    def resize_panels(self, chat_width: str, doc_width: str):
        """Resize the chat and document panels."""
        self.chat_panel_width = chat_width
        self.document_panel_width = doc_width
    
    def search_messages(self, query: str):
        """Search through chat messages."""
        self.search_query = query
        if not query:
            self.filtered_messages = self.messages
            return
        
        query_lower = query.lower()
        self.filtered_messages = [
            msg for msg in self.messages
            if query_lower in msg.content.lower()
        ]
    
    def get_chat_analytics(self) -> Dict:
        """Get chat analytics data."""
        if not self.chat_history:
            return {}
        
        total_queries = len(self.chat_history)
        avg_response_time = sum(h.get("response_time", 0) for h in self.chat_history) / total_queries
        total_citations = sum(h.get("citations_count", 0) for h in self.chat_history)
        
        return {
            "total_queries": total_queries,
            "average_response_time": round(avg_response_time, 2),
            "total_citations": total_citations,
            "success_rate": sum(1 for h in self.chat_history if h.get("citations_count", 0) > 0) / total_queries * 100
        }
    
    def export_chat(self) -> str:
        """Export chat history as text."""
        if not self.messages:
            return "No messages to export."
        
        lines = []
        lines.append(f"Arete Philosophy Chat Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        lines.append("")
        
        for msg in self.messages:
            role = "You" if msg.role == "user" else "Arete"
            timestamp = msg.timestamp.strftime("%H:%M:%S")
            lines.append(f"[{timestamp}] {role}:")
            lines.append(msg.content)
            
            if msg.citations:
                lines.append(f"  Citations ({len(msg.citations)}):")
                for i, citation in enumerate(msg.citations, 1):
                    lines.append(f"    {i}. {citation.source_title} (Score: {citation.relevance_score:.2f})")
            
            lines.append("")
        
        return "\n".join(lines)

# Initialize global chat state
chat_state = ChatState()