"""
Streamlit chat interface for Arete philosophical tutoring system.

Provides an interactive web interface for philosophical conversations with
the complete Graph-RAG system including session management, citation display,
and integration with the RAG pipeline.
"""

import streamlit as st
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
import time

# Arete imports
import sys
from pathlib import Path

# Add the src directory to path so we can import arete modules
root_path = Path(__file__).parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from arete.models.chat_session import ChatSession, ChatMessage, ChatContext, MessageType, SessionStatus
from arete.services.chat_service import ChatService

# Import document viewer components
from .document_viewer import (
    SplitViewLayout, DocumentRenderer, CitationNavigator, DocumentSearchInterface,
    DocumentContent, Citation, create_sample_documents, create_sample_citations
)


class AreteStreamlitInterface:
    """Main Streamlit interface for Arete philosophical tutoring."""
    
    def __init__(self):
        """Initialize the Streamlit interface."""
        self.chat_service = ChatService()
        
        # Initialize document viewer components
        self.split_view_layout = SplitViewLayout()
        self.document_search_interface = DocumentSearchInterface()
        
        # Load sample documents for demonstration
        self.document_search_interface.set_available_documents(create_sample_documents())
        
        self.setup_page_config()
        self.initialize_session_state()
    
    def setup_page_config(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title="Arete - Philosophical Tutoring Assistant",
            page_icon="🏛️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS for philosophical theme
        st.markdown("""
        <style>
        .main {
            padding-top: 2rem;
        }
        .stChatMessage[data-testid="message"] {
            background-color: #f8f9fa;
            border-left: 4px solid #007bff;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 0.5rem;
        }
        .citation {
            background-color: #e9ecef;
            border-left: 3px solid #6c757d;
            padding: 0.5rem;
            margin: 0.25rem 0;
            font-size: 0.9em;
            font-style: italic;
        }
        .philosophical-quote {
            border-left: 4px solid #17a2b8;
            padding-left: 1rem;
            margin: 1rem 0;
            font-style: italic;
            color: #495057;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if "current_session" not in st.session_state:
            st.session_state.current_session = None
        
        if "user_id" not in st.session_state:
            st.session_state.user_id = f"user_{uuid.uuid4().hex[:8]}"
        
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        if "session_context" not in st.session_state:
            st.session_state.session_context = ChatContext()
            
        # Document viewer session state
        if "current_document" not in st.session_state:
            st.session_state.current_document = None
            
        if "selected_citation" not in st.session_state:
            st.session_state.selected_citation = None
            
        if "ui_mode" not in st.session_state:
            st.session_state.ui_mode = "Split View"  # Default to split view
            
        if "document_search_expanded" not in st.session_state:
            st.session_state.document_search_expanded = False
    
    def render_sidebar(self):
        """Render the sidebar with session management and context settings."""
        with st.sidebar:
            st.header("🏛️ Arete Philosophy Tutor")
            
            # Session Management
            st.subheader("📚 Session Management")
            
            # Current session info
            if st.session_state.current_session:
                st.info(f"**Current Session:** {st.session_state.current_session.title}")
                st.caption(f"Created: {st.session_state.current_session.created_at.strftime('%Y-%m-%d %H:%M')}")
            else:
                st.warning("No active session")
            
            # New session button
            if st.button("🆕 New Session"):
                self.create_new_session()
            
            # Session list
            user_sessions = self.chat_service.list_user_sessions(st.session_state.user_id, limit=10)
            if user_sessions:
                st.subheader("📜 Recent Sessions")
                for session in user_sessions[:5]:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(f"📖 {session.title[:20]}...", key=f"load_{session.session_id}"):
                            self.load_session(session.session_id)
                    with col2:
                        if st.button("🗑️", key=f"del_{session.session_id}", help="Delete session"):
                            self.delete_session(session.session_id)
            
            st.divider()
            
            # Context Configuration
            st.subheader("🎓 Learning Context")
            
            student_level = st.selectbox(
                "Academic Level",
                ["undergraduate", "graduate", "advanced", "general"],
                index=0,
                key="student_level"
            )
            
            philosophical_period = st.selectbox(
                "Philosophical Period",
                ["ancient", "medieval", "modern", "contemporary", "all"],
                index=0,
                key="phil_period"
            )
            
            current_topic = st.text_input(
                "Current Topic",
                placeholder="e.g., virtue ethics, cave allegory",
                key="current_topic"
            )
            
            # Update context when changed
            if (student_level != st.session_state.session_context.student_level or
                philosophical_period != st.session_state.session_context.philosophical_period or
                current_topic != st.session_state.session_context.current_topic):
                
                st.session_state.session_context = ChatContext(
                    student_level=student_level,
                    philosophical_period=philosophical_period,
                    current_topic=current_topic
                )
                
                if st.session_state.current_session:
                    st.session_state.current_session.update_context(st.session_state.session_context)
            
            st.divider()
            
            # Document Viewer Controls
            st.subheader("📚 Document Viewer")
            
            # UI Mode selector
            ui_mode = st.selectbox(
                "Interface Mode",
                ["Split View", "Chat Only", "Document Only"],
                index=["Split View", "Chat Only", "Document Only"].index(st.session_state.ui_mode),
                key="ui_mode_selector"
            )
            
            if ui_mode != st.session_state.ui_mode:
                st.session_state.ui_mode = ui_mode
                st.rerun()
            
            # Document selection
            with st.expander("📖 Select Document", expanded=st.session_state.document_search_expanded):
                selected_document = self.document_search_interface.render_document_selector()
                if selected_document and selected_document != st.session_state.current_document:
                    st.session_state.current_document = selected_document
                    # Load sample citations for the selected document
                    if selected_document.doc_id == "plato_republic":
                        sample_citations = create_sample_citations()
                        self.split_view_layout.citation_navigator.set_citations(sample_citations[:1])  # First citation
                    st.success(f"Loaded: {selected_document.title}")
                    st.rerun()
            
            st.divider()
            
            # Statistics
            if st.session_state.current_session:
                st.subheader("📊 Session Stats")
                message_count = len(st.session_state.current_session.messages)
                st.metric("Messages", message_count)
                
                if message_count > 0:
                    citation_count = sum(len(msg.citations) for msg in st.session_state.current_session.messages)
                    st.metric("Citations", citation_count)
                    
            # Document stats
            if st.session_state.current_document:
                st.subheader("📄 Document Stats")
                st.metric("Characters", len(st.session_state.current_document.content))
                citations_count = len(self.split_view_layout.citation_navigator.citations)
                st.metric("Citations Available", citations_count)
    
    def create_new_session(self):
        """Create a new chat session."""
        session_title = f"Philosophy Discussion - {datetime.now().strftime('%H:%M')}"
        
        new_session = self.chat_service.create_session(
            user_id=st.session_state.user_id,
            title=session_title,
            context=st.session_state.session_context
        )
        
        st.session_state.current_session = new_session
        st.session_state.messages = []
        st.success(f"Created new session: {session_title}")
        st.rerun()
    
    def load_session(self, session_id: str):
        """Load an existing chat session."""
        session = self.chat_service.get_session(session_id)
        if session:
            st.session_state.current_session = session
            st.session_state.messages = [msg for msg in session.messages]
            st.session_state.session_context = session.context
            st.success(f"Loaded session: {session.title}")
            st.rerun()
    
    def delete_session(self, session_id: str):
        """Delete a chat session."""
        if self.chat_service.delete_session(session_id):
            if (st.session_state.current_session and 
                st.session_state.current_session.session_id == session_id):
                st.session_state.current_session = None
                st.session_state.messages = []
            st.success("Session deleted")
            st.rerun()
    
    def display_message(self, message: ChatMessage):
        """Display a single chat message with proper formatting."""
        with st.chat_message(message.message_type.value):
            # Message content
            st.write(message.content)
            
            # Citations display
            if message.citations:
                st.markdown("**Sources:**")
                for citation in message.citations:
                    st.markdown(f'<div class="citation">📜 {citation}</div>', 
                               unsafe_allow_html=True)
            
            # Metadata (timestamp, etc.)
            if message.message_type == MessageType.ASSISTANT and message.metadata:
                with st.expander("ℹ️ Response Details", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    
                    if "provider" in message.metadata:
                        col1.caption(f"**Provider:** {message.metadata['provider']}")
                    
                    if "response_time" in message.metadata:
                        col2.caption(f"**Time:** {message.metadata['response_time']:.2f}s")
                    
                    if "token_count" in message.metadata:
                        col3.caption(f"**Tokens:** {message.metadata['token_count']}")
            
            # Timestamp
            st.caption(f"*{message.timestamp.strftime('%H:%M:%S')}*")
    
    def render_chat_interface(self):
        """Render the main chat interface."""
        st.header("💬 Philosophical Conversation")
        
        # Ensure we have a session
        if not st.session_state.current_session:
            st.info("👈 Please create a new session to start chatting")
            return
        
        # Display chat messages
        for message in st.session_state.messages:
            self.display_message(message)
        
        # Chat input
        if prompt := st.chat_input("Ask a philosophical question..."):
            self.handle_user_input(prompt)
    
    def handle_user_input(self, user_input: str):
        """Handle user input and generate response."""
        # Create user message
        user_message = ChatMessage(
            message_id=f"msg_{uuid.uuid4().hex[:8]}",
            content=user_input,
            message_type=MessageType.USER,
            timestamp=datetime.now(),
            user_id=st.session_state.user_id
        )
        
        # Add to session and display
        st.session_state.current_session.add_message(user_message)
        st.session_state.messages.append(user_message)
        
        # Update service
        self.chat_service.add_message_to_session(
            st.session_state.current_session.session_id,
            user_message
        )
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Generate assistant response (placeholder for now)
        self.generate_assistant_response(user_input)
    
    def generate_assistant_response(self, user_input: str):
        """Generate assistant response using RAG pipeline."""
        import asyncio
        from ..services.rag_pipeline_service import RAGPipelineService, RAGPipelineConfig, create_rag_pipeline_service
        
        with st.chat_message("assistant"):
            # Show typing indicator
            with st.spinner("🤔 Thinking about your philosophical question..."):
                
                # Initialize RAG pipeline if not already done
                if not hasattr(self, '_rag_pipeline'):
                    self._rag_pipeline = create_rag_pipeline_service()
                
                # Create pipeline configuration based on session context
                pipeline_config = RAGPipelineConfig(
                    max_retrieval_results=30,
                    max_response_tokens=1500,
                    temperature=0.7,
                    enable_reranking=True,
                    enable_diversification=True,
                    philosophical_domain_boost=1.2
                )
                
                # Prepare user context from session
                user_context = {
                    'student_level': st.session_state.session_context.student_level,
                    'philosophical_period': st.session_state.session_context.philosophical_period,
                    'current_topic': st.session_state.session_context.current_topic,
                    'session_id': st.session_state.current_session.session_id if st.session_state.current_session else None
                }
                
                try:
                    # Execute RAG pipeline
                    start_time = time.time()
                    
                    # Use asyncio to run the async pipeline
                    pipeline_result = asyncio.run(
                        self._rag_pipeline.execute_pipeline(
                            query=user_input,
                            config=pipeline_config,
                            user_context=user_context
                        )
                    )
                    
                    response_time = time.time() - start_time
                    
                    # Display the response
                    st.write(pipeline_result.response.response_text)
                    
                    # Display citations
                    if pipeline_result.response.citations:
                        st.markdown("**Sources:**")
                        for citation in pipeline_result.response.citations:
                            citation_text = citation.source_reference or f"Citation {citation.id}"
                            st.markdown(f'<div class="citation">📖 {citation_text}</div>', 
                                       unsafe_allow_html=True)
                    
                    # Display detailed metadata in expander
                    with st.expander("ℹ️ Response Details", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        
                        col1.caption(f"**Provider:** {pipeline_result.response.provider_used}")
                        col2.caption(f"**Time:** {response_time:.2f}s")
                        col3.caption(f"**Citations:** {len(pipeline_result.response.citations)}")
                        
                        # Additional pipeline metrics
                        col1.caption(f"**Retrieved:** {pipeline_result.metrics.retrieved_results}")
                        col2.caption(f"**Relevance:** {pipeline_result.metrics.average_relevance_score:.3f}")
                        col3.caption(f"**Validation:** {pipeline_result.response.validation.accuracy_score:.3f}")
                    
                    # Create assistant message with real data
                    assistant_message = ChatMessage(
                        message_id=f"msg_{uuid.uuid4().hex[:8]}",
                        content=pipeline_result.response.response_text,
                        message_type=MessageType.ASSISTANT,
                        timestamp=datetime.now(),
                        citations=[citation.source_reference or f"Citation {citation.id}" 
                                 for citation in pipeline_result.response.citations],
                        metadata={
                            "provider": pipeline_result.response.provider_used,
                            "response_time": response_time,
                            "token_count": pipeline_result.response.token_usage.get('response_tokens', 0),
                            "retrieval_results": pipeline_result.metrics.retrieved_results,
                            "relevance_score": pipeline_result.metrics.average_relevance_score,
                            "validation_score": pipeline_result.response.validation.accuracy_score,
                            "citations_count": len(pipeline_result.response.citations)
                        }
                    )
                    
                except Exception as e:
                    st.error(f"Sorry, I encountered an error: {str(e)}")
                    
                    # Fallback to basic response
                    assistant_message = ChatMessage(
                        message_id=f"msg_{uuid.uuid4().hex[:8]}",
                        content=f"I apologize, but I'm having trouble processing your question right now. Error: {str(e)}",
                        message_type=MessageType.ASSISTANT,
                        timestamp=datetime.now(),
                        citations=[],
                        metadata={
                            "provider": "error_fallback",
                            "response_time": 0.0,
                            "error": str(e)
                        }
                    )
        
        # Add to session
        st.session_state.current_session.add_message(assistant_message)
        st.session_state.messages.append(assistant_message)
        
        # Update service
        self.chat_service.add_message_to_session(
            st.session_state.current_session.session_id,
            assistant_message
        )
    
    def render_welcome_message(self):
        """Render welcome message for new users."""
        if not st.session_state.messages and not st.session_state.current_session:
            st.markdown("""
            ### Welcome to Arete! 🏛️
            
            **Arete** is your AI-powered philosophical tutoring assistant, designed to help you explore the rich tradition of classical philosophy through interactive dialogue.
            
            #### How to get started:
            1. 👈 **Create a new session** in the sidebar
            2. 🎓 **Set your learning context** (academic level, philosophical period, topic)
            3. 💬 **Ask philosophical questions** in the chat
            4. 📜 **Explore citations** from classical texts
            
            #### What you can explore:
            - **Ancient Philosophy**: Plato, Aristotle, Stoics, Epicureans
            - **Medieval Philosophy**: Augustine, Aquinas, Islamic philosophy
            - **Modern Philosophy**: Descartes, Kant, Hume, Spinoza
            - **Contemporary Issues**: Applied ethics, political philosophy, metaphysics
            
            #### Example questions to try:
            - "What is virtue according to Aristotle?"
            - "Explain Plato's Cave Allegory"
            - "How does Kant define categorical imperative?"
            - "What is the difference between Stoicism and Epicureanism?"
            
            Start by creating a new session and asking your first philosophical question! 🤔💭
            """)
    
    def run(self):
        """Main application entry point."""
        # Render sidebar
        self.render_sidebar()
        
        # Render main content based on UI mode
        if st.session_state.ui_mode == "Split View":
            self._render_split_view_interface()
        elif st.session_state.ui_mode == "Chat Only":
            self._render_chat_only_interface() 
        elif st.session_state.ui_mode == "Document Only":
            self._render_document_only_interface()
        else:
            # Default to split view
            self._render_split_view_interface()
    
    def _render_split_view_interface(self):
        """Render split view interface with chat and document panels."""
        # Use the split view layout component
        self.split_view_layout.render_split_view(self, st.session_state.current_document)
    
    def _render_chat_only_interface(self):
        """Render chat-only interface."""
        if st.session_state.current_session or st.session_state.messages:
            self.render_chat_interface()
        else:
            self.render_welcome_message()
            
    def _render_document_only_interface(self):
        """Render document-only interface."""
        if st.session_state.current_document:
            st.markdown("### 📄 Document Viewer")
            
            # Set up document renderer
            self.split_view_layout.document_renderer.set_document(st.session_state.current_document)
            
            # Load citations if available
            if st.session_state.current_document.doc_id == "plato_republic":
                sample_citations = create_sample_citations()[:1]  # First citation
                self.split_view_layout.document_renderer.set_citations(sample_citations)
                self.split_view_layout.citation_navigator.set_citations(sample_citations)
            
            # Render document components
            self.split_view_layout.document_renderer.render_document_header()
            self.split_view_layout.document_renderer.render_search_controls()
            self.split_view_layout.document_renderer.render_document_content()
            
        else:
            st.info("👈 Please select a document from the sidebar to view it.")
            
            # Show welcome message for document viewer
            st.markdown("""
            ### 📚 Document Viewer Mode
            
            In this mode, you can:
            - **Browse classical philosophical texts**
            - **Search within documents** 
            - **Navigate citations and references**
            - **Highlight and annotate passages**
            
            Select a document from the sidebar to get started!
            """)


def main():
    """Main function to run the Streamlit app."""
    app = AreteStreamlitInterface()
    app.run()


if __name__ == "__main__":
    main()