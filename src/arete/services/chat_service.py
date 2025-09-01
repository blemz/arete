"""
Chat service for managing philosophical tutoring sessions.

Provides session management, message handling, and conversation flow
for the Arete Graph-RAG philosophical tutoring system.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from ..models.chat_session import ChatSession, ChatMessage, SessionStatus, ChatContext, MessageType


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
        limit: Optional[int] = None,
        bookmarked_only: bool = False,
        sort_by: str = "updated_at"
    ) -> List[ChatSession]:
        """List sessions for a user with enhanced filtering options."""
        session_ids = self._user_sessions.get(user_id, [])
        sessions = []
        
        for session_id in session_ids:
            session = self._sessions.get(session_id)
            if session:
                # Apply status filter if specified
                if status_filter is not None and session.status != status_filter:
                    continue
                
                # Apply bookmark filter if specified
                if bookmarked_only and not session.is_bookmarked:
                    continue
                
                sessions.append(session)
        
        # Sort by specified field
        if sort_by == "updated_at":
            sessions.sort(key=lambda s: s.updated_at, reverse=True)
        elif sort_by == "created_at":
            sessions.sort(key=lambda s: s.created_at, reverse=True)
        elif sort_by == "last_accessed":
            sessions.sort(key=lambda s: s.last_accessed, reverse=True)
        elif sort_by == "access_count":
            sessions.sort(key=lambda s: s.access_count, reverse=True)
        elif sort_by == "title":
            sessions.sort(key=lambda s: s.title.lower())
        
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
        search_content: bool = True,
        status_filter: Optional[SessionStatus] = None
    ) -> List[ChatSession]:
        """Search sessions by title, content, tags, and citations."""
        sessions = self.list_user_sessions(user_id)
        results = []
        
        query_lower = query.lower()
        
        for session in sessions:
            # Apply status filter if specified
            if status_filter is not None and session.status != status_filter:
                continue
            
            match_found = False
            
            # Search in title
            if query_lower in session.title.lower():
                match_found = True
            
            # Search in tags
            elif any(query_lower in tag.lower() for tag in session.tags):
                match_found = True
            
            # Search in summary
            elif session.summary and query_lower in session.summary.lower():
                match_found = True
            
            # Search in message content and citations if enabled
            elif search_content:
                for message in session.messages:
                    if (query_lower in message.content.lower() or 
                        any(query_lower in citation.lower() for citation in message.citations)):
                        match_found = True
                        break
            
            if match_found:
                results.append(session)
        
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
    
    # Enhanced UX Features
    
    def bookmark_session(self, session_id: str, bookmarked: bool = True) -> bool:
        """Bookmark or unbookmark a session."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.bookmark(bookmarked)
        return True
    
    def add_session_tags(self, session_id: str, tags: List[str]) -> bool:
        """Add tags to a session."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.add_tags(tags)
        return True
    
    def remove_session_tags(self, session_id: str, tags: List[str]) -> bool:
        """Remove tags from a session."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.remove_tags(tags)
        return True
    
    def search_sessions_by_tags(self, user_id: str, tags: List[str]) -> List[ChatSession]:
        """Search sessions by tags."""
        sessions = self.list_user_sessions(user_id)
        results = []
        
        tags_lower = [tag.lower() for tag in tags]
        
        for session in sessions:
            session_tags_lower = [tag.lower() for tag in session.tags]
            
            # Check if any of the search tags match session tags
            if any(tag in session_tags_lower for tag in tags_lower):
                results.append(session)
        
        return results
    
    def get_conversation_history(
        self, 
        session_id: str, 
        limit: Optional[int] = None, 
        offset: int = 0
    ) -> List[ChatMessage]:
        """Get paginated conversation history for a session."""
        session = self.get_session(session_id)
        if not session:
            return []
        
        # Sort messages chronologically
        messages = sorted(session.messages, key=lambda m: m.timestamp)
        
        # Apply pagination
        if limit:
            end_index = offset + limit
            return messages[offset:end_index]
        else:
            return messages[offset:]
    
    def get_conversation_thread(
        self, 
        session_id: str, 
        message_id: str, 
        context_size: int = 3
    ) -> List[ChatMessage]:
        """Get conversation thread around a specific message."""
        session = self.get_session(session_id)
        if not session:
            return []
        
        return session.get_message_thread(message_id, context_size)
    
    def get_session_activity_timeline(self, session_id: str) -> List[Dict[str, Any]]:
        """Get chronological timeline of session activity."""
        session = self.get_session(session_id)
        if not session:
            return []
        
        return session.get_conversation_timeline()
    
    def generate_conversation_summary(self, session_id: str) -> Optional[str]:
        """Generate a summary of the conversation (placeholder for AI implementation)."""
        session = self.get_session(session_id)
        if not session or not session.messages:
            return None
        
        # Simple summary generation (to be enhanced with AI)
        philosophers = []
        user_questions = []
        
        for message in session.messages:
            content_lower = message.content.lower()
            
            # Extract potential philosophers mentioned
            for philosopher in ["plato", "aristotle", "kant", "socrates", "aquinas", "descartes", "hume", "nietzsche"]:
                if philosopher in content_lower and philosopher not in [p.lower() for p in philosophers]:
                    philosophers.append(philosopher.title())
            
            # Extract user questions
            if message.message_type == MessageType.USER and "?" in message.content:
                user_questions.append(message.content[:100] + "..." if len(message.content) > 100 else message.content)
        
        summary_parts = []
        
        if philosophers:
            summary_parts.append(f"Philosophers discussed: {', '.join(philosophers)}")
        
        if session.context.current_topic:
            summary_parts.append(f"Main topic: {session.context.current_topic}")
        
        if user_questions:
            summary_parts.append(f"Key questions explored: {len(user_questions)}")
        
        summary_parts.append(f"Total messages: {len(session.messages)}")
        
        return "; ".join(summary_parts) if summary_parts else "Philosophical discussion session"
    
    def get_detailed_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get detailed statistics for a user's sessions."""
        sessions = self.list_user_sessions(user_id)
        
        if not sessions:
            return {
                "total_sessions": 0,
                "active_sessions": 0,
                "completed_sessions": 0,
                "paused_sessions": 0,
                "bookmarked_sessions": 0,
                "total_messages": 0,
                "average_messages_per_session": 0,
                "most_recent_session": None,
                "most_recent_activity": None,
                "most_active_period": "N/A",
                "average_session_length": 0
            }
        
        total_sessions = len(sessions)
        active_sessions = len([s for s in sessions if s.status == SessionStatus.ACTIVE])
        completed_sessions = len([s for s in sessions if s.status == SessionStatus.COMPLETED])
        paused_sessions = len([s for s in sessions if s.status == SessionStatus.PAUSED])
        bookmarked_sessions = len([s for s in sessions if s.is_bookmarked])
        total_messages = sum(len(s.messages) for s in sessions)
        
        # Calculate most active period (simplified)
        most_active_period = "Morning"  # Placeholder - could analyze message timestamps
        
        # Calculate average session length in messages
        average_session_length = total_messages / total_sessions if total_sessions > 0 else 0
        
        most_recent = sessions[0] if sessions else None
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "completed_sessions": completed_sessions,
            "paused_sessions": paused_sessions,
            "bookmarked_sessions": bookmarked_sessions,
            "total_messages": total_messages,
            "average_messages_per_session": total_messages / total_sessions if total_sessions > 0 else 0,
            "most_recent_session": most_recent.session_id if most_recent else None,
            "most_recent_activity": most_recent.updated_at if most_recent else None,
            "most_active_period": most_active_period,
            "average_session_length": average_session_length
        }
    
    def analyze_philosophical_topics(self, session_id: str) -> Dict[str, Any]:
        """Analyze philosophical topics and themes in a session."""
        session = self.get_session(session_id)
        if not session:
            return {"topics": [], "philosophers_mentioned": [], "ethical_themes": []}
        
        philosophers_mentioned = []
        ethical_themes = []
        topics = []
        
        # Known philosophers and their topics
        philosopher_map = {
            "aristotle": ["virtue ethics", "ethics", "politics", "metaphysics"],
            "plato": ["forms", "justice", "republic", "cave allegory"],
            "kant": ["categorical imperative", "deontology", "transcendental"],
            "socrates": ["dialogue", "questioning", "virtue", "knowledge"],
            "aquinas": ["natural law", "scholasticism", "theology"],
            "descartes": ["cogito", "dualism", "skepticism"],
            "hume": ["empiricism", "causation", "skepticism"],
            "nietzsche": ["will to power", "eternal recurrence", "nihilism"]
        }
        
        ethical_keywords = ["virtue", "justice", "good", "evil", "moral", "ethical", "duty", "right", "wrong"]
        
        all_content = " ".join([msg.content.lower() for msg in session.messages])
        
        # Find philosophers
        for philosopher, related_topics in philosopher_map.items():
            if philosopher in all_content:
                philosophers_mentioned.append(philosopher.title())
                topics.extend([topic for topic in related_topics if topic in all_content])
        
        # Find ethical themes
        ethical_themes = [theme for theme in ethical_keywords if theme in all_content]
        
        # Add session context topic if available
        if session.context.current_topic:
            topics.append(session.context.current_topic)
        
        return {
            "topics": list(set(topics)),  # Remove duplicates
            "philosophers_mentioned": philosophers_mentioned,
            "ethical_themes": list(set(ethical_themes))
        }
    
    def prepare_session_for_sharing(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Prepare session data for sharing or collaboration."""
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Generate a shareable summary
        share_data = {
            "session_id": session.session_id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "message_count": len(session.messages),
            "summary": session.summary or self.generate_conversation_summary(session_id),
            "tags": session.tags,
            "context": {
                "topic": session.context.current_topic,
                "period": session.context.philosophical_period,
                "level": session.context.student_level
            },
            "shareable_link": f"arete://session/{session.session_id}"  # Placeholder URL scheme
        }
        
        return share_data