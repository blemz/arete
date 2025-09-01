"""
User preferences service for managing user settings and preferences.

Provides functionality for creating, updating, retrieving, and managing
user preferences in the Arete philosophical tutoring system.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from ..models.user_preferences import (
    UserPreferences,
    Theme,
    CitationStyle,
    DisplaySettings,
    NotificationSettings,
    PrivacySettings,
    StudySettings
)


class UserPreferencesService:
    """Service for managing user preferences and settings."""
    
    def __init__(self):
        """Initialize the preferences service."""
        # In-memory storage for preferences (to be replaced with persistent storage)
        self._preferences: Dict[str, UserPreferences] = {}
        self._preferences_history: Dict[str, List[Dict[str, Any]]] = {}  # For preference change history
    
    def create_user_preferences(self, user_id: str, **kwargs) -> UserPreferences:
        """Create default user preferences for a new user."""
        preferences = UserPreferences(
            user_id=user_id,
            **kwargs
        )
        
        self._preferences[user_id] = preferences
        self._record_preference_change(user_id, "created", "User preferences created")
        
        return preferences
    
    def get_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """Get user preferences, creating defaults if they don't exist."""
        if user_id in self._preferences:
            # Record access
            preferences = self._preferences[user_id]
            return preferences
        else:
            # Create default preferences for new user
            return self.create_user_preferences(user_id)
    
    def update_user_preferences(self, user_id: str, preferences: UserPreferences) -> bool:
        """Update complete user preferences."""
        if user_id != preferences.user_id:
            return False
        
        # Update timestamp
        preferences.update_timestamp()
        
        # Store updated preferences
        old_preferences = self._preferences.get(user_id)
        self._preferences[user_id] = preferences
        
        # Record change
        changes = self._detect_preference_changes(old_preferences, preferences)
        self._record_preference_change(user_id, "updated", f"Updated preferences: {', '.join(changes)}")
        
        return True
    
    def update_user_preferences_partial(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update specific user preference fields."""
        current_preferences = self.get_user_preferences(user_id)
        if not current_preferences:
            return False
        
        # Apply updates
        updated_preferences = self._apply_partial_updates(current_preferences, updates)
        
        return self.update_user_preferences(user_id, updated_preferences)
    
    def delete_user_preferences(self, user_id: str) -> bool:
        """Delete user preferences."""
        if user_id not in self._preferences:
            return False
        
        del self._preferences[user_id]
        self._record_preference_change(user_id, "deleted", "User preferences deleted")
        
        return True
    
    def export_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Export user preferences as dictionary."""
        preferences = self.get_user_preferences(user_id)
        if not preferences:
            return None
        
        return preferences.to_dict()
    
    def import_user_preferences(self, preferences_data: Dict[str, Any]) -> bool:
        """Import user preferences from dictionary."""
        try:
            user_id = preferences_data.get("user_id")
            if not user_id:
                return False
            
            preferences = UserPreferences.from_dict(preferences_data)
            return self.update_user_preferences(user_id, preferences)
        except Exception:
            return False
    
    def get_preferences_summary(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of user preferences."""
        preferences = self.get_user_preferences(user_id)
        if not preferences:
            return None
        
        return {
            "user_id": user_id,
            "theme": preferences.theme.value,
            "citation_style": preferences.citation_style.value,
            "language": preferences.language,
            "auto_save": preferences.auto_save,
            "display_preferences": {
                "font_size": preferences.display_settings.font_size,
                "compact_mode": preferences.display_settings.compact_mode,
                "show_timestamps": preferences.display_settings.show_timestamps
            },
            "notification_preferences": {
                "email_notifications": preferences.notification_settings.email_notifications,
                "push_notifications": preferences.notification_settings.push_notifications
            },
            "privacy_preferences": {
                "data_sharing": preferences.privacy_settings.data_sharing,
                "export_data_allowed": preferences.privacy_settings.export_data_allowed
            },
            "last_updated": preferences.updated_at.isoformat()
        }
    
    def get_chat_interface_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get preferences formatted for chat interface."""
        preferences = self.get_user_preferences(user_id)
        if not preferences:
            # Return default chat interface preferences
            return self._get_default_chat_preferences()
        
        return preferences.get_chat_interface_config()
    
    def get_notification_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get notification preferences for the user."""
        preferences = self.get_user_preferences(user_id)
        if not preferences:
            return self._get_default_notification_preferences()
        
        return preferences.get_notification_config()
    
    def can_user_export_data(self, user_id: str) -> bool:
        """Check if user allows data export."""
        preferences = self.get_user_preferences(user_id)
        if not preferences:
            return True  # Default to allowing export
        
        return preferences.privacy_settings.export_data_allowed
    
    def get_session_retention_period(self, user_id: str) -> int:
        """Get session history retention period for user."""
        preferences = self.get_user_preferences(user_id)
        if not preferences:
            return 365  # Default to 1 year
        
        return preferences.privacy_settings.session_history_retention
    
    def migrate_user_preferences(self, old_preferences_data: Dict[str, Any]) -> UserPreferences:
        """Migrate old preference format to new format."""
        user_id = old_preferences_data.get("user_id")
        if not user_id:
            raise ValueError("User ID is required for migration")
        
        # Start with default preferences
        preferences = UserPreferences(user_id=user_id)
        
        # Migrate known fields
        if "theme" in old_preferences_data:
            try:
                preferences.theme = Theme(old_preferences_data["theme"])
            except ValueError:
                pass  # Keep default if invalid
        
        # Migrate display settings
        display_updates = {}
        if "show_timestamps" in old_preferences_data:
            display_updates["show_timestamps"] = old_preferences_data["show_timestamps"]
        if "font_size" in old_preferences_data:
            display_updates["font_size"] = old_preferences_data["font_size"]
        if "compact_mode" in old_preferences_data:
            display_updates["compact_mode"] = old_preferences_data["compact_mode"]
        
        if display_updates:
            current_display = preferences.display_settings.to_dict()
            current_display.update(display_updates)
            preferences.display_settings = DisplaySettings.from_dict(current_display)
        
        # Migrate other fields as needed
        if "language" in old_preferences_data:
            preferences.language = old_preferences_data["language"]
        if "auto_save" in old_preferences_data:
            preferences.auto_save = old_preferences_data["auto_save"]
        
        # Update version to indicate migration
        preferences.version = 2
        preferences.update_timestamp()
        
        # Store migrated preferences
        self._preferences[user_id] = preferences
        self._record_preference_change(user_id, "migrated", "Preferences migrated to new format")
        
        return preferences
    
    def validate_preferences_data(self, preferences_data: Dict[str, Any]) -> bool:
        """Validate preferences data structure."""
        try:
            # Try to create UserPreferences from data
            UserPreferences.from_dict(preferences_data)
            return True
        except Exception:
            return False
    
    def get_preference_change_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get history of preference changes for a user."""
        return self._preferences_history.get(user_id, [])
    
    def reset_user_preferences_to_defaults(self, user_id: str) -> bool:
        """Reset user preferences to default values."""
        try:
            default_preferences = UserPreferences(user_id=user_id)
            self._preferences[user_id] = default_preferences
            self._record_preference_change(user_id, "reset", "Preferences reset to defaults")
            return True
        except Exception:
            return False
    
    def bulk_update_preferences(self, user_preferences_list: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Bulk update multiple user preferences."""
        results = {}
        
        for prefs_data in user_preferences_list:
            user_id = prefs_data.get("user_id")
            if user_id:
                results[user_id] = self.import_user_preferences(prefs_data)
            else:
                results["invalid_data"] = False
        
        return results
    
    # Private helper methods
    
    def _apply_partial_updates(self, preferences: UserPreferences, updates: Dict[str, Any]) -> UserPreferences:
        """Apply partial updates to user preferences."""
        prefs_dict = preferences.to_dict()
        
        # Handle nested updates
        for key, value in updates.items():
            if key == "display_settings" and isinstance(value, dict):
                prefs_dict["display_settings"].update(value)
            elif key == "notification_settings" and isinstance(value, dict):
                prefs_dict["notification_settings"].update(value)
            elif key == "privacy_settings" and isinstance(value, dict):
                prefs_dict["privacy_settings"].update(value)
            elif key == "study_settings" and isinstance(value, dict):
                prefs_dict["study_settings"].update(value)
            else:
                prefs_dict[key] = value
        
        return UserPreferences.from_dict(prefs_dict)
    
    def _detect_preference_changes(self, old_prefs: Optional[UserPreferences], new_prefs: UserPreferences) -> List[str]:
        """Detect what preferences have changed."""
        if not old_prefs:
            return ["all (new preferences)"]
        
        changes = []
        
        if old_prefs.theme != new_prefs.theme:
            changes.append("theme")
        if old_prefs.citation_style != new_prefs.citation_style:
            changes.append("citation_style")
        if old_prefs.language != new_prefs.language:
            changes.append("language")
        if old_prefs.auto_save != new_prefs.auto_save:
            changes.append("auto_save")
        
        # Check nested settings (simplified)
        if old_prefs.display_settings.to_dict() != new_prefs.display_settings.to_dict():
            changes.append("display_settings")
        if old_prefs.notification_settings.to_dict() != new_prefs.notification_settings.to_dict():
            changes.append("notification_settings")
        if old_prefs.privacy_settings.to_dict() != new_prefs.privacy_settings.to_dict():
            changes.append("privacy_settings")
        
        return changes if changes else ["minor updates"]
    
    def _record_preference_change(self, user_id: str, action: str, description: str) -> None:
        """Record a preference change for audit purposes."""
        if user_id not in self._preferences_history:
            self._preferences_history[user_id] = []
        
        change_record = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "description": description
        }
        
        self._preferences_history[user_id].append(change_record)
        
        # Keep only last 50 changes per user
        if len(self._preferences_history[user_id]) > 50:
            self._preferences_history[user_id] = self._preferences_history[user_id][-50:]
    
    def _get_default_chat_preferences(self) -> Dict[str, Any]:
        """Get default chat interface preferences."""
        default_prefs = UserPreferences(user_id="default")
        return default_prefs.get_chat_interface_config()
    
    def _get_default_notification_preferences(self) -> Dict[str, Any]:
        """Get default notification preferences."""
        default_prefs = UserPreferences(user_id="default")
        return default_prefs.get_notification_config()