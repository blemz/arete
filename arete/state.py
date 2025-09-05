"""Global application state for Arete Reflex app."""

import reflex as rx
from typing import Dict, List, Optional
from enum import Enum


class LayoutMode(Enum):
    """Layout modes for the application."""
    SPLIT_VIEW = "split"
    CHAT_ONLY = "chat"
    DOCUMENT_ONLY = "document"
    MOBILE = "mobile"


class ThemeMode(Enum):
    """Theme modes for the application."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class NavigationState(rx.State):
    """State for navigation and layout management."""
    
    # Navigation state
    current_route: str = "/"
    is_mobile_menu_open: bool = False
    is_sidebar_collapsed: bool = False
    is_user_dropdown_open: bool = False
    
    # Layout state
    layout_mode: str = LayoutMode.SPLIT_VIEW.value
    theme_mode: str = ThemeMode.LIGHT.value
    
    # Recent items
    recent_conversations: List[Dict[str, str]] = [
        {"id": "conv1", "title": "What is virtue according to Plato?", "date": "2025-09-05"},
        {"id": "conv2", "title": "Aristotelian ethics discussion", "date": "2025-09-04"},
        {"id": "conv3", "title": "Socratic method analysis", "date": "2025-09-03"},
    ]
    
    recent_documents: List[Dict[str, str]] = [
        {"id": "doc1", "title": "Plato's Republic", "type": "dialogue"},
        {"id": "doc2", "title": "Nicomachean Ethics", "type": "treatise"},
        {"id": "doc3", "title": "Apology", "type": "dialogue"},
    ]
    
    # User profile
    user_name: str = "Scholar"
    user_avatar: str = "/avatar-placeholder.png"
    
    def toggle_mobile_menu(self):
        """Toggle mobile hamburger menu."""
        self.is_mobile_menu_open = not self.is_mobile_menu_open
    
    def toggle_sidebar(self):
        """Toggle sidebar collapse state."""
        self.is_sidebar_collapsed = not self.is_sidebar_collapsed
    
    def toggle_user_dropdown(self):
        """Toggle user dropdown menu."""
        self.is_user_dropdown_open = not self.is_user_dropdown_open
    
    def toggle_theme(self):
        """Toggle between light and dark theme."""
        if self.theme_mode == ThemeMode.LIGHT.value:
            self.theme_mode = ThemeMode.DARK.value
        else:
            self.theme_mode = ThemeMode.LIGHT.value
    
    def set_layout_mode(self, mode: str):
        """Set the current layout mode."""
        if mode in [m.value for m in LayoutMode]:
            self.layout_mode = mode
    
    def set_current_route(self, route: str):
        """Set the current active route."""
        self.current_route = route
        # Close mobile menu when navigating
        self.is_mobile_menu_open = False
    
    def close_mobile_menu(self):
        """Close mobile menu."""
        self.is_mobile_menu_open = False
    
    def close_user_dropdown(self):
        """Close user dropdown."""
        self.is_user_dropdown_open = False


class ChatState(rx.State):
    """State for chat functionality."""
    
    messages: List[Dict[str, str]] = []
    current_message: str = ""
    is_loading: bool = False
    
    def send_message(self):
        """Send a message to the chat."""
        if self.current_message.strip():
            self.messages.append({
                "role": "user",
                "content": self.current_message,
                "timestamp": "just now"
            })
            
            # Simulate AI response
            self.is_loading = True
            yield
            
            # Add AI response
            self.messages.append({
                "role": "assistant", 
                "content": f"This is a response to: {self.current_message}",
                "timestamp": "just now"
            })
            
            self.current_message = ""
            self.is_loading = False


class DocumentState(rx.State):
    """State for document viewer functionality."""
    
    current_document: Optional[str] = None
    document_content: str = ""
    highlighted_passages: List[Dict[str, str]] = []
    search_query: str = ""
    search_results: List[Dict[str, str]] = []
    
    def load_document(self, doc_id: str):
        """Load a document for viewing."""
        self.current_document = doc_id
        # Simulate loading document content
        self.document_content = f"Content of document {doc_id}..."
    
    def search_document(self):
        """Search within the current document."""
        if self.search_query.strip():
            # Simulate search results
            self.search_results = [
                {"passage": f"Result for '{self.search_query}'", "location": "Page 42"},
                {"passage": f"Another result for '{self.search_query}'", "location": "Page 67"},
            ]
    
    def highlight_passage(self, passage: str, location: str):
        """Highlight a passage in the document."""
        self.highlighted_passages.append({
            "passage": passage,
            "location": location,
            "timestamp": "just now"
        })