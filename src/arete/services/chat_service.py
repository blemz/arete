"""
Chat service for managing philosophical tutoring sessions.

Provides session management, message handling, and conversation flow
for the Arete Graph-RAG philosophical tutoring system.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from ..models.chat_session import ChatSession, ChatMessage, SessionStatus, ChatContext


class ChatService:
    """Service for managing chat sessions and conversations."""
    
    def __init__(self):
        """Initialize chat service."""
        # In-memory storage for sessions (to be replaced with persistent storage)
        self._sessions: Dict[str, ChatSession] = {}
        self._user_sessions: Dict[str, List[str]] = {}  # user_id -> [session_ids]
    
    def create_session(
        self, 
        user_id: str, 
        title: str,
        context: Optional[ChatContext] = None
    ) -> ChatSession:
        """Create a new chat session."""
        session_id = str(uuid.uuid4())
        
        session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            title=title,
            context=context or ChatContext()
        )
        
        # Store session
        self._sessions[session_id] = session
        
        # Track user sessions
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = []
        self._user_sessions[user_id].append(session_id)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Retrieve a session by ID."""
        return self._sessions.get(session_id)
    
    def list_user_sessions(
        self, 
        user_id: str, 
        status_filter: Optional[SessionStatus] = None,
        limit: Optional[int] = None
    ) -> List[ChatSession]:
        """List sessions for a user."""
        session_ids = self._user_sessions.get(user_id, [])
        sessions = []
        
        for session_id in session_ids:
            session = self._sessions.get(session_id)
            if session:
                # Apply status filter if specified
                if status_filter is None or session.status == status_filter:
                    sessions.append(session)
        
        # Sort by updated_at descending (most recent first)
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        
        # Apply limit if specified
        if limit:
            sessions = sessions[:limit]
        
        return sessions
    
    def update_session(
        self,
        session_id: str,
        title: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        context: Optional[ChatContext] = None
    ) -> Optional[ChatSession]:
        """Update session properties."""
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Update properties
        if title is not None:
            session.title = title
        
        if status is not None:
            session.status = status
        
        if context is not None:
            session.context = context
        
        # Update timestamp with small delay to ensure different timestamps
        import time
        time.sleep(0.001)
        session.updated_at = datetime.now()
        
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Remove from storage
        del self._sessions[session_id]
        
        # Remove from user sessions
        user_id = session.user_id
        if user_id in self._user_sessions:
            self._user_sessions[user_id] = [
                sid for sid in self._user_sessions[user_id] 
                if sid != session_id
            ]
        
        return True
    
    def add_message_to_session(
        self, 
        session_id: str, 
        message: ChatMessage
    ) -> Optional[ChatSession]:
        """Add a message to a session."""
        session = self.get_session(session_id)
        if not session:
            return None
        
        session.add_message(message)
        return session
    
    def search_sessions(
        self, 
        user_id: str, 
        query: str, 
        search_content: bool = True
    ) -> List[ChatSession]:
        """Search sessions by title or content."""
        sessions = self.list_user_sessions(user_id)
        results = []
        
        query_lower = query.lower()
        
        for session in sessions:
            # Search in title
            if query_lower in session.title.lower():
                results.append(session)
                continue
            
            # Search in message content if enabled
            if search_content:
                for message in session.messages:
                    if query_lower in message.content.lower():
                        results.append(session)
                        break
        
        return results
    
    def cleanup_inactive_sessions(self, days_threshold: int = 30) -> int:
        """Clean up sessions inactive for specified days."""
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        cleanup_count = 0
        
        # Find sessions to clean up
        sessions_to_delete = []
        for session_id, session in self._sessions.items():
            if session.updated_at < cutoff_date and session.status != SessionStatus.ACTIVE:
                sessions_to_delete.append(session_id)
        
        # Delete inactive sessions
        for session_id in sessions_to_delete:
            if self.delete_session(session_id):
                cleanup_count += 1
        
        return cleanup_count
    
    def get_session_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for user's sessions."""
        sessions = self.list_user_sessions(user_id)
        
        total_sessions = len(sessions)
        active_sessions = len([s for s in sessions if s.status == SessionStatus.ACTIVE])
        total_messages = sum(len(s.messages) for s in sessions)
        
        # Find most recent session
        most_recent = sessions[0] if sessions else None
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "completed_sessions": len([s for s in sessions if s.status == SessionStatus.COMPLETED]),
            "paused_sessions": len([s for s in sessions if s.status == SessionStatus.PAUSED]),
            "total_messages": total_messages,
            "average_messages_per_session": total_messages / total_sessions if total_sessions > 0 else 0,
            "most_recent_session": most_recent.session_id if most_recent else None,
            "most_recent_activity": most_recent.updated_at if most_recent else None
        }
    
    def export_session(self, session_id: str, format: str = "dict") -> Optional[Dict[str, Any]]:
        """Export session data in specified format."""
        session = self.get_session(session_id)
        if not session:
            return None
        
        if format == "dict":
            return session.to_dict()
        
        # Add other export formats as needed
        return session.to_dict()
    
    def import_session(self, session_data: Dict[str, Any]) -> ChatSession:
        """Import session from data."""
        session = ChatSession.from_dict(session_data)
        
        # Store imported session
        self._sessions[session.session_id] = session
        
        # Track user sessions
        user_id = session.user_id
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = []
        
        if session.session_id not in self._user_sessions[user_id]:
            self._user_sessions[user_id].append(session.session_id)
        
        return session