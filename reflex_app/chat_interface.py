"""Chat interface for Reflex integration with RAG system"""

import reflex as rx
from typing import List, Dict, Any, Optional
import asyncio
import sys
import os

# Import existing Arete chat functionality
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from chat_rag_clean import (
        initialize_services,
        search_similar_chunks,
        search_related_entities,
        construct_context,
        generate_response,
        format_citations,
        prepare_embedding_text
    )
except ImportError as e:
    print(f"Warning: Could not import RAG chat functions: {e}")


class ChatMessage(rx.Base):
    """Chat message model"""
    content: str
    is_user: bool
    timestamp: str
    citations: Optional[List[Dict[str, Any]]] = None
    context_used: Optional[str] = None


class ChatInterfaceState(rx.State):
    """State management for chat interface"""
    
    # Chat state
    messages: List[ChatMessage] = []
    current_input: str = ""
    is_loading: bool = False
    is_connected: bool = False
    
    # RAG context
    last_context: str = ""
    last_citations: List[Dict[str, Any]] = []
    
    # Services (initialized on startup)
    services_initialized: bool = False
    
    async def initialize_rag_services(self):
        """Initialize RAG services"""
        if self.services_initialized:
            return True
            
        try:
            # Initialize services from chat_rag_clean
            services = await initialize_services()
            if services:
                self.services_initialized = True
                self.is_connected = True
                return True
        except Exception as e:
            print(f"Error initializing RAG services: {e}")
            self.is_connected = False
            return False
        
        return False
    
    def set_input(self, value: str):
        """Set current input value"""
        self.current_input = value
    
    async def send_message(self):
        """Send message and get RAG response"""
        if not self.current_input.strip():
            return
        
        user_message = self.current_input.strip()
        self.messages.append(ChatMessage(
            content=user_message,
            is_user=True,
            timestamp=rx.moment().format("HH:mm:ss")
        ))
        
        self.current_input = ""
        self.is_loading = True
        
        try:
            if not self.services_initialized:
                await self.initialize_rag_services()
            
            if self.services_initialized:
                # Use actual RAG pipeline
                response_content, citations, context = await self.get_rag_response(user_message)
            else:
                # Fallback response
                response_content = self.get_fallback_response(user_message)
                citations = []
                context = ""
            
            # Add AI response
            ai_message = ChatMessage(
                content=response_content,
                is_user=False,
                timestamp=rx.moment().format("HH:mm:ss"),
                citations=citations,
                context_used=context
            )
            self.messages.append(ai_message)
            
            self.last_citations = citations
            self.last_context = context
            
        except Exception as e:
            error_message = ChatMessage(
                content=f"I apologize, but I encountered an error: {str(e)}. Please try again.",
                is_user=False,
                timestamp=rx.moment().format("HH:mm:ss")
            )
            self.messages.append(error_message)
        
        finally:
            self.is_loading = False
    
    async def get_rag_response(self, query: str) -> tuple[str, List[Dict], str]:
        """Get response using RAG pipeline"""
        try:
            # Search for similar chunks
            similar_chunks = await search_similar_chunks(query)
            
            # Search for related entities
            related_entities = await search_related_entities(query)
            
            # Construct context
            context = construct_context(similar_chunks, related_entities)
            
            # Generate response
            response = await generate_response(query, context)
            
            # Format citations
            citations = format_citations(similar_chunks)
            
            return response, citations, context
            
        except Exception as e:
            print(f"Error in RAG response: {e}")
            raise e
    
    def get_fallback_response(self, query: str) -> str:
        """Get fallback response when RAG is unavailable"""
        philosophical_responses = {
            "virtue": "Virtue, or arete in Greek, is a central concept in classical philosophy. According to Plato, virtue is knowledge - knowing what is good and acting accordingly. Aristotle developed this further, distinguishing between intellectual and moral virtues.",
            "justice": "Justice is one of the four cardinal virtues in Plato's Republic. Plato defines justice as each part of the soul (and state) performing its proper function - reason ruling, spirit supporting, and appetite obeying.",
            "knowledge": "Knowledge versus opinion (doxa) is a fundamental distinction in Plato's philosophy. True knowledge is of the eternal Forms, while opinion deals with the changing world of appearances.",
            "soul": "The soul (psyche) in Platonic philosophy is immortal and consists of three parts: reason (logos), spirit (thymos), and appetite (epithumia). The rational part should rule over the others.",
            "good": "The Form of the Good is the highest Form in Plato's philosophy, described in the Republic through the Analogy of the Sun. It is the source of truth and reality."
        }
        
        query_lower = query.lower()
        for key, response in philosophical_responses.items():
            if key in query_lower:
                return response
        
        return "I'm currently unable to access the full knowledge base. Please try again, or rephrase your question about classical philosophy."
    
    def clear_chat(self):
        """Clear all messages"""
        self.messages = []
        self.last_context = ""
        self.last_citations = []
    
    def on_key_press(self, key: str):
        """Handle keyboard shortcuts"""
        if key == "Enter" and not self.is_loading:
            return self.send_message


def chat_message_component(message: ChatMessage) -> rx.Component:
    """Individual chat message component"""
    return rx.box(
        rx.hstack(
            # Avatar/Icon
            rx.avatar(
                rx.cond(
                    message.is_user,
                    rx.icon("user"),
                    rx.icon("bot")
                ),
                color_scheme=rx.cond(message.is_user, "blue", "green"),
                size="2"
            ),
            
            # Message content
            rx.vstack(
                # Header
                rx.hstack(
                    rx.text(
                        rx.cond(message.is_user, "You", "Arete AI"),
                        font_weight="bold",
                        font_size="sm",
                        color=rx.cond(message.is_user, "blue.600", "green.600")
                    ),
                    rx.text(
                        message.timestamp,
                        font_size="xs",
                        color="gray.500"
                    ),
                    spacing="2"
                ),
                
                # Message text
                rx.text(
                    message.content,
                    font_size="sm",
                    white_space="pre-wrap"
                ),
                
                # Citations (if available)
                rx.cond(
                    message.citations,
                    rx.vstack(
                        rx.text("Sources:", font_size="xs", font_weight="bold", color="gray.600"),
                        rx.foreach(
                            message.citations,
                            lambda citation: rx.box(
                                rx.text(
                                    f"• {citation['title']} (Relevance: {citation.get('relevance', 0):.1%})",
                                    font_size="xs",
                                    color="gray.600"
                                ),
                                rx.text(
                                    citation.get('preview', ''),
                                    font_size="xs",
                                    color="gray.500",
                                    font_style="italic",
                                    max_width="400px",
                                    white_space="pre-wrap"
                                ),
                                padding="2",
                                border_left="2px solid",
                                border_color="gray.300",
                                margin_left="2"
                            )
                        ),
                        spacing="1",
                        margin_top="2"
                    )
                ),
                
                align="start",
                spacing="1",
                flex="1"
            ),
            
            spacing="3",
            align="start",
            width="100%"
        ),
        
        padding="4",
        border_radius="lg",
        bg=rx.cond(
            message.is_user,
            "blue.50",
            "green.50"
        ),
        border="1px solid",
        border_color=rx.cond(
            message.is_user,
            "blue.200",
            "green.200"
        ),
        width="100%",
        margin_bottom="3"
    )


def chat_input_area() -> rx.Component:
    """Chat input area with send button"""
    return rx.hstack(
        rx.input(
            value=ChatInterfaceState.current_input,
            on_change=ChatInterfaceState.set_input,
            on_key_down=lambda key: rx.cond(
                key == "Enter",
                ChatInterfaceState.send_message(),
                rx.fragment()
            ),
            placeholder="Ask about classical philosophy...",
            size="3",
            flex="1",
            disabled=ChatInterfaceState.is_loading
        ),
        
        rx.button(
            rx.cond(
                ChatInterfaceState.is_loading,
                rx.spinner(size="1"),
                rx.icon("send")
            ),
            on_click=ChatInterfaceState.send_message,
            color_scheme="blue",
            size="3",
            disabled=ChatInterfaceState.is_loading | (ChatInterfaceState.current_input.length() == 0)
        ),
        
        spacing="2",
        width="100%",
        padding="4",
        border_top="1px solid",
        border_color="gray.200",
        bg="white"
    )


def connection_status() -> rx.Component:
    """Show RAG connection status"""
    return rx.hstack(
        rx.cond(
            ChatInterfaceState.is_connected,
            rx.hstack(
                rx.icon("check-circle", color="green.500", size=16),
                rx.text("RAG System Connected", color="green.600", font_size="sm"),
                spacing="1"
            ),
            rx.hstack(
                rx.icon("alert-circle", color="orange.500", size=16),
                rx.text("Using Fallback Responses", color="orange.600", font_size="sm"),
                spacing="1"
            )
        ),
        rx.spacer(),
        rx.button(
            rx.icon("trash-2"),
            "Clear Chat",
            on_click=ChatInterfaceState.clear_chat,
            color_scheme="gray",
            variant="soft",
            size="2"
        ),
        width="100%",
        padding="3",
        border_bottom="1px solid",
        border_color="gray.200",
        bg="gray.50"
    )


def chat_interface() -> rx.Component:
    """Main chat interface component"""
    return rx.vstack(
        # Header with title and status
        rx.vstack(
            rx.heading("Arete AI - Classical Philosophy Tutor", size="5"),
            rx.text(
                "Ask questions about classical philosophical texts and concepts",
                color="gray.600"
            ),
            connection_status(),
            spacing="2",
            width="100%"
        ),
        
        # Chat messages area
        rx.box(
            rx.cond(
                ChatInterfaceState.messages.length() == 0,
                rx.vstack(
                    rx.icon("message-circle", size=32, color="gray.400"),
                    rx.text("Start a conversation about philosophy", color="gray.500"),
                    rx.text("Try asking: 'What is virtue according to Plato?'", font_size="sm", color="gray.400"),
                    spacing="3",
                    align="center",
                    justify="center",
                    height="300px"
                ),
                rx.vstack(
                    rx.foreach(
                        ChatInterfaceState.messages,
                        chat_message_component
                    ),
                    spacing="0",
                    width="100%"
                )
            ),
            width="100%",
            flex="1",
            overflow_y="auto",
            padding="4",
            max_height="calc(100vh - 200px)"
        ),
        
        # Input area
        chat_input_area(),
        
        width="100%",
        max_width="800px",
        margin="0 auto",
        height="100vh",
        bg="white",
        border_radius="lg",
        shadow="lg",
        spacing="0"
    )


# Initialize services on app start
async def initialize_chat_on_load():
    """Initialize chat services when page loads"""
    state = ChatInterfaceState()
    await state.initialize_rag_services()