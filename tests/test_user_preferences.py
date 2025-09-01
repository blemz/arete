"""
Tests for user preferences and settings management.

Tests cover user preference creation, validation, storage, retrieval,
and integration with the chat interface following contract-based testing.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from typing import List, Dict, Any, Optional
import json

from arete.services.user_preferences_service import UserPreferencesService, UserPreferences
from arete.models.user_preferences import (
    Theme,
    CitationStyle,
    DisplaySettings,
    NotificationSettings,
    PrivacySettings
)


class TestUserPreferences:
    """Test UserPreferences model and validation."""
    
    def test_user_preferences_creation_with_defaults(self):
        """Test creating user preferences with default values."""
        prefs = UserPreferences(user_id="test_user")
        
        assert prefs.user_id == "test_user"
        assert prefs.theme == Theme.LIGHT
        assert prefs.citation_style == CitationStyle.CHICAGO
        assert prefs.display_settings is not None
        assert prefs.notification_settings is not None
        assert prefs.privacy_settings is not None
    
    def test_user_preferences_creation_with_custom_values(self):
        """Test creating user preferences with custom values."""
        display_settings = DisplaySettings(
            show_timestamps=False,
            message_grouping="by_author",
            font_size="large",
            compact_mode=True
        )
        
        prefs = UserPreferences(
            user_id="custom_user",
            theme=Theme.DARK,
            citation_style=CitationStyle.APA,
            language="es",
            display_settings=display_settings
        )
        
        assert prefs.user_id == "custom_user"
        assert prefs.theme == Theme.DARK
        assert prefs.citation_style == CitationStyle.APA
        assert prefs.language == "es"
        assert prefs.display_settings.compact_mode is True
        assert prefs.display_settings.font_size == "large"
    
    def test_user_preferences_serialization(self):
        """Test user preferences to_dict serialization."""
        prefs = UserPreferences(
            user_id="serialize_user",
            theme=Theme.DARK,
            citation_style=CitationStyle.MLA
        )
        
        prefs_dict = prefs.to_dict()
        
        assert prefs_dict["user_id"] == "serialize_user"
        assert prefs_dict["theme"] == "dark"
        assert prefs_dict["citation_style"] == "mla"
        assert "display_settings" in prefs_dict
        assert "notification_settings" in prefs_dict
        assert "created_at" in prefs_dict
    
    def test_user_preferences_from_dict(self):
        """Test user preferences from_dict deserialization."""
        prefs_data = {
            "user_id": "deserialize_user",
            "theme": "dark",
            "citation_style": "apa",
            "language": "fr",
            "auto_save": False,
            "display_settings": {
                "show_timestamps": False,
                "message_grouping": "by_type",
                "font_size": "small",
                "compact_mode": True
            },
            "created_at": "2025-08-26T10:00:00"
        }
        
        prefs = UserPreferences.from_dict(prefs_data)
        
        assert prefs.user_id == "deserialize_user"
        assert prefs.theme == Theme.DARK
        assert prefs.citation_style == CitationStyle.APA
        assert prefs.language == "fr"
        assert prefs.auto_save is False
        assert prefs.display_settings.compact_mode is True


class TestDisplaySettings:
    """Test DisplaySettings model."""
    
    def test_display_settings_defaults(self):
        """Test display settings default values."""
        settings = DisplaySettings()
        
        assert settings.show_timestamps is True
        assert settings.message_grouping == "chronological"
        assert settings.font_size == "medium"
        assert settings.compact_mode is False
        assert settings.show_citations is True
        assert settings.citations_expanded is False
    
    def test_display_settings_validation(self):
        """Test display settings validation."""
        # Valid font sizes
        valid_settings = DisplaySettings(font_size="small")
        assert valid_settings.font_size == "small"
        
        valid_settings = DisplaySettings(font_size="large")
        assert valid_settings.font_size == "large"
        
        # Valid message grouping options
        valid_settings = DisplaySettings(message_grouping="by_type")
        assert valid_settings.message_grouping == "by_type"
        
        valid_settings = DisplaySettings(message_grouping="by_author")
        assert valid_settings.message_grouping == "by_author"
    
    def test_display_settings_invalid_values(self):
        """Test display settings with invalid values."""
        # Invalid font size should raise validation error
        with pytest.raises(ValueError):
            DisplaySettings(font_size="invalid_size")
        
        # Invalid message grouping should raise validation error
        with pytest.raises(ValueError):
            DisplaySettings(message_grouping="invalid_grouping")


class TestNotificationSettings:
    """Test NotificationSettings model."""
    
    def test_notification_settings_defaults(self):
        """Test notification settings default values."""
        settings = NotificationSettings()
        
        assert settings.email_notifications is True
        assert settings.push_notifications is True
        assert settings.session_reminders is True
        assert settings.new_features is True
        assert settings.philosophical_quotes is False
    
    def test_notification_settings_customization(self):
        """Test customizing notification settings."""
        settings = NotificationSettings(
            email_notifications=False,
            push_notifications=False,
            session_reminders=False,
            philosophical_quotes=True
        )
        
        assert settings.email_notifications is False
        assert settings.push_notifications is False
        assert settings.session_reminders is False
        assert settings.philosophical_quotes is True


class TestPrivacySettings:
    """Test PrivacySettings model."""
    
    def test_privacy_settings_defaults(self):
        """Test privacy settings default values."""
        settings = PrivacySettings()
        
        assert settings.data_sharing is True
        assert settings.analytics is True
        assert settings.personalized_content is True
        assert settings.session_history_retention == 365
        assert settings.export_data_allowed is True
    
    def test_privacy_settings_customization(self):
        """Test customizing privacy settings."""
        settings = PrivacySettings(
            data_sharing=False,
            analytics=False,
            session_history_retention=30,
            export_data_allowed=False
        )
        
        assert settings.data_sharing is False
        assert settings.analytics is False
        assert settings.session_history_retention == 30
        assert settings.export_data_allowed is False


class TestUserPreferencesService:
    """Test UserPreferencesService for managing user preferences."""
    
    @pytest.fixture
    def preferences_service(self):
        """Create preferences service for testing."""
        return UserPreferencesService()
    
    def test_create_user_preferences(self, preferences_service):
        """Test creating user preferences."""
        user_id = "new_user"
        
        prefs = preferences_service.create_user_preferences(user_id)
        
        assert prefs.user_id == user_id
        assert prefs.theme == Theme.LIGHT  # Default theme
        assert prefs.citation_style == CitationStyle.CHICAGO  # Default citation
        assert isinstance(prefs.display_settings, DisplaySettings)
        assert isinstance(prefs.notification_settings, NotificationSettings)
    
    def test_get_user_preferences_existing(self, preferences_service):
        """Test retrieving existing user preferences."""
        user_id = "existing_user"
        
        # Create preferences first
        created_prefs = preferences_service.create_user_preferences(user_id)
        
        # Retrieve preferences
        retrieved_prefs = preferences_service.get_user_preferences(user_id)
        
        assert retrieved_prefs is not None
        assert retrieved_prefs.user_id == user_id
        assert retrieved_prefs.user_id == created_prefs.user_id
    
    def test_get_user_preferences_nonexistent(self, preferences_service):
        """Test retrieving non-existent user preferences returns defaults."""
        user_id = "nonexistent_user"
        
        prefs = preferences_service.get_user_preferences(user_id)
        
        # Should return default preferences for new user
        assert prefs is not None
        assert prefs.user_id == user_id
        assert prefs.theme == Theme.LIGHT  # Default values
    
    def test_update_user_preferences_full(self, preferences_service):
        """Test updating complete user preferences."""
        user_id = "update_user"
        
        # Create initial preferences
        preferences_service.create_user_preferences(user_id)
        
        # Create updated preferences
        new_display_settings = DisplaySettings(
            show_timestamps=False,
            font_size="large",
            compact_mode=True
        )
        
        updated_prefs = UserPreferences(
            user_id=user_id,
            theme=Theme.DARK,
            citation_style=CitationStyle.APA,
            language="es",
            display_settings=new_display_settings
        )
        
        result = preferences_service.update_user_preferences(user_id, updated_prefs)
        
        assert result is True
        
        # Verify changes were saved
        saved_prefs = preferences_service.get_user_preferences(user_id)
        assert saved_prefs.theme == Theme.DARK
        assert saved_prefs.citation_style == CitationStyle.APA
        assert saved_prefs.language == "es"
        assert saved_prefs.display_settings.compact_mode is True
    
    def test_update_user_preferences_partial(self, preferences_service):
        """Test partial update of user preferences."""
        user_id = "partial_update_user"
        
        # Create initial preferences
        preferences_service.create_user_preferences(user_id)
        
        # Update only specific fields
        updates = {
            "theme": Theme.DARK,
            "auto_save": False,
            "display_settings": {
                "font_size": "large"
            }
        }
        
        result = preferences_service.update_user_preferences_partial(user_id, updates)
        
        assert result is True
        
        # Verify partial changes
        updated_prefs = preferences_service.get_user_preferences(user_id)
        assert updated_prefs.theme == Theme.DARK
        assert updated_prefs.auto_save is False
        assert updated_prefs.display_settings.font_size == "large"
        # Other settings should remain unchanged
        assert updated_prefs.citation_style == CitationStyle.CHICAGO  # Default unchanged
    
    def test_preferences_validation_invalid_theme(self, preferences_service):
        """Test preferences validation with invalid theme."""
        user_id = "invalid_theme_user"
        
        with pytest.raises(ValueError):
            invalid_prefs = UserPreferences(
                user_id=user_id,
                theme="invalid_theme"  # This should raise a validation error
            )
    
    def test_preferences_validation_invalid_citation_style(self, preferences_service):
        """Test preferences validation with invalid citation style."""
        user_id = "invalid_citation_user"
        
        with pytest.raises(ValueError):
            invalid_prefs = UserPreferences(
                user_id=user_id,
                citation_style="invalid_style"  # This should raise a validation error
            )
    
    def test_delete_user_preferences(self, preferences_service):
        """Test deleting user preferences."""
        user_id = "delete_user"
        
        # Create preferences
        preferences_service.create_user_preferences(user_id)
        
        # Verify they exist
        assert preferences_service.get_user_preferences(user_id) is not None
        
        # Delete preferences
        result = preferences_service.delete_user_preferences(user_id)
        
        assert result is True
        
        # Verify deletion - should return defaults for new user
        prefs_after_delete = preferences_service.get_user_preferences(user_id)
        assert prefs_after_delete.created_at != preferences_service.get_user_preferences(user_id).created_at
    
    def test_export_user_preferences(self, preferences_service):
        """Test exporting user preferences."""
        user_id = "export_user"
        
        # Create and customize preferences
        prefs = preferences_service.create_user_preferences(user_id)
        prefs.theme = Theme.DARK
        prefs.citation_style = CitationStyle.MLA
        preferences_service.update_user_preferences(user_id, prefs)
        
        # Export preferences
        exported_data = preferences_service.export_user_preferences(user_id)
        
        assert exported_data is not None
        assert exported_data["user_id"] == user_id
        assert exported_data["theme"] == "dark"
        assert exported_data["citation_style"] == "mla"
        assert "display_settings" in exported_data
        assert "notification_settings" in exported_data
    
    def test_import_user_preferences(self, preferences_service):
        """Test importing user preferences."""
        user_id = "import_user"
        
        # Prepare import data
        import_data = {
            "user_id": user_id,
            "theme": "dark",
            "citation_style": "apa",
            "language": "fr",
            "auto_save": False,
            "display_settings": {
                "font_size": "large",
                "compact_mode": True
            }
        }
        
        # Import preferences
        result = preferences_service.import_user_preferences(import_data)
        
        assert result is True
        
        # Verify imported preferences
        imported_prefs = preferences_service.get_user_preferences(user_id)
        assert imported_prefs.theme == Theme.DARK
        assert imported_prefs.citation_style == CitationStyle.APA
        assert imported_prefs.language == "fr"
        assert imported_prefs.display_settings.font_size == "large"
    
    def test_get_preferences_summary(self, preferences_service):
        """Test getting a summary of user preferences."""
        user_id = "summary_user"
        
        # Create customized preferences
        prefs = preferences_service.create_user_preferences(user_id)
        prefs.theme = Theme.DARK
        prefs.citation_style = CitationStyle.APA
        prefs.language = "es"
        preferences_service.update_user_preferences(user_id, prefs)
        
        # Get summary
        summary = preferences_service.get_preferences_summary(user_id)
        
        assert summary is not None
        assert summary["theme"] == "dark"
        assert summary["citation_style"] == "apa"
        assert summary["language"] == "es"
        assert "display_preferences" in summary
        assert "notification_preferences" in summary


class TestPreferencesIntegration:
    """Test integration of preferences with other services."""
    
    @pytest.fixture
    def preferences_service(self):
        """Create preferences service for testing."""
        return UserPreferencesService()
    
    def test_preferences_chat_interface_integration(self, preferences_service):
        """Test preferences integration with chat interface."""
        user_id = "chat_integration_user"
        
        # Create preferences with specific display settings
        prefs = preferences_service.create_user_preferences(user_id)
        prefs.theme = Theme.DARK
        prefs.display_settings.show_timestamps = False
        prefs.display_settings.compact_mode = True
        prefs.citation_style = CitationStyle.APA
        preferences_service.update_user_preferences(user_id, prefs)
        
        # Get preferences for chat interface
        chat_prefs = preferences_service.get_chat_interface_preferences(user_id)
        
        assert chat_prefs["theme"] == "dark"
        assert chat_prefs["show_timestamps"] is False
        assert chat_prefs["compact_mode"] is True
        assert chat_prefs["citation_style"] == "apa"
    
    def test_preferences_export_integration(self, preferences_service):
        """Test preferences integration with export functionality."""
        user_id = "export_integration_user"
        
        # Create preferences with privacy settings
        prefs = preferences_service.create_user_preferences(user_id)
        prefs.privacy_settings.export_data_allowed = False
        preferences_service.update_user_preferences(user_id, prefs)
        
        # Check export permissions
        can_export = preferences_service.can_user_export_data(user_id)
        
        assert can_export is False
        
        # Change preference and test again
        prefs.privacy_settings.export_data_allowed = True
        preferences_service.update_user_preferences(user_id, prefs)
        
        can_export = preferences_service.can_user_export_data(user_id)
        assert can_export is True
    
    def test_preferences_notification_integration(self, preferences_service):
        """Test preferences integration with notification system."""
        user_id = "notification_integration_user"
        
        # Create preferences with notification settings
        prefs = preferences_service.create_user_preferences(user_id)
        prefs.notification_settings.email_notifications = False
        prefs.notification_settings.push_notifications = True
        prefs.notification_settings.philosophical_quotes = True
        preferences_service.update_user_preferences(user_id, prefs)
        
        # Get notification preferences
        notification_prefs = preferences_service.get_notification_preferences(user_id)
        
        assert notification_prefs["email_notifications"] is False
        assert notification_prefs["push_notifications"] is True
        assert notification_prefs["philosophical_quotes"] is True
    
    def test_preferences_migration_compatibility(self, preferences_service):
        """Test backward compatibility and preference migration."""
        user_id = "migration_user"
        
        # Simulate old preference format
        old_prefs_data = {
            "user_id": user_id,
            "theme": "light",
            "show_timestamps": True,
            "font_size": "medium"
            # Missing new fields like citation_style, notification_settings, etc.
        }
        
        # Test migration
        migrated_prefs = preferences_service.migrate_user_preferences(old_prefs_data)
        
        assert migrated_prefs.user_id == user_id
        assert migrated_prefs.theme == Theme.LIGHT
        assert migrated_prefs.display_settings.show_timestamps is True
        assert migrated_prefs.display_settings.font_size == "medium"
        # New fields should have defaults
        assert migrated_prefs.citation_style == CitationStyle.CHICAGO
        assert isinstance(migrated_prefs.notification_settings, NotificationSettings)