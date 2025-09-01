"""
Service for managing conversation sharing and collaboration.

Provides functionality for creating shared conversation links,
managing permissions, and handling collaborative features.
"""

import hashlib
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from arete.models.sharing_models import (
    SharedConversation, 
    ShareComment, 
    ShareAnnotation,
    ShareType, 
    ExpirationPeriod, 
    SharePermissions
)
from arete.services.chat_service import ChatService


class ConversationSharingService:
    """Service for conversation sharing and collaboration management."""
    
    def __init__(self, chat_service: ChatService):
        """Initialize the sharing service."""
        self.chat_service = chat_service
        # In a real implementation, these would be database repositories
        self._shared_conversations: Dict[str, SharedConversation] = {}
        self._share_comments: Dict[str, List[ShareComment]] = {}
        self._share_annotations: Dict[str, List[ShareAnnotation]] = {}
    
    def create_share(
        self,
        session_id: str,
        owner_user_id: str,
        share_type: ShareType,
        permissions: SharePermissions,
        expiration: ExpirationPeriod = ExpirationPeriod.NEVER,
        authorized_users: List[str] = None,
        password: Optional[str] = None
    ) -> SharedConversation:
        """Create a new shared conversation."""
        if authorized_users is None:
            authorized_users = []
        
        # Verify session exists and belongs to user
        session = self.chat_service.get_session(session_id)
        if not session or session.user_id != owner_user_id:
            raise ValueError(f"Session {session_id} not found or not accessible")
        
        # Generate unique share ID
        share_id = self._generate_share_id(session_id, share_type)
        
        # Handle password protection
        password_hash = None
        if password:
            password_hash = self._hash_password(password)
        
        # Create shared conversation
        shared_conversation = SharedConversation(
            share_id=share_id,
            session_id=session_id,
            owner_user_id=owner_user_id,
            share_type=share_type,
            permissions=permissions,
            expiration=expiration,
            authorized_users=authorized_users,
            is_password_protected=bool(password),
            password_hash=password_hash
        )
        
        # Post-init to set expiration date
        if hasattr(shared_conversation, '__post_init__'):
            shared_conversation.__post_init__()
        
        # Store the share
        self._shared_conversations[share_id] = shared_conversation
        
        return shared_conversation
    
    def get_share(self, share_id: str) -> Optional[SharedConversation]:
        """Get a shared conversation by ID."""
        return self._shared_conversations.get(share_id)
    
    def get_shares_by_session(self, session_id: str) -> List[SharedConversation]:
        """Get all shares for a specific session."""
        return [
            share for share in self._shared_conversations.values()
            if share.session_id == session_id
        ]
    
    def get_shares_by_owner(self, owner_user_id: str) -> List[SharedConversation]:
        """Get all shares created by a specific user."""
        return [
            share for share in self._shared_conversations.values()
            if share.owner_user_id == owner_user_id
        ]
    
    def access_share(
        self, 
        share_id: str, 
        user_email: Optional[str] = None,
        password: Optional[str] = None
    ) -> Tuple[Optional[SharedConversation], str]:
        """
        Access a shared conversation.
        
        Returns:
            Tuple of (SharedConversation, error_message) where error_message is empty on success
        """
        share = self.get_share(share_id)
        if not share:
            return None, "Share not found"
        
        # Check if share is accessible
        if not share.is_accessible():
            if share.is_revoked:
                return None, "This share has been revoked"
            elif share.is_expired():
                return None, "This share has expired"
            else:
                return None, "This share is no longer available"
        
        # Check password protection
        if share.is_password_protected:
            if not password:
                return None, "Password required"
            if not self._verify_password(password, share.password_hash):
                return None, "Incorrect password"
        
        # Check user access
        if not share.can_access(user_email):
            return None, "Access denied - you are not authorized to view this conversation"
        
        # Record access
        share.record_access(user_email)
        
        return share, ""
    
    def revoke_share(self, share_id: str, owner_user_id: str) -> bool:
        """Revoke a shared conversation."""
        share = self.get_share(share_id)
        if not share or share.owner_user_id != owner_user_id:
            return False
        
        share.revoke()
        return True
    
    def update_share_permissions(
        self, 
        share_id: str, 
        owner_user_id: str, 
        new_permissions: SharePermissions
    ) -> bool:
        """Update permissions for a shared conversation."""
        share = self.get_share(share_id)
        if not share or share.owner_user_id != owner_user_id:
            return False
        
        share.permissions = new_permissions
        return True
    
    def extend_share_expiration(
        self, 
        share_id: str, 
        owner_user_id: str, 
        new_expiration: ExpirationPeriod
    ) -> bool:
        """Extend the expiration of a shared conversation."""
        share = self.get_share(share_id)
        if not share or share.owner_user_id != owner_user_id:
            return False
        
        share.extend_expiration(new_expiration)
        return True
    
    def add_authorized_user(
        self, 
        share_id: str, 
        owner_user_id: str, 
        user_email: str
    ) -> bool:
        """Add an authorized user to a shared conversation."""
        share = self.get_share(share_id)
        if not share or share.owner_user_id != owner_user_id:
            return False
        
        if user_email not in share.authorized_users:
            share.authorized_users.append(user_email)
        return True
    
    def remove_authorized_user(
        self, 
        share_id: str, 
        owner_user_id: str, 
        user_email: str
    ) -> bool:
        """Remove an authorized user from a shared conversation."""
        share = self.get_share(share_id)
        if not share or share.owner_user_id != owner_user_id:
            return False
        
        if user_email in share.authorized_users:
            share.authorized_users.remove(user_email)
        return True
    
    # Comment management methods
    
    def add_comment(
        self,
        share_id: str,
        content: str,
        author_email: str,
        author_name: Optional[str] = None,
        message_id: Optional[str] = None,
        message_position: Optional[int] = None,
        parent_comment_id: Optional[str] = None
    ) -> Optional[ShareComment]:
        """Add a comment to a shared conversation."""
        share = self.get_share(share_id)
        if not share or not share.permissions.allow_comments:
            return None
        
        # Check if user can access the share
        if not share.can_access(author_email):
            return None
        
        # Generate comment ID
        comment_id = f"comment_{int(time.time())}_{hashlib.md5(author_email.encode()).hexdigest()[:8]}"
        
        comment = ShareComment(
            comment_id=comment_id,
            share_id=share_id,
            message_id=message_id,
            content=content,
            author_email=author_email,
            author_name=author_name,
            message_position=message_position,
            parent_comment_id=parent_comment_id
        )
        
        if share_id not in self._share_comments:
            self._share_comments[share_id] = []
        self._share_comments[share_id].append(comment)
        
        return comment
    
    def get_comments(self, share_id: str) -> List[ShareComment]:
        """Get all comments for a shared conversation."""
        return self._share_comments.get(share_id, [])
    
    def get_comments_for_message(self, share_id: str, message_id: str) -> List[ShareComment]:
        """Get comments for a specific message."""
        all_comments = self.get_comments(share_id)
        return [comment for comment in all_comments if comment.message_id == message_id]
    
    # Annotation management methods
    
    def add_annotation(
        self,
        share_id: str,
        message_id: str,
        annotation_type: str,
        selected_text: str,
        start_position: int,
        end_position: int,
        author_email: str,
        content: Optional[str] = None,
        author_name: Optional[str] = None,
        color: str = "yellow"
    ) -> Optional[ShareAnnotation]:
        """Add an annotation to a shared conversation."""
        share = self.get_share(share_id)
        if not share or not share.permissions.allow_annotations:
            return None
        
        # Check if user can access the share
        if not share.can_access(author_email):
            return None
        
        # Generate annotation ID
        annotation_id = f"annotation_{int(time.time())}_{hashlib.md5(author_email.encode()).hexdigest()[:8]}"
        
        annotation = ShareAnnotation(
            annotation_id=annotation_id,
            share_id=share_id,
            message_id=message_id,
            annotation_type=annotation_type,
            content=content,
            selected_text=selected_text,
            start_position=start_position,
            end_position=end_position,
            color=color,
            author_email=author_email,
            author_name=author_name
        )
        
        if share_id not in self._share_annotations:
            self._share_annotations[share_id] = []
        self._share_annotations[share_id].append(annotation)
        
        return annotation
    
    def get_annotations(self, share_id: str) -> List[ShareAnnotation]:
        """Get all annotations for a shared conversation."""
        return self._share_annotations.get(share_id, [])
    
    def get_annotations_for_message(self, share_id: str, message_id: str) -> List[ShareAnnotation]:
        """Get annotations for a specific message."""
        all_annotations = self.get_annotations(share_id)
        return [annotation for annotation in all_annotations if annotation.message_id == message_id]
    
    # Analytics methods
    
    def get_share_analytics(self, share_id: str, owner_user_id: str) -> Dict[str, any]:
        """Get analytics for a shared conversation."""
        share = self.get_share(share_id)
        if not share or share.owner_user_id != owner_user_id:
            return {}
        
        comments_count = len(self.get_comments(share_id))
        annotations_count = len(self.get_annotations(share_id))
        
        return {
            "share_id": share_id,
            "access_count": share.access_count,
            "last_accessed": share.last_accessed,
            "comments_count": comments_count,
            "annotations_count": annotations_count,
            "is_active": share.is_active,
            "expires_at": share.expires_at,
            "days_until_expiration": (share.expires_at - datetime.now()).days if share.expires_at else None
        }
    
    def cleanup_expired_shares(self) -> int:
        """Clean up expired shares and return count of cleaned shares."""
        expired_shares = []
        
        for share_id, share in self._shared_conversations.items():
            if share.is_expired():
                expired_shares.append(share_id)
        
        for share_id in expired_shares:
            del self._shared_conversations[share_id]
            # Clean up associated comments and annotations
            if share_id in self._share_comments:
                del self._share_comments[share_id]
            if share_id in self._share_annotations:
                del self._share_annotations[share_id]
        
        return len(expired_shares)
    
    # Private helper methods
    
    def _generate_share_id(self, session_id: str, share_type: ShareType) -> str:
        """Generate a unique share ID."""
        share_data = f"{session_id}_{share_type.value}_{int(time.time())}"
        return hashlib.md5(share_data.encode()).hexdigest()[:12]
    
    def _hash_password(self, password: str) -> str:
        """Hash a password for storage."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        return hashlib.sha256(password.encode()).hexdigest() == password_hash
    
    def generate_sharing_url(self, share_id: str, base_url: str = "https://arete.app/shared") -> str:
        """Generate a complete sharing URL."""
        return f"{base_url}/{share_id}"
    
    def get_share_statistics(self) -> Dict[str, any]:
        """Get overall sharing statistics."""
        active_shares = sum(1 for share in self._shared_conversations.values() if share.is_accessible())
        total_accesses = sum(share.access_count for share in self._shared_conversations.values())
        
        share_types = {}
        for share in self._shared_conversations.values():
            share_type = share.share_type.value
            share_types[share_type] = share_types.get(share_type, 0) + 1
        
        return {
            "total_shares": len(self._shared_conversations),
            "active_shares": active_shares,
            "total_accesses": total_accesses,
            "share_types": share_types,
            "total_comments": sum(len(comments) for comments in self._share_comments.values()),
            "total_annotations": sum(len(annotations) for annotations in self._share_annotations.values())
        }