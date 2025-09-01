"""
Streamlit chat interface for Arete philosophical tutoring system.

Provides an interactive web interface for philosophical conversations with
the complete Graph-RAG system including session management, citation display,
and integration with the RAG pipeline.
"""

import streamlit as st
import uuid
import os
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
from arete.services.user_preferences_service import UserPreferencesService
from arete.services.conversation_export_service import ConversationExportService
from arete.services.conversation_sharing_service import ConversationSharingService
from arete.models.user_preferences import UserPreferences, Theme, CitationStyle
from arete.models.export_models import ExportFormat, ExportOptions
from arete.models.sharing_models import ShareType, ExpirationPeriod, SharePermissions

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
        self.preferences_service = UserPreferencesService()
        self.export_service = ConversationExportService()
        self.sharing_service = ConversationSharingService(self.chat_service)
        
        # Initialize document viewer components
        self.split_view_layout = SplitViewLayout()
        self.document_search_interface = DocumentSearchInterface()
        
        # Load sample documents for demonstration
        self.document_search_interface.set_available_documents(create_sample_documents())
        
        self.setup_page_config()
        self.initialize_session_state()
        
        # Apply user theme after session state is initialized
        self.apply_user_theme()
    
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
            
        # User preferences
        if "user_preferences" not in st.session_state:
            st.session_state.user_preferences = self.preferences_service.get_user_preferences(st.session_state.user_id)
            
        if "preferences_sidebar_expanded" not in st.session_state:
            st.session_state.preferences_sidebar_expanded = False
            
        if "show_preferences" not in st.session_state:
            st.session_state.show_preferences = False
            
        if "show_search" not in st.session_state:
            st.session_state.show_search = False
            
        if "search_results" not in st.session_state:
            st.session_state.search_results = []
    
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
            
            # User Preferences
            st.subheader("⚙️ Preferences")
            
            if st.button("🎨 Customize Interface", key="show_preferences"):
                st.session_state.show_preferences = not st.session_state.show_preferences
            
            if st.session_state.show_preferences:
                self.render_preferences_panel()
            
            # Export Functionality
            if st.session_state.current_session and len(st.session_state.current_session.messages) > 0:
                if st.button("📥 Export Conversation", key="show_export"):
                    st.session_state.show_export = not st.session_state.get("show_export", False)
                
                if st.session_state.get("show_export", False):
                    self.render_export_panel()
            
            # Enhanced Search
            st.subheader("🔍 Search Conversations")
            
            if st.button("🔎 Advanced Search", key="show_search"):
                st.session_state.show_search = not st.session_state.show_search
            
            # Quick search
            quick_search = st.text_input(
                "Quick Search",
                placeholder="Search across all conversations...",
                key="quick_search_input"
            )
            
            if quick_search:
                self.perform_quick_search(quick_search)
            
            # Advanced search panel
            if st.session_state.show_search:
                self.render_advanced_search_panel()
            
            # Display search results
            if st.session_state.search_results:
                self.display_search_results()
            
            st.divider()
            
            # Sharing and Collaboration
            if st.session_state.current_session and len(st.session_state.current_session.messages) > 0:
                st.subheader("🤝 Share Conversation")
                
                if st.button("🔗 Share & Collaborate", key="show_sharing"):
                    st.session_state.show_sharing = not st.session_state.get("show_sharing", False)
                
                if st.session_state.get("show_sharing", False):
                    self.render_sharing_panel()
            
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
    
    def render_preferences_panel(self):
        """Render user preferences panel."""
        st.markdown("**🎨 Interface Theme**")
        
        # Theme selection
        current_theme = st.session_state.user_preferences.theme.value
        theme_options = ["light", "dark", "high_contrast", "sepia"]
        theme_labels = ["Light", "Dark", "High Contrast", "Sepia"]
        
        selected_theme = st.selectbox(
            "Theme",
            options=theme_options,
            format_func=lambda x: dict(zip(theme_options, theme_labels))[x],
            index=theme_options.index(current_theme),
            key="theme_selector"
        )
        
        # Citation style selection
        st.markdown("**📚 Citation Style**")
        current_citation_style = st.session_state.user_preferences.citation_style.value
        citation_options = ["chicago", "mla", "apa", "harvard", "oxford"]
        citation_labels = ["Chicago", "MLA", "APA", "Harvard", "Oxford"]
        
        selected_citation_style = st.selectbox(
            "Citation Format",
            options=citation_options,
            format_func=lambda x: dict(zip(citation_options, citation_labels))[x],
            index=citation_options.index(current_citation_style),
            key="citation_style_selector"
        )
        
        # Display settings
        st.markdown("**📱 Display Options**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            show_timestamps = st.checkbox(
                "Show timestamps",
                value=st.session_state.user_preferences.display_settings.show_timestamps,
                key="show_timestamps_checkbox"
            )
            
            compact_mode = st.checkbox(
                "Compact mode",
                value=st.session_state.user_preferences.display_settings.compact_mode,
                key="compact_mode_checkbox"
            )
        
        with col2:
            show_citations = st.checkbox(
                "Show citations",
                value=st.session_state.user_preferences.display_settings.show_citations,
                key="show_citations_checkbox"
            )
            
            animations_enabled = st.checkbox(
                "Enable animations",
                value=st.session_state.user_preferences.display_settings.animations_enabled,
                key="animations_checkbox"
            )
        
        # Font size
        font_size_options = ["small", "medium", "large", "extra_large"]
        font_size_labels = ["Small", "Medium", "Large", "Extra Large"]
        
        selected_font_size = st.selectbox(
            "Font Size",
            options=font_size_options,
            format_func=lambda x: dict(zip(font_size_options, font_size_labels))[x],
            index=font_size_options.index(st.session_state.user_preferences.display_settings.font_size),
            key="font_size_selector"
        )
        
        # Language and other settings
        st.markdown("**🌐 Language & Other**")
        
        auto_save = st.checkbox(
            "Auto-save conversations",
            value=st.session_state.user_preferences.auto_save,
            key="auto_save_checkbox"
        )
        
        # Notification settings
        st.markdown("**🔔 Notifications**")
        
        email_notifications = st.checkbox(
            "Email notifications",
            value=st.session_state.user_preferences.notification_settings.email_notifications,
            key="email_notifications_checkbox"
        )
        
        philosophical_quotes = st.checkbox(
            "Daily philosophical quotes",
            value=st.session_state.user_preferences.notification_settings.philosophical_quotes,
            key="philosophical_quotes_checkbox"
        )
        
        # Save preferences button
        if st.button("💾 Save Preferences", key="save_preferences"):
            self.save_user_preferences(
                theme=selected_theme,
                citation_style=selected_citation_style,
                show_timestamps=show_timestamps,
                compact_mode=compact_mode,
                show_citations=show_citations,
                animations_enabled=animations_enabled,
                font_size=selected_font_size,
                auto_save=auto_save,
                email_notifications=email_notifications,
                philosophical_quotes=philosophical_quotes
            )
            st.success("✅ Preferences saved!")
            st.rerun()
        
        # Reset to defaults button
        if st.button("🔄 Reset to Defaults", key="reset_preferences"):
            if self.preferences_service.reset_user_preferences_to_defaults(st.session_state.user_id):
                st.session_state.user_preferences = self.preferences_service.get_user_preferences(st.session_state.user_id)
                st.success("✅ Preferences reset to defaults!")
                st.rerun()
    
    def save_user_preferences(self, **kwargs):
        """Save updated user preferences."""
        try:
            # Create updates dictionary
            updates = {
                "theme": Theme(kwargs["theme"]),
                "citation_style": CitationStyle(kwargs["citation_style"]),
                "auto_save": kwargs["auto_save"],
                "display_settings": {
                    "show_timestamps": kwargs["show_timestamps"],
                    "compact_mode": kwargs["compact_mode"],
                    "show_citations": kwargs["show_citations"],
                    "animations_enabled": kwargs["animations_enabled"],
                    "font_size": kwargs["font_size"]
                },
                "notification_settings": {
                    "email_notifications": kwargs["email_notifications"],
                    "philosophical_quotes": kwargs["philosophical_quotes"]
                }
            }
            
            # Update preferences
            result = self.preferences_service.update_user_preferences_partial(
                st.session_state.user_id,
                updates
            )
            
            if result:
                # Update session state
                st.session_state.user_preferences = self.preferences_service.get_user_preferences(st.session_state.user_id)
                return True
            
        except Exception as e:
            st.error(f"Error saving preferences: {str(e)}")
        
        return False
    
    def apply_user_theme(self):
        """Apply user theme to the interface."""
        if not st.session_state.user_preferences:
            return
        
        theme = st.session_state.user_preferences.theme
        font_size = st.session_state.user_preferences.display_settings.font_size
        compact_mode = st.session_state.user_preferences.display_settings.compact_mode
        animations_enabled = st.session_state.user_preferences.display_settings.animations_enabled
        
        # Apply theme-specific CSS
        theme_css = self.get_theme_css(theme, font_size, compact_mode, animations_enabled)
        st.markdown(theme_css, unsafe_allow_html=True)
    
    def get_theme_css(self, theme, font_size, compact_mode, animations_enabled):
        """Get CSS for the selected theme and preferences."""
        # Font size mapping
        font_sizes = {
            "small": "0.8rem",
            "medium": "1rem", 
            "large": "1.2rem",
            "extra_large": "1.4rem"
        }
        
        # Base CSS
        css = f"""
        <style>
        .main {{
            font-size: {font_sizes.get(font_size, "1rem")};
        }}
        """
        
        # Theme-specific CSS
        if theme == Theme.DARK:
            css += """
            .stApp {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            .stSidebar {
                background-color: #2d2d2d;
            }
            .stChatMessage[data-testid="message"] {
                background-color: #3d3d3d;
                border-left: 4px solid #4a90e2;
            }
            """
        elif theme == Theme.HIGH_CONTRAST:
            css += """
            .stApp {
                background-color: #000000;
                color: #ffffff;
                font-weight: bold;
            }
            .stChatMessage[data-testid="message"] {
                background-color: #333333;
                border: 2px solid #ffffff;
            }
            """
        elif theme == Theme.SEPIA:
            css += """
            .stApp {
                background-color: #f4f3e7;
                color: #5c4b37;
            }
            .stChatMessage[data-testid="message"] {
                background-color: #ede7d3;
                border-left: 4px solid #8b7355;
            }
            """
        
        # Compact mode
        if compact_mode:
            css += """
            .stChatMessage {
                margin: 0.25rem 0 !important;
                padding: 0.5rem !important;
            }
            """
        
        # Disable animations if requested
        if not animations_enabled:
            css += """
            * {
                transition: none !important;
                animation: none !important;
            }
            """
        
        css += "</style>"
        return css
    
    def render_export_panel(self):
        """Render export options panel."""
        st.markdown("**📥 Export Format**")
        
        # Format selection
        format_options = ["pdf", "markdown", "html", "txt", "json"]
        format_labels = ["PDF", "Markdown", "HTML", "Plain Text", "JSON"]
        
        selected_format = st.selectbox(
            "Choose Format",
            options=format_options,
            format_func=lambda x: dict(zip(format_options, format_labels))[x],
            key="export_format_selector"
        )
        
        # Export options
        st.markdown("**⚙️ Export Options**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            include_timestamps = st.checkbox(
                "Include timestamps",
                value=True,
                key="export_timestamps"
            )
            
            include_citations = st.checkbox(
                "Include citations",
                value=True,
                key="export_citations"
            )
        
        with col2:
            include_metadata = st.checkbox(
                "Include metadata",
                value=True,
                key="export_metadata"
            )
            
            include_context = st.checkbox(
                "Include session context",
                value=True,
                key="export_context"
            )
        
        # Additional options for specific formats
        if selected_format == "pdf":
            st.markdown("**📄 PDF Options**")
            font_size = st.slider("Font Size", min_value=8, max_value=16, value=12, key="pdf_font_size")
            page_size = st.selectbox("Page Size", ["A4", "Letter"], key="pdf_page_size")
        
        if selected_format in ["html", "markdown"]:
            format_quotes = st.checkbox(
                "Format philosophical quotes",
                value=True,
                key="format_quotes"
            )
        
        # Custom options
        st.markdown("**🎨 Customization**")
        
        custom_header = st.text_input(
            "Custom Header (optional)",
            placeholder="e.g., My Philosophy Discussion",
            key="export_custom_header"
        )
        
        # Export button
        if st.button("📥 Export Now", key="start_export", type="primary"):
            self.perform_export(
                format=selected_format,
                include_timestamps=include_timestamps,
                include_citations=include_citations,
                include_metadata=include_metadata,
                include_context=include_context,
                custom_header=custom_header,
                font_size=locals().get('font_size', 12),
                page_size=locals().get('page_size', 'A4'),
                format_quotes=locals().get('format_quotes', True)
            )
    
    def perform_export(self, **export_kwargs):
        """Perform the actual export operation."""
        if not st.session_state.current_session:
            st.error("No active session to export")
            return
        
        try:
            # Create export options
            options = ExportOptions(
                include_timestamps=export_kwargs.get('include_timestamps', True),
                include_citations=export_kwargs.get('include_citations', True),
                include_metadata=export_kwargs.get('include_metadata', True),
                include_context=export_kwargs.get('include_context', True),
                custom_header=export_kwargs.get('custom_header') or None,
                font_size=export_kwargs.get('font_size', 12),
                page_size=export_kwargs.get('page_size', 'A4'),
                format_philosophical_quotes=export_kwargs.get('format_quotes', True)
            )
            
            # Get export format
            format_str = export_kwargs.get('format', 'markdown')
            export_format = ExportFormat(format_str)
            
            # Perform export
            with st.spinner(f"Exporting conversation to {format_str.upper()}..."):
                result = self.export_service.export_session(
                    st.session_state.current_session,
                    export_format,
                    options
                )
            
            if result.success:
                st.success(f"✅ Export completed successfully!")
                
                # Display export info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("File Size", f"{result.file_size:,} bytes" if result.file_size else "N/A")
                with col2:
                    st.metric("Export Time", f"{result.export_time:.2f}s" if result.export_time else "N/A")
                with col3:
                    st.metric("Messages", result.message_count or 0)
                
                # Download link
                if result.file_path and os.path.exists(result.file_path):
                    with open(result.file_path, 'rb') as f:
                        file_data = f.read()
                    
                    filename = os.path.basename(result.file_path)
                    
                    # Get MIME type based on format
                    mime_types = {
                        'pdf': 'application/pdf',
                        'markdown': 'text/markdown',
                        'html': 'text/html',
                        'txt': 'text/plain',
                        'json': 'application/json'
                    }
                    
                    mime_type = mime_types.get(format_str, 'application/octet-stream')
                    
                    st.download_button(
                        label=f"📥 Download {filename}",
                        data=file_data,
                        file_name=filename,
                        mime=mime_type,
                        key="download_export"
                    )
                    
                    # Show preview for text-based formats
                    if format_str in ['markdown', 'txt', 'html'] and result.file_size < 50000:  # < 50KB
                        with st.expander("👀 Preview Export"):
                            if format_str == 'html':
                                st.components.v1.html(file_data.decode('utf-8'), height=400, scrolling=True)
                            else:
                                st.code(file_data.decode('utf-8'), language=format_str if format_str != 'txt' else None)
            
            else:
                st.error(f"❌ Export failed: {result.error_message}")
        
        except Exception as e:
            st.error(f"❌ Export error: {str(e)}")
    
    def perform_quick_search(self, query: str):
        """Perform a quick search across conversations."""
        if len(query.strip()) < 2:
            return
        
        try:
            # Search across user's sessions
            results = self.chat_service.search_sessions(
                user_id=st.session_state.user_id,
                query=query,
                search_content=True
            )
            
            st.session_state.search_results = results
            
        except Exception as e:
            st.error(f"Search error: {str(e)}")
    
    def render_advanced_search_panel(self):
        """Render advanced search options panel."""
        st.markdown("**🔎 Advanced Search Options**")
        
        # Search query
        search_query = st.text_input(
            "Search Query",
            placeholder="Enter search terms...",
            key="advanced_search_query"
        )
        
        # Search filters
        col1, col2 = st.columns(2)
        
        with col1:
            search_in_content = st.checkbox(
                "Search in messages",
                value=True,
                key="search_in_content"
            )
            
            search_in_citations = st.checkbox(
                "Search in citations",
                value=True,
                key="search_in_citations"
            )
        
        with col2:
            search_in_titles = st.checkbox(
                "Search in titles",
                value=True,
                key="search_in_titles"
            )
            
            search_in_tags = st.checkbox(
                "Search in tags",
                value=True,
                key="search_in_tags"
            )
        
        # Session status filter
        status_filter = st.selectbox(
            "Session Status",
            options=["all", "active", "completed", "paused"],
            key="search_status_filter"
        )
        
        # Date range
        st.markdown("**📅 Date Range**")
        use_date_filter = st.checkbox("Filter by date range", key="use_date_filter")
        
        if use_date_filter:
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("From", key="search_start_date")
            with col2:
                end_date = st.date_input("To", key="search_end_date")
        
        # Philosophical filters
        st.markdown("**🏛️ Philosophical Filters**")
        
        philosopher_filter = st.multiselect(
            "Philosophers mentioned",
            options=["Plato", "Aristotle", "Kant", "Socrates", "Aquinas", "Descartes", "Hume", "Nietzsche"],
            key="philosopher_filter"
        )
        
        period_filter = st.selectbox(
            "Philosophical Period",
            options=["all", "ancient", "medieval", "modern", "contemporary"],
            key="period_filter"
        )
        
        # Search button
        if st.button("🔍 Search", key="perform_advanced_search", type="primary"):
            if search_query.strip():
                self.perform_advanced_search(
                    query=search_query,
                    search_content=search_in_content,
                    search_citations=search_in_citations,
                    search_titles=search_in_titles,
                    search_tags=search_in_tags,
                    status_filter=status_filter,
                    philosopher_filter=philosopher_filter,
                    period_filter=period_filter,
                    use_date_filter=use_date_filter,
                    start_date=locals().get('start_date'),
                    end_date=locals().get('end_date')
                )
            else:
                st.warning("Please enter a search query")
    
    def perform_advanced_search(self, **search_params):
        """Perform advanced search with filters."""
        try:
            query = search_params.get('query', '')
            
            # Get status filter
            status_filter = None
            if search_params.get('status_filter') != 'all':
                from arete.models.chat_session import SessionStatus
                status_map = {
                    'active': SessionStatus.ACTIVE,
                    'completed': SessionStatus.COMPLETED,
                    'paused': SessionStatus.PAUSED
                }
                status_filter = status_map.get(search_params.get('status_filter'))
            
            # Search sessions
            results = self.chat_service.search_sessions(
                user_id=st.session_state.user_id,
                query=query,
                search_content=search_params.get('search_content', True),
                status_filter=status_filter
            )
            
            # Apply additional filters
            filtered_results = []
            
            for session in results:
                include_session = True
                
                # Philosopher filter
                philosopher_filter = search_params.get('philosopher_filter', [])
                if philosopher_filter:
                    session_content = ' '.join([msg.content.lower() for msg in session.messages])
                    if not any(philosopher.lower() in session_content for philosopher in philosopher_filter):
                        include_session = False
                
                # Period filter
                period_filter = search_params.get('period_filter', 'all')
                if period_filter != 'all' and session.context.philosophical_period != period_filter:
                    include_session = False
                
                # Date filter
                if search_params.get('use_date_filter', False):
                    start_date = search_params.get('start_date')
                    end_date = search_params.get('end_date')
                    
                    if start_date and session.created_at.date() < start_date:
                        include_session = False
                    
                    if end_date and session.created_at.date() > end_date:
                        include_session = False
                
                if include_session:
                    filtered_results.append(session)
            
            st.session_state.search_results = filtered_results
            
            if filtered_results:
                st.success(f"🎉 Found {len(filtered_results)} matching conversation(s)")
            else:
                st.info("📋 No conversations match your search criteria")
            
        except Exception as e:
            st.error(f"Advanced search error: {str(e)}")
    
    def display_search_results(self):
        """Display search results."""
        if not st.session_state.search_results:
            return
        
        st.markdown(f"**📋 Search Results ({len(st.session_state.search_results)})** ")
        
        for i, session in enumerate(st.session_state.search_results[:10]):  # Limit to 10 results
            with st.expander(f"📖 {session.title}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Status:** {session.status.value}")
                    st.write(f"**Created:** {session.created_at.strftime('%Y-%m-%d %H:%M')}")
                    st.write(f"**Messages:** {len(session.messages)}")
                
                with col2:
                    if session.context.current_topic:
                        st.write(f"**Topic:** {session.context.current_topic}")
                    if session.context.philosophical_period:
                        st.write(f"**Period:** {session.context.philosophical_period}")
                
                with col3:
                    if st.button(f"👁️ View", key=f"view_result_{i}"):
                        self.load_session(session.session_id)
                        st.session_state.search_results = []  # Clear search results
                        st.rerun()
                    
                    if len(session.messages) > 0:
                        # Show preview of first message
                        preview = session.messages[0].content[:100] + "..." if len(session.messages[0].content) > 100 else session.messages[0].content
                        st.caption(f"**Preview:** {preview}")
                
                # Show tags if any
                if hasattr(session, 'tags') and session.tags:
                    st.write(f"**Tags:** {', '.join(session.tags)}")
        
        if len(st.session_state.search_results) > 10:
            st.info(f"Showing first 10 results. {len(st.session_state.search_results) - 10} more available.")
        
        # Clear results button
        if st.button("🗑️ Clear Search Results", key="clear_search"):
            st.session_state.search_results = []
            st.rerun()
    
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
    
    def render_sharing_panel(self):
        """Render conversation sharing and collaboration panel."""
        st.markdown("**🔗 Share Conversation**")
        
        if not st.session_state.current_session:
            st.info("No active session to share")
            return
        
        session = st.session_state.current_session
        
        # Share options
        share_type = st.radio(
            "Sharing Type",
            options=["view_only", "collaborative", "public"],
            format_func=lambda x: {
                "view_only": "👁️ View Only",
                "collaborative": "✏️ Collaborative",
                "public": "🌐 Public"
            }[x],
            key="sharing_type"
        )
        
        # Permission settings
        st.markdown("**🔒 Permissions**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            allow_download = st.checkbox(
                "Allow download",
                value=True if share_type in ["view_only", "public"] else False,
                key="allow_download"
            )
            
            allow_copy = st.checkbox(
                "Allow copy text",
                value=True,
                key="allow_copy"
            )
        
        with col2:
            if share_type == "collaborative":
                allow_comments = st.checkbox(
                    "Allow comments",
                    value=True,
                    key="allow_comments"
                )
                
                allow_annotations = st.checkbox(
                    "Allow annotations",
                    value=True,
                    key="allow_annotations"
                )
        
        # Expiration settings
        st.markdown("**⏰ Expiration**")
        
        expiration_type = st.selectbox(
            "Link expires",
            options=["never", "1hour", "1day", "1week", "1month"],
            format_func=lambda x: {
                "never": "Never",
                "1hour": "In 1 hour",
                "1day": "In 1 day", 
                "1week": "In 1 week",
                "1month": "In 1 month"
            }[x],
            key="expiration_type"
        )
        
        # Privacy options
        if share_type != "public":
            st.markdown("**👥 Specific Users**")
            
            user_emails = st.text_area(
                "User emails (one per line)",
                placeholder="user1@example.com\nuser2@example.com",
                key="share_user_emails"
            )
        
        # Generate sharing link
        if st.button("🔗 Generate Sharing Link", key="generate_share_link", type="primary"):
            try:
                # Create permissions object
                permissions = SharePermissions(
                    allow_download=allow_download,
                    allow_copy=allow_copy,
                    allow_comments=share_type == "collaborative" and st.session_state.get("allow_comments", False),
                    allow_annotations=share_type == "collaborative" and st.session_state.get("allow_annotations", False)
                )
                
                # Map share type from string to enum
                share_type_enum = {
                    "view_only": ShareType.VIEW_ONLY,
                    "collaborative": ShareType.COLLABORATIVE,
                    "public": ShareType.PUBLIC
                }[share_type]
                
                # Map expiration from string to enum
                expiration_enum = {
                    "never": ExpirationPeriod.NEVER,
                    "1hour": ExpirationPeriod.ONE_HOUR,
                    "1day": ExpirationPeriod.ONE_DAY,
                    "1week": ExpirationPeriod.ONE_WEEK,
                    "1month": ExpirationPeriod.ONE_MONTH
                }[expiration_type]
                
                # Get authorized users if not public
                authorized_users = []
                if share_type != "public" and 'share_user_emails' in st.session_state:
                    user_emails_text = st.session_state.get('share_user_emails', '')
                    authorized_users = [email.strip() for email in user_emails_text.split('\n') if email.strip()]
                
                # Create the share using the service
                shared_conversation = self.sharing_service.create_share(
                    session_id=session.session_id,
                    owner_user_id=st.session_state.user_id,
                    share_type=share_type_enum,
                    permissions=permissions,
                    expiration=expiration_enum,
                    authorized_users=authorized_users
                )
                
                # Generate the sharing URL
                sharing_url = self.sharing_service.generate_sharing_url(shared_conversation.share_id)
                
                # Display the sharing link
                st.success("🎉 Sharing link generated!")
                st.code(sharing_url, language=None)
                
                # Copy to clipboard button (JavaScript required)
                st.markdown(f"""
                <script>
                function copyToClipboard() {{
                    navigator.clipboard.writeText('{sharing_url}').then(function() {{
                        alert('Link copied to clipboard!');
                    }}, function(err) {{
                        console.error('Could not copy text: ', err);
                    }});
                }}
                </script>
                
                <button onclick="copyToClipboard()" style="
                    background-color: #4CAF50;
                    border: none;
                    color: white;
                    padding: 10px 20px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 14px;
                    margin: 4px 2px;
                    cursor: pointer;
                    border-radius: 4px;
                ">📋 Copy Link</button>
                """, unsafe_allow_html=True)
                
                # Show sharing details
                with st.expander("🔍 Sharing Details"):
                    st.json({
                        "Share ID": shared_conversation.share_id,
                        "Share Type": shared_conversation.share_type.value,
                        "Expiration": shared_conversation.expiration.value,
                        "Permissions": shared_conversation.permissions.to_dict(),
                        "Authorized Users": len(shared_conversation.authorized_users) if shared_conversation.authorized_users else "Public" if shared_conversation.share_type == ShareType.PUBLIC else "None specified"
                    })
                
            except Exception as e:
                st.error(f"❌ Error generating sharing link: {str(e)}")
        
        # Display existing shared links
        existing_shares = self.sharing_service.get_shares_by_session(session.session_id)
        
        if existing_shares:
            st.markdown("**📋 Previously Shared Links**")
            
            for shared_conv in existing_shares:
                with st.expander(f"🔗 {shared_conv.share_type.value.replace('_', ' ').title()} Share - {shared_conv.share_id}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        sharing_url = self.sharing_service.generate_sharing_url(shared_conv.share_id)
                        st.code(sharing_url)
                        
                        status_indicator = "🟢 Active" if shared_conv.is_accessible() else "🔴 Inactive"
                        if shared_conv.is_revoked:
                            status_indicator = "❌ Revoked"
                        elif shared_conv.is_expired():
                            status_indicator = "⏰ Expired"
                        
                        st.caption(f"Status: {status_indicator} | Type: {shared_conv.share_type.value} | Expires: {shared_conv.expiration.value}")
                        st.caption(f"Created: {shared_conv.created_at.strftime('%Y-%m-%d %H:%M')} | Accessed: {shared_conv.access_count} times")
                    
                    with col2:
                        if shared_conv.is_accessible() and st.button("🗑️ Revoke", key=f"revoke_{shared_conv.share_id}"):
                            success = self.sharing_service.revoke_share(shared_conv.share_id, st.session_state.user_id)
                            if success:
                                st.success("Link revoked!")
                                st.rerun()
                            else:
                                st.error("Failed to revoke link")
        else:
            st.info("No existing shares for this conversation")
        
        # Collaboration features for collaborative shares
        if share_type == "collaborative":
            st.markdown("**💬 Collaboration Features**")
            
            st.info("""
            **Collaborative Features Available:**
            - 👥 Multiple users can view the conversation
            - 💬 Users can add comments to specific messages
            - 📝 Users can add annotations and highlights
            - 🔔 Real-time notifications for new activity
            - 📊 Activity tracking and contributor insights
            """)

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