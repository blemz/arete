"""
Arete Reflex Application - Main App Module

A Graph-RAG AI tutoring system for classical philosophical texts.
Built with Reflex framework for modern web interface.
"""

import reflex as rx
from typing import List

# Import pages (will be created)
from .pages import index_page, chat_page, document_page, analytics_page

class AreteState(rx.State):
    """Global state for the Arete application."""
    
    # User session state
    user_query: str = ""
    chat_history: List[dict] = []
    is_loading: bool = False
    
    # Document viewer state
    current_document: str = ""
    selected_citation: str = ""
    
    # Analytics state
    current_analysis: dict = {}
    
    def set_loading(self, loading: bool):
        """Set loading state."""
        self.is_loading = loading
    
    def add_chat_message(self, message: str, is_user: bool = True):
        """Add message to chat history."""
        self.chat_history.append({
            "content": message,
            "is_user": is_user,
            "timestamp": rx.moment().format("HH:mm")
        })
    
    def clear_chat(self):
        """Clear chat history."""
        self.chat_history = []
    
    def set_document(self, doc_id: str):
        """Set current document."""
        self.current_document = doc_id
    
    def set_citation(self, citation: str):
        """Set selected citation."""
        self.selected_citation = citation


def create_app() -> rx.App:
    """Create and configure the Arete Reflex application."""
    
    app = rx.App(
        state=AreteState,
        stylesheets=[
            "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
            "/styles/global.css"
        ],
        title="Arete - AI Philosophy Tutor",
        description="Graph-RAG AI tutoring system for classical philosophical texts"
    )
    
    # Add routes
    app.add_page(index_page, route="/", title="Arete - Home")
    app.add_page(chat_page, route="/chat", title="Arete - Chat")
    app.add_page(document_page, route="/documents", title="Arete - Documents")
    app.add_page(analytics_page, route="/analytics", title="Arete - Analytics")
    
    return app


# Create the app instance
app = create_app()