"""
Tests for conversation sharing functionality.

Tests sharing models, service, and integration with chat system.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from arete.models.sharing_models import (
    SharedConversation, ShareComment, ShareAnnotation,
    ShareType, ExpirationPeriod, SharePermissions
)
from arete.services.conversation_sharing_service import ConversationSharingService
from arete.services.chat_service import ChatService
from arete.models.chat_session import ChatSession, SessionStatus


class TestSharePermissions:
    """Test SharePermissions model."""
    
    def test_permissions_creation_with_defaults(self):
        """Test creating permissions with default values."""
        permissions = SharePermissions()
        
        assert permissions.allow_download is True
        assert permissions.allow_copy is True
        assert permissions.allow_comments is False
        assert permissions.allow_annotations is False
        assert permissions.allow_highlights is False
        assert permissions.allow_bookmarks is False
    
    def test_permissions_creation_with_custom_values(self):
        """Test creating permissions with custom values."""
        permissions = SharePermissions(
            allow_download=False,
            allow_comments=True,
            allow_annotations=True
        )
        
        assert permissions.allow_download is False
        assert permissions.allow_comments is True
        assert permissions.allow_annotations is True
    
    def test_permissions_serialization(self):
        """Test permissions to_dict and from_dict methods."""
        permissions = SharePermissions(
            allow_download=False,
            allow_comments=True,
            allow_annotations=True
        )
        
        data = permissions.to_dict()
        reconstructed = SharePermissions.from_dict(data)
        
        assert reconstructed.allow_download is False
        assert reconstructed.allow_comments is True
        assert reconstructed.allow_annotations is True


class TestSharedConversation:
    """Test SharedConversation model."""
    
    def test_shared_conversation_creation(self):
        """Test creating a shared conversation."""
        permissions = SharePermissions(allow_comments=True)
        
        shared = SharedConversation(
            share_id="test123",
            session_id="session123",
            owner_user_id="user123",
            share_type=ShareType.COLLABORATIVE,
            permissions=permissions
        )
        
        assert shared.share_id == "test123"
        assert shared.session_id == "session123"
        assert shared.owner_user_id == "user123"
        assert shared.share_type == ShareType.COLLABORATIVE
        assert shared.permissions.allow_comments is True
        assert shared.is_active is True
        assert shared.is_revoked is False
    
    def test_expiration_calculation(self):
        """Test expiration date calculation."""
        permissions = SharePermissions()
        
        # Test one hour expiration
        shared = SharedConversation(
            share_id="test123",
            session_id="session123",
            owner_user_id="user123",
            share_type=ShareType.VIEW_ONLY,
            permissions=permissions,
            expiration=ExpirationPeriod.ONE_HOUR
        )
        
        # Mock __post_init__ call since it's not automatically called in tests
        shared.expires_at = shared._calculate_expiration_date()
        
        assert shared.expires_at is not None
        assert shared.expires_at > datetime.now()
        assert shared.expires_at < datetime.now() + timedelta(hours=2)
    
    def test_is_expired_check(self):
        """Test expiration checking."""
        permissions = SharePermissions()
        
        # Never expires
        shared_never = SharedConversation(
            share_id="test123",
            session_id="session123", 
            owner_user_id="user123",
            share_type=ShareType.VIEW_ONLY,
            permissions=permissions,
            expiration=ExpirationPeriod.NEVER
        )
        
        assert shared_never.is_expired() is False
        
        # Already expired
        shared_expired = SharedConversation(
            share_id="test456",
            session_id="session123",
            owner_user_id="user123", 
            share_type=ShareType.VIEW_ONLY,
            permissions=permissions,
            expiration=ExpirationPeriod.ONE_HOUR,
            expires_at=datetime.now() - timedelta(hours=1)
        )
        
        assert shared_expired.is_expired() is True
    
    def test_accessibility_check(self):
        """Test accessibility checking."""
        permissions = SharePermissions()
        
        # Active and accessible
        shared = SharedConversation(
            share_id="test123",
            session_id="session123",
            owner_user_id="user123",
            share_type=ShareType.VIEW_ONLY,
            permissions=permissions
        )
        
        assert shared.is_accessible() is True
        
        # Revoked - not accessible
        shared.revoke()
        assert shared.is_accessible() is False
    
    def test_can_access_public_share(self):
        """Test access control for public shares."""
        permissions = SharePermissions()
        
        shared = SharedConversation(
            share_id="test123",
            session_id="session123",
            owner_user_id="user123",
            share_type=ShareType.PUBLIC,
            permissions=permissions
        )
        
        # Public shares are accessible to anyone
        assert shared.can_access(None) is True
        assert shared.can_access("anyone@example.com") is True
    
    def test_can_access_authorized_users(self):
        """Test access control for authorized users."""
        permissions = SharePermissions()
        
        shared = SharedConversation(
            share_id="test123",
            session_id="session123",
            owner_user_id="user123",
            share_type=ShareType.COLLABORATIVE,
            permissions=permissions,
            authorized_users=["user1@example.com", "user2@example.com"]
        )
        
        assert shared.can_access("user1@example.com") is True
        assert shared.can_access("user2@example.com") is True
        assert shared.can_access("unauthorized@example.com") is False
    
    def test_record_access(self):
        """Test recording access to a share."""
        permissions = SharePermissions()
        
        shared = SharedConversation(
            share_id="test123",
            session_id="session123",
            owner_user_id="user123",
            share_type=ShareType.VIEW_ONLY,
            permissions=permissions
        )
        
        initial_count = shared.access_count
        initial_accessed = shared.last_accessed
        
        shared.record_access("user@example.com")
        
        assert shared.access_count == initial_count + 1
        assert shared.last_accessed is not None
        assert shared.last_accessed != initial_accessed
    
    def test_serialization(self):
        """Test shared conversation serialization."""
        permissions = SharePermissions(allow_comments=True)
        
        shared = SharedConversation(
            share_id="test123",
            session_id="session123",
            owner_user_id="user123",
            share_type=ShareType.COLLABORATIVE,
            permissions=permissions,
            authorized_users=["user1@example.com"]
        )
        
        data = shared.to_dict()
        reconstructed = SharedConversation.from_dict(data)
        
        assert reconstructed.share_id == shared.share_id
        assert reconstructed.session_id == shared.session_id
        assert reconstructed.share_type == shared.share_type
        assert reconstructed.permissions.allow_comments == shared.permissions.allow_comments
        assert reconstructed.authorized_users == shared.authorized_users


class TestShareComment:
    """Test ShareComment model."""
    
    def test_comment_creation(self):
        """Test creating a share comment."""
        comment = ShareComment(
            comment_id="comment123",
            share_id="share123",
            content="This is a test comment",
            author_email="user@example.com",
            message_id="msg123"
        )
        
        assert comment.comment_id == "comment123"
        assert comment.share_id == "share123"
        assert comment.content == "This is a test comment"
        assert comment.author_email == "user@example.com"
        assert comment.message_id == "msg123"
        assert comment.is_resolved is False
        assert comment.is_deleted is False
    
    def test_comment_serialization(self):
        """Test comment serialization."""
        comment = ShareComment(
            comment_id="comment123",
            share_id="share123",
            content="Test comment",
            author_email="user@example.com"
        )
        
        data = comment.to_dict()
        reconstructed = ShareComment.from_dict(data)
        
        assert reconstructed.comment_id == comment.comment_id
        assert reconstructed.content == comment.content
        assert reconstructed.author_email == comment.author_email


class TestShareAnnotation:
    """Test ShareAnnotation model."""
    
    def test_annotation_creation(self):
        """Test creating a share annotation."""
        annotation = ShareAnnotation(
            annotation_id="annotation123",
            share_id="share123",
            message_id="msg123",
            annotation_type="highlight",
            selected_text="This is highlighted text",
            start_position=10,
            end_position=35,
            author_email="user@example.com"
        )
        
        assert annotation.annotation_id == "annotation123"
        assert annotation.share_id == "share123"
        assert annotation.message_id == "msg123"
        assert annotation.annotation_type == "highlight"
        assert annotation.selected_text == "This is highlighted text"
        assert annotation.start_position == 10
        assert annotation.end_position == 35
        assert annotation.author_email == "user@example.com"
        assert annotation.color == "yellow"  # default
        assert annotation.is_public is True
    
    def test_annotation_serialization(self):
        """Test annotation serialization."""
        annotation = ShareAnnotation(
            annotation_id="annotation123",
            share_id="share123",
            message_id="msg123",
            annotation_type="note",
            selected_text="Selected text",
            start_position=0,
            end_position=13,
            author_email="user@example.com",
            content="This is a note",
            color="blue"
        )
        
        data = annotation.to_dict()
        reconstructed = ShareAnnotation.from_dict(data)
        
        assert reconstructed.annotation_id == annotation.annotation_id
        assert reconstructed.content == annotation.content
        assert reconstructed.color == annotation.color
        assert reconstructed.selected_text == annotation.selected_text


class TestConversationSharingService:
    """Test ConversationSharingService."""
    
    @pytest.fixture
    def mock_chat_service(self):
        """Create a mock chat service."""
        chat_service = Mock(spec=ChatService)
        
        # Mock session
        mock_session = ChatSession(
            session_id="session123",
            user_id="user123",
            title="Test Session"
        )
        chat_service.get_session.return_value = mock_session
        
        return chat_service
    
    @pytest.fixture
    def sharing_service(self, mock_chat_service):
        """Create a sharing service with mock dependencies."""
        return ConversationSharingService(mock_chat_service)
    
    def test_create_share_success(self, sharing_service):
        """Test successful share creation."""
        permissions = SharePermissions(allow_comments=True)
        
        share = sharing_service.create_share(
            session_id="session123",
            owner_user_id="user123",
            share_type=ShareType.COLLABORATIVE,
            permissions=permissions,
            authorized_users=["friend@example.com"]
        )
        
        assert share is not None
        assert share.session_id == "session123"
        assert share.owner_user_id == "user123"
        assert share.share_type == ShareType.COLLABORATIVE
        assert share.permissions.allow_comments is True
        assert "friend@example.com" in share.authorized_users
        assert share.share_id is not None
        assert len(share.share_id) == 12  # Generated hash length
    
    def test_create_share_session_not_found(self, sharing_service, mock_chat_service):
        """Test share creation with non-existent session."""
        mock_chat_service.get_session.return_value = None
        permissions = SharePermissions()
        
        with pytest.raises(ValueError, match="Session .* not found"):
            sharing_service.create_share(
                session_id="nonexistent",
                owner_user_id="user123",
                share_type=ShareType.VIEW_ONLY,
                permissions=permissions
            )
    
    def test_create_share_with_password(self, sharing_service):
        """Test creating a password-protected share."""
        permissions = SharePermissions()
        
        share = sharing_service.create_share(
            session_id="session123",
            owner_user_id="user123",
            share_type=ShareType.VIEW_ONLY,
            permissions=permissions,
            password="secret123"
        )
        
        assert share.is_password_protected is True
        assert share.password_hash is not None
        assert share.password_hash != "secret123"  # Should be hashed
    
    def test_get_share(self, sharing_service):
        """Test getting a share by ID."""
        permissions = SharePermissions()
        
        # Create a share
        created_share = sharing_service.create_share(
            session_id="session123",
            owner_user_id="user123",
            share_type=ShareType.VIEW_ONLY,
            permissions=permissions
        )
        
        # Get the share
        retrieved_share = sharing_service.get_share(created_share.share_id)
        
        assert retrieved_share is not None
        assert retrieved_share.share_id == created_share.share_id
        assert retrieved_share.session_id == created_share.session_id
    
    def test_access_share_success(self, sharing_service):
        """Test successful share access."""
        permissions = SharePermissions()
        
        # Create public share
        share = sharing_service.create_share(
            session_id="session123",
            owner_user_id="user123",
            share_type=ShareType.PUBLIC,
            permissions=permissions
        )
        
        # Access the share
        accessed_share, error = sharing_service.access_share(share.share_id)
        
        assert accessed_share is not None
        assert error == ""
        assert accessed_share.access_count == 1
    
    def test_access_share_with_password(self, sharing_service):
        """Test accessing password-protected share."""
        permissions = SharePermissions()
        password = "secret123"
        
        # Create password-protected share
        share = sharing_service.create_share(
            session_id="session123",
            owner_user_id="user123",
            share_type=ShareType.VIEW_ONLY,
            permissions=permissions,
            password=password
        )
        
        # Access with correct password
        accessed_share, error = sharing_service.access_share(
            share.share_id,
            password=password
        )
        
        assert accessed_share is not None
        assert error == ""
        
        # Access with wrong password
        accessed_share, error = sharing_service.access_share(
            share.share_id,
            password="wrong"
        )
        
        assert accessed_share is None
        assert "Incorrect password" in error
    
    def test_access_share_unauthorized(self, sharing_service):
        """Test accessing share without authorization."""
        permissions = SharePermissions()
        
        # Create share with specific authorized users
        share = sharing_service.create_share(
            session_id="session123",
            owner_user_id="user123",
            share_type=ShareType.COLLABORATIVE,
            permissions=permissions,
            authorized_users=["authorized@example.com"]
        )
        
        # Access as unauthorized user
        accessed_share, error = sharing_service.access_share(
            share.share_id,
            user_email="unauthorized@example.com"
        )
        
        assert accessed_share is None
        assert "Access denied" in error
        
        # Access as authorized user
        accessed_share, error = sharing_service.access_share(
            share.share_id,
            user_email="authorized@example.com"
        )
        
        assert accessed_share is not None
        assert error == ""
    
    def test_revoke_share(self, sharing_service):
        """Test revoking a share."""
        permissions = SharePermissions()
        
        share = sharing_service.create_share(
            session_id="session123",
            owner_user_id="user123",
            share_type=ShareType.VIEW_ONLY,
            permissions=permissions
        )
        
        # Revoke the share
        success = sharing_service.revoke_share(share.share_id, "user123")
        assert success is True
        
        # Verify share is revoked
        retrieved_share = sharing_service.get_share(share.share_id)
        assert retrieved_share.is_revoked is True
        assert retrieved_share.is_accessible() is False
        
        # Try to access revoked share
        accessed_share, error = sharing_service.access_share(share.share_id)
        assert accessed_share is None
        assert "revoked" in error
    
    def test_add_comment(self, sharing_service):
        """Test adding comments to a shared conversation."""
        permissions = SharePermissions(allow_comments=True)
        
        share = sharing_service.create_share(
            session_id="session123",
            owner_user_id="user123",
            share_type=ShareType.COLLABORATIVE,
            permissions=permissions
        )
        
        # Add comment
        comment = sharing_service.add_comment(
            share_id=share.share_id,
            content="This is a test comment",
            author_email="commenter@example.com",
            message_id="msg123"
        )
        
        assert comment is not None
        assert comment.content == "This is a test comment"
        assert comment.author_email == "commenter@example.com"
        assert comment.share_id == share.share_id
        
        # Get comments
        comments = sharing_service.get_comments(share.share_id)
        assert len(comments) == 1
        assert comments[0].comment_id == comment.comment_id
    
    def test_add_comment_not_allowed(self, sharing_service):
        """Test adding comments when not allowed."""
        permissions = SharePermissions(allow_comments=False)
        
        share = sharing_service.create_share(
            session_id="session123",
            owner_user_id="user123",
            share_type=ShareType.VIEW_ONLY,
            permissions=permissions
        )
        
        # Try to add comment
        comment = sharing_service.add_comment(
            share_id=share.share_id,
            content="This should not work",
            author_email="commenter@example.com"
        )
        
        assert comment is None
    
    def test_add_annotation(self, sharing_service):
        """Test adding annotations to a shared conversation."""
        permissions = SharePermissions(allow_annotations=True)
        
        share = sharing_service.create_share(
            session_id="session123",
            owner_user_id="user123",
            share_type=ShareType.COLLABORATIVE,
            permissions=permissions
        )
        
        # Add annotation
        annotation = sharing_service.add_annotation(
            share_id=share.share_id,
            message_id="msg123",
            annotation_type="highlight",
            selected_text="highlighted text",
            start_position=10,
            end_position=26,
            author_email="annotator@example.com",
            color="blue"
        )
        
        assert annotation is not None
        assert annotation.selected_text == "highlighted text"
        assert annotation.color == "blue"
        assert annotation.share_id == share.share_id
        
        # Get annotations
        annotations = sharing_service.get_annotations(share.share_id)
        assert len(annotations) == 1
        assert annotations[0].annotation_id == annotation.annotation_id
    
    def test_get_share_analytics(self, sharing_service):
        """Test getting share analytics."""
        permissions = SharePermissions(allow_comments=True, allow_annotations=True)
        
        share = sharing_service.create_share(
            session_id="session123",
            owner_user_id="user123",
            share_type=ShareType.COLLABORATIVE,
            permissions=permissions
        )
        
        # Add some activity
        sharing_service.access_share(share.share_id)
        sharing_service.access_share(share.share_id)
        sharing_service.add_comment(share.share_id, "Comment", "user@example.com")
        sharing_service.add_annotation(
            share.share_id, "msg123", "highlight", "text", 0, 4, "user@example.com"
        )
        
        # Get analytics
        analytics = sharing_service.get_share_analytics(share.share_id, "user123")
        
        assert analytics["access_count"] == 2
        assert analytics["comments_count"] == 1
        assert analytics["annotations_count"] == 1
        assert analytics["is_active"] is True
    
    def test_cleanup_expired_shares(self, sharing_service):
        """Test cleaning up expired shares."""
        permissions = SharePermissions()
        
        # Create expired share
        expired_share = sharing_service.create_share(
            session_id="session123",
            owner_user_id="user123",
            share_type=ShareType.VIEW_ONLY,
            permissions=permissions,
            expiration=ExpirationPeriod.ONE_HOUR
        )
        
        # Manually set as expired
        expired_share.expires_at = datetime.now() - timedelta(hours=1)
        
        # Create active share
        active_share = sharing_service.create_share(
            session_id="session456",
            owner_user_id="user123",
            share_type=ShareType.VIEW_ONLY,
            permissions=permissions
        )
        
        # Add some comments to expired share
        sharing_service.add_comment(
            expired_share.share_id, "Comment", "user@example.com"
        )
        
        # Cleanup expired shares
        cleaned_count = sharing_service.cleanup_expired_shares()
        
        assert cleaned_count == 1
        assert sharing_service.get_share(expired_share.share_id) is None
        assert sharing_service.get_share(active_share.share_id) is not None
        assert len(sharing_service.get_comments(expired_share.share_id)) == 0
    
    def test_get_share_statistics(self, sharing_service):
        """Test getting overall sharing statistics."""
        permissions = SharePermissions()
        
        # Create shares of different types
        sharing_service.create_share(
            "session1", "user123", ShareType.VIEW_ONLY, permissions
        )
        sharing_service.create_share(
            "session2", "user123", ShareType.PUBLIC, permissions
        )
        sharing_service.create_share(
            "session3", "user123", ShareType.COLLABORATIVE, permissions
        )
        
        stats = sharing_service.get_share_statistics()
        
        assert stats["total_shares"] == 3
        assert stats["active_shares"] == 3
        assert "view_only" in stats["share_types"]
        assert "public" in stats["share_types"] 
        assert "collaborative" in stats["share_types"]