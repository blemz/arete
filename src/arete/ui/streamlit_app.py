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
from ..models.chat_session import ChatSession, ChatMessage, ChatContext, MessageType, SessionStatus
from ..services.chat_service import ChatService


class AreteStreamlitInterface:
    """Main Streamlit interface for Arete philosophical tutoring."""
    
    def __init__(self):
        """Initialize the Streamlit interface."""
        self.chat_service = ChatService()
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
            
            # Statistics
            if st.session_state.current_session:
                st.subheader("📊 Session Stats")
                message_count = len(st.session_state.current_session.messages)
                st.metric("Messages", message_count)
                
                if message_count > 0:
                    citation_count = sum(len(msg.citations) for msg in st.session_state.current_session.messages)
                    st.metric("Citations", citation_count)
    
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
        """Generate assistant response (placeholder - will integrate with RAG pipeline)."""
        with st.chat_message("assistant"):
            # Show typing indicator
            with st.spinner("🤔 Thinking about your philosophical question..."):
                time.sleep(2)  # Simulate processing time
            
            # Placeholder response (to be replaced with RAG pipeline integration)
            response_content = self.get_placeholder_response(user_input)
            
            st.write(response_content)
            
            # Placeholder citations
            citations = ["Republic 514a", "Ethics 1103a"]
            if citations:
                st.markdown("**Sources:**")
                for citation in citations:
                    st.markdown(f'<div class="citation">📜 {citation}</div>', 
                               unsafe_allow_html=True)
        
        # Create assistant message
        assistant_message = ChatMessage(
            message_id=f"msg_{uuid.uuid4().hex[:8]}",
            content=response_content,
            message_type=MessageType.ASSISTANT,
            timestamp=datetime.now(),
            citations=citations,
            metadata={
                "provider": "placeholder",
                "response_time": 2.0,
                "token_count": len(response_content.split()) * 2
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
    
    def get_placeholder_response(self, user_input: str) -> str:
        """Generate placeholder response based on keywords (will be replaced with RAG)."""
        user_lower = user_input.lower()
        
        if "virtue" in user_lower or "aristotle" in user_lower:
            return """According to Aristotle in the Nicomachean Ethics, virtue (arete) is a disposition to act excellently, acquired through habit and practice. Virtue lies in the mean between extremes of excess and deficiency - for example, courage is the mean between cowardice and recklessness."""
        
        elif "cave" in user_lower or "plato" in user_lower:
            return """In Plato's Allegory of the Cave from Book VII of the Republic, prisoners chained in a cave mistake shadows on the wall for reality. This represents how most people mistake the material world for true reality, when they should be seeking the eternal Forms through philosophical contemplation."""
        
        elif "justice" in user_lower:
            return """Plato defines justice in the Republic as each part of the soul doing its proper function: reason ruling, spirit supporting reason, and appetite being controlled. This creates harmony within the individual, just as justice in the state occurs when each class performs its proper role."""
        
        elif "good" in user_lower or "form" in user_lower:
            return """The Form of the Good, according to Plato, is the highest of all Forms and the source of all truth and reality. Just as the sun illuminates the visible world, the Form of the Good illuminates the intelligible world of Forms, making knowledge possible."""
        
        else:
            return f"""That's an excellent philosophical question about "{user_input}". This touches on fundamental questions that have engaged philosophers for millennia. Let me help you explore the different perspectives on this topic, drawing from both ancient and contemporary philosophical traditions."""
    
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
        
        # Render main content
        if st.session_state.current_session or st.session_state.messages:
            self.render_chat_interface()
        else:
            self.render_welcome_message()


def main():
    """Main function to run the Streamlit app."""
    app = AreteStreamlitInterface()
    app.run()


if __name__ == "__main__":
    main()