#!/usr/bin/env python3
"""
Demo script for testing chat interface functionality.

This demonstrates the chat session management and basic interface
components without running the full Streamlit app.
"""

from src.arete.models.chat_session import ChatSession, ChatMessage, ChatContext, MessageType
from src.arete.services.chat_service import ChatService
from src.arete.ui.streamlit_app import AreteStreamlitInterface
import uuid
from datetime import datetime


def demo_chat_functionality():
    """Demonstrate chat functionality."""
    print("Arete Chat Interface Demo")
    print("=" * 40)
    
    # Initialize chat service
    chat_service = ChatService()
    user_id = f"demo_user_{uuid.uuid4().hex[:8]}"
    
    # Create a demo session
    print("Creating demo session...")
    context = ChatContext(
        student_level="undergraduate",
        philosophical_period="ancient",
        current_topic="virtue ethics",
        learning_objectives=["understand Aristotelian virtue", "explore practical wisdom"]
    )
    
    session = chat_service.create_session(
        user_id=user_id,
        title="Demo: Virtue Ethics Discussion",
        context=context
    )
    
    print(f"Created session: {session.session_id}")
    print(f"   Title: {session.title}")
    print(f"   Context: {session.context.student_level}, {session.context.philosophical_period}")
    
    # Add some demo messages
    print("\nAdding demo messages...")
    
    # User message
    user_msg = ChatMessage(
        message_id=f"msg_{uuid.uuid4().hex[:8]}",
        content="What is virtue according to Aristotle?",
        message_type=MessageType.USER,
        timestamp=datetime.now(),
        user_id=user_id
    )
    
    session.add_message(user_msg)
    print(f"User: {user_msg.content}")
    
    # Assistant response
    assistant_msg = ChatMessage(
        message_id=f"msg_{uuid.uuid4().hex[:8]}",
        content="According to Aristotle in the Nicomachean Ethics, virtue (arete) is a disposition to act excellently, acquired through habit and practice. Virtue lies in the mean between extremes of excess and deficiency.",
        message_type=MessageType.ASSISTANT,
        timestamp=datetime.now(),
        citations=["Ethics 1103a", "Ethics 1107a"],
        metadata={
            "provider": "demo",
            "response_time": 1.5,
            "token_count": 45
        }
    )
    
    session.add_message(assistant_msg)
    print(f"Assistant: {assistant_msg.content}")
    print(f"Citations: {', '.join(assistant_msg.citations)}")
    
    # Test session management
    print(f"\nSession Statistics:")
    print(f"   Messages: {len(session.messages)}")
    print(f"   Status: {session.status.value}")
    print(f"   Created: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Updated: {session.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test service functionality
    print(f"\nTesting service functionality...")
    
    # List user sessions
    user_sessions = chat_service.list_user_sessions(user_id)
    print(f"   User has {len(user_sessions)} sessions")
    
    # Search sessions
    search_results = chat_service.search_sessions(user_id, "virtue")
    print(f"   Found {len(search_results)} sessions containing 'virtue'")
    
    # Get session statistics
    stats = chat_service.get_session_statistics(user_id)
    print(f"   Statistics: {stats}")
    
    print(f"\nDemo completed successfully!")
    print(f"Ready to launch Streamlit interface with: python run_streamlit.py")


if __name__ == "__main__":
    demo_chat_functionality()