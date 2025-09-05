"""
Chat Service for handling conversational interactions with RAG pipeline.
"""

import asyncio
from typing import Dict, Any, List
from .rag_service import get_rag_service


class ChatService:
    """Service for handling chat interactions with RAG integration."""
    
    def __init__(self):
        """Initialize chat service."""
        self.rag_service = get_rag_service()
        self.conversation_history: List[Dict[str, Any]] = []
    
    async def send_message(self, message: str, user_id: str = "default") -> Dict[str, Any]:
        """Send a message and get RAG-powered response."""
        try:
            # Add user message to history
            user_entry = {
                "role": "user",
                "content": message,
                "timestamp": asyncio.get_event_loop().time()
            }
            self.conversation_history.append(user_entry)
            
            # Process query through RAG
            rag_result = await self.rag_service.process_query(message)
            
            # Create assistant response
            assistant_entry = {
                "role": "assistant",
                "content": rag_result["response"],
                "citations": rag_result.get("citations", []),
                "entities": rag_result.get("entities", []),
                "timestamp": asyncio.get_event_loop().time()
            }
            self.conversation_history.append(assistant_entry)
            
            return {
                "success": True,
                "response": rag_result["response"],
                "citations": rag_result.get("citations", []),
                "entities": rag_result.get("entities", []),
                "message_id": len(self.conversation_history) - 1
            }
            
        except Exception as e:
            error_response = f"I apologize, but I encountered an error processing your question: {str(e)}"
            
            # Still add to history for continuity
            error_entry = {
                "role": "assistant",
                "content": error_response,
                "citations": [],
                "entities": [],
                "timestamp": asyncio.get_event_loop().time(),
                "error": True
            }
            self.conversation_history.append(error_entry)
            
            return {
                "success": False,
                "response": error_response,
                "citations": [],
                "entities": [],
                "error": str(e)
            }
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the complete conversation history."""
        return self.conversation_history.copy()
    
    def clear_conversation(self):
        """Clear the conversation history."""
        self.conversation_history.clear()
    
    def get_recent_context(self, max_messages: int = 6) -> str:
        """Get recent conversation context for improved responses."""
        recent_messages = self.conversation_history[-max_messages:]
        
        context_parts = []
        for msg in recent_messages:
            role = msg["role"]
            content = msg["content"][:500]  # Truncate long messages
            context_parts.append(f"{role.capitalize()}: {content}")
        
        return "\n".join(context_parts)
    
    async def get_suggested_followups(self, last_response: str) -> List[str]:
        """Generate suggested follow-up questions based on the last response."""
        try:
            # Simple rule-based suggestions for now
            suggestions = []
            
            if "virtue" in last_response.lower():
                suggestions.extend([
                    "How does Aristotle's view of virtue differ from Plato's?",
                    "What are the cardinal virtues in classical philosophy?",
                    "Can virtue be taught according to Socrates?"
                ])
            
            if "justice" in last_response.lower():
                suggestions.extend([
                    "What is distributive justice according to Aristotle?",
                    "How does Plato define justice in the Republic?",
                    "What is the relationship between justice and virtue?"
                ])
            
            if "knowledge" in last_response.lower():
                suggestions.extend([
                    "What is the difference between knowledge and opinion?",
                    "How does Socratic ignorance relate to true knowledge?",
                    "What is Plato's theory of Forms?"
                ])
            
            # Default philosophical questions
            if not suggestions:
                suggestions = [
                    "Tell me about the Socratic method",
                    "What is the allegory of the cave?",
                    "How did ancient philosophers view happiness?",
                    "What is the role of reason in ethics?"
                ]
            
            return suggestions[:3]  # Return top 3 suggestions
            
        except Exception as e:
            return ["What other philosophical concepts interest you?"]


# Global chat service instance
_chat_service = None

def get_chat_service() -> ChatService:
    """Get the global chat service instance."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service