"""
Internationalization Service for Multi-Language Support.

This service provides comprehensive internationalization (i18n) functionality including
language detection, text translation, locale-specific formatting, and cultural
adaptations for the Arete philosophical tutoring system.
"""

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
import json
from pathlib import Path


class SupportedLanguage(Enum):
    """Supported languages with their ISO codes."""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    CHINESE_SIMPLIFIED = "zh-CN"
    CHINESE_TRADITIONAL = "zh-TW"
    JAPANESE = "ja"
    KOREAN = "ko"
    ARABIC = "ar"
    HEBREW = "he"
    HINDI = "hi"
    SANSKRIT = "sa"  # For classical texts
    LATIN = "la"     # For medieval texts
    ANCIENT_GREEK = "grc"  # For ancient texts


class TextDirection(Enum):
    """Text direction options."""
    LEFT_TO_RIGHT = "ltr"
    RIGHT_TO_LEFT = "rtl"


class DateFormat(Enum):
    """Date format options."""
    US = "MM/DD/YYYY"        # US format
    EUROPEAN = "DD/MM/YYYY"  # European format
    ISO = "YYYY-MM-DD"       # ISO format
    RELATIVE = "relative"    # Relative format (2 hours ago)


@dataclass
class LanguageInfo:
    """Information about a supported language."""
    code: str
    name: str
    native_name: str
    text_direction: TextDirection
    date_format: DateFormat
    decimal_separator: str = "."
    thousand_separator: str = ","
    currency_symbol: str = "$"
    philosophical_tradition: Optional[str] = None


@dataclass
class TranslationEntry:
    """A translation entry with context."""
    key: str
    text: str
    context: Optional[str] = None
    plural_form: Optional[str] = None
    description: Optional[str] = None


class InternationalizationService:
    """Service for internationalization and localization."""
    
    def __init__(self, default_language: SupportedLanguage = SupportedLanguage.ENGLISH):
        """Initialize the internationalization service."""
        self.default_language = default_language
        self.current_language = default_language
        self.translations: Dict[str, Dict[str, TranslationEntry]] = {}
        self.language_info: Dict[str, LanguageInfo] = {}
        
        self._initialize_language_info()
        self._load_translations()
    
    def _initialize_language_info(self):
        """Initialize language information."""
        languages = [
            LanguageInfo("en", "English", "English", TextDirection.LEFT_TO_RIGHT, DateFormat.US, 
                        philosophical_tradition="Analytic Philosophy"),
            LanguageInfo("es", "Spanish", "Español", TextDirection.LEFT_TO_RIGHT, DateFormat.EUROPEAN,
                        philosophical_tradition="Iberian Philosophy"),
            LanguageInfo("fr", "French", "Français", TextDirection.LEFT_TO_RIGHT, DateFormat.EUROPEAN,
                        philosophical_tradition="Continental Philosophy"),
            LanguageInfo("de", "German", "Deutsch", TextDirection.LEFT_TO_RIGHT, DateFormat.EUROPEAN,
                        philosophical_tradition="German Idealism"),
            LanguageInfo("it", "Italian", "Italiano", TextDirection.LEFT_TO_RIGHT, DateFormat.EUROPEAN,
                        philosophical_tradition="Renaissance Philosophy"),
            LanguageInfo("pt", "Portuguese", "Português", TextDirection.LEFT_TO_RIGHT, DateFormat.EUROPEAN,
                        philosophical_tradition="Luso-Brazilian Philosophy"),
            LanguageInfo("ru", "Russian", "Русский", TextDirection.LEFT_TO_RIGHT, DateFormat.EUROPEAN,
                        philosophical_tradition="Russian Philosophy"),
            LanguageInfo("zh-CN", "Chinese (Simplified)", "中文(简体)", TextDirection.LEFT_TO_RIGHT, DateFormat.ISO,
                        decimal_separator=".", philosophical_tradition="Chinese Philosophy"),
            LanguageInfo("zh-TW", "Chinese (Traditional)", "中文(繁體)", TextDirection.LEFT_TO_RIGHT, DateFormat.ISO,
                        decimal_separator=".", philosophical_tradition="Chinese Philosophy"),
            LanguageInfo("ja", "Japanese", "日本語", TextDirection.LEFT_TO_RIGHT, DateFormat.ISO,
                        philosophical_tradition="Japanese Philosophy"),
            LanguageInfo("ko", "Korean", "한국어", TextDirection.LEFT_TO_RIGHT, DateFormat.ISO,
                        philosophical_tradition="Korean Philosophy"),
            LanguageInfo("ar", "Arabic", "العربية", TextDirection.RIGHT_TO_LEFT, DateFormat.EUROPEAN,
                        decimal_separator=".", philosophical_tradition="Islamic Philosophy"),
            LanguageInfo("he", "Hebrew", "עברית", TextDirection.RIGHT_TO_LEFT, DateFormat.EUROPEAN,
                        philosophical_tradition="Jewish Philosophy"),
            LanguageInfo("hi", "Hindi", "हिन्दी", TextDirection.LEFT_TO_RIGHT, DateFormat.EUROPEAN,
                        philosophical_tradition="Indian Philosophy"),
            LanguageInfo("sa", "Sanskrit", "संस्कृत", TextDirection.LEFT_TO_RIGHT, DateFormat.EUROPEAN,
                        philosophical_tradition="Vedantic Philosophy"),
            LanguageInfo("la", "Latin", "Latina", TextDirection.LEFT_TO_RIGHT, DateFormat.EUROPEAN,
                        philosophical_tradition="Medieval Philosophy"),
            LanguageInfo("grc", "Ancient Greek", "Ἀρχαία Ἑλληνική", TextDirection.LEFT_TO_RIGHT, DateFormat.EUROPEAN,
                        philosophical_tradition="Ancient Greek Philosophy")
        ]
        
        for lang in languages:
            self.language_info[lang.code] = lang
    
    def _load_translations(self):
        """Load translation files for supported languages."""
        # This would typically load from JSON files
        # For now, we'll initialize with base English translations
        
        base_translations = {
            # Interface elements
            "app_title": "Arete - Philosophical Tutoring Assistant",
            "sidebar_title": "Arete Philosophy Tutor",
            "chat_placeholder": "Ask a philosophical question...",
            "new_session": "New Session",
            "session_management": "Session Management",
            "current_session": "Current Session",
            "recent_sessions": "Recent Sessions",
            
            # Navigation
            "chat_mode": "Chat Only",
            "document_mode": "Document Only", 
            "split_view": "Split View",
            "interface_mode": "Interface Mode",
            
            # Preferences
            "preferences": "Preferences",
            "customize_interface": "Customize Interface",
            "accessibility_settings": "Accessibility Settings",
            "theme": "Theme",
            "font_size": "Font Size",
            "language": "Language",
            "save_preferences": "Save Preferences",
            "reset_to_defaults": "Reset to Defaults",
            
            # Themes
            "light_theme": "Light",
            "dark_theme": "Dark",
            "high_contrast_theme": "High Contrast (WCAG AAA)",
            "sepia_theme": "Sepia (Eye Comfort)",
            
            # Font sizes
            "small_font": "Small (0.9rem)",
            "medium_font": "Medium (1rem)",
            "large_font": "Large (1.25rem)",
            "extra_large_font": "Extra Large (1.5rem)",
            
            # Accessibility
            "keyboard_navigation": "Enhanced keyboard navigation",
            "screen_reader_support": "Screen reader support",
            "reduce_motion": "Reduce motion (Accessibility)",
            "high_contrast_images": "High contrast images",
            "large_click_targets": "Large click targets",
            
            # Actions
            "submit": "Submit",
            "cancel": "Cancel",
            "save": "Save",
            "delete": "Delete",
            "export": "Export",
            "share": "Share",
            "search": "Search",
            "help": "Help",
            "close": "Close",
            
            # Status messages
            "loading": "Loading...",
            "saving": "Saving...",
            "saved_successfully": "Saved successfully!",
            "error_occurred": "An error occurred",
            "preferences_saved": "Preferences saved!",
            "session_created": "New session created",
            "session_deleted": "Session deleted",
            
            # Philosophical contexts
            "academic_level": "Academic Level",
            "undergraduate": "Undergraduate",
            "graduate": "Graduate", 
            "advanced": "Advanced",
            "general": "General",
            
            "philosophical_period": "Philosophical Period",
            "ancient": "Ancient",
            "medieval": "Medieval", 
            "modern": "Modern",
            "contemporary": "Contemporary",
            "all_periods": "All Periods",
            
            # Educational content
            "sources": "Sources",
            "citations": "Citations",
            "response_details": "Response Details",
            "thinking": "Thinking about your philosophical question...",
            
            # Keyboard shortcuts
            "keyboard_shortcuts": "Keyboard Shortcuts",
            "tab_navigate": "Tab: Navigate forward",
            "shift_tab_navigate": "Shift+Tab: Navigate backward",
            "enter_activate": "Enter: Activate buttons and links",
            "space_toggle": "Space: Toggle checkboxes",
            "escape_close": "Escape: Close modals and cancel",
            "ctrl_enter_submit": "Ctrl+Enter: Submit chat message",
            "ctrl_n_new": "Ctrl+N: Create new session",
            "ctrl_slash_help": "Ctrl+/: Show keyboard shortcuts",
            
            # Error messages
            "network_error": "Network connection error",
            "server_error": "Server error occurred",
            "validation_error": "Please check your input",
            "file_not_found": "File not found",
            "permission_denied": "Permission denied",
            
            # Philosophical terms (examples)
            "virtue": "Virtue",
            "justice": "Justice",
            "wisdom": "Wisdom",
            "courage": "Courage",
            "temperance": "Temperance",
            "ethics": "Ethics",
            "metaphysics": "Metaphysics",
            "epistemology": "Epistemology",
            "logic": "Logic",
            "aesthetics": "Aesthetics"
        }
        
        # Initialize English translations
        self.translations["en"] = {}
        for key, text in base_translations.items():
            self.translations["en"][key] = TranslationEntry(
                key=key,
                text=text,
                context="interface"
            )
        
        # Initialize other languages with English as fallback
        for lang_code in self.language_info.keys():
            if lang_code not in self.translations:
                self.translations[lang_code] = {}
    
    def set_language(self, language: SupportedLanguage) -> bool:
        """Set the current language."""
        if language.value in self.language_info:
            self.current_language = language
            return True
        return False
    
    def get_current_language(self) -> SupportedLanguage:
        """Get the current language."""
        return self.current_language
    
    def get_supported_languages(self) -> List[Tuple[str, str, str]]:
        """Get list of supported languages (code, name, native_name)."""
        return [
            (code, info.name, info.native_name)
            for code, info in self.language_info.items()
        ]
    
    def translate(self, key: str, language: Optional[str] = None, 
                  context: Optional[str] = None, **kwargs) -> str:
        """Translate a text key to the specified language."""
        target_language = language or self.current_language.value
        
        # Try to get translation in target language
        if (target_language in self.translations and 
            key in self.translations[target_language]):
            translation = self.translations[target_language][key].text
        # Fallback to default language
        elif (self.default_language.value in self.translations and 
              key in self.translations[self.default_language.value]):
            translation = self.translations[self.default_language.value][key].text
        # Last resort: return the key itself
        else:
            translation = key.replace('_', ' ').title()
        
        # Handle string formatting
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except (KeyError, ValueError):
                # If formatting fails, return unformatted string
                pass
        
        return translation
    
    def translate_plural(self, key: str, count: int, language: Optional[str] = None) -> str:
        """Translate a plural form based on count."""
        target_language = language or self.current_language.value
        
        if (target_language in self.translations and 
            key in self.translations[target_language]):
            entry = self.translations[target_language][key]
            
            # Simple plural logic (would be more complex for languages with complex plural rules)
            if count == 1:
                return entry.text
            elif entry.plural_form:
                return entry.plural_form
            else:
                return entry.text + "s"  # Simple English pluralization
        
        # Fallback
        return self.translate(key, language)
    
    def get_language_info(self, language: Optional[str] = None) -> LanguageInfo:
        """Get language information."""
        target_language = language or self.current_language.value
        return self.language_info.get(target_language, self.language_info["en"])
    
    def is_rtl_language(self, language: Optional[str] = None) -> bool:
        """Check if language uses right-to-left text direction."""
        info = self.get_language_info(language)
        return info.text_direction == TextDirection.RIGHT_TO_LEFT
    
    def format_date(self, date_obj, language: Optional[str] = None, format_type: Optional[DateFormat] = None) -> str:
        """Format date according to language conventions."""
        info = self.get_language_info(language)
        date_format = format_type or info.date_format
        
        # This would use proper date formatting libraries
        # For now, return a simple implementation
        if date_format == DateFormat.US:
            return date_obj.strftime("%m/%d/%Y")
        elif date_format == DateFormat.EUROPEAN:
            return date_obj.strftime("%d/%m/%Y")
        elif date_format == DateFormat.ISO:
            return date_obj.strftime("%Y-%m-%d")
        else:  # RELATIVE
            return "recently"  # Would implement relative date logic
    
    def format_number(self, number: float, language: Optional[str] = None) -> str:
        """Format number according to language conventions."""
        info = self.get_language_info(language)
        
        # Simple number formatting
        formatted = f"{number:,.2f}"
        
        # Replace separators according to language
        if info.decimal_separator != ".":
            formatted = formatted.replace(".", "TEMP_DECIMAL")
            formatted = formatted.replace(",", info.thousand_separator)
            formatted = formatted.replace("TEMP_DECIMAL", info.decimal_separator)
        elif info.thousand_separator != ",":
            formatted = formatted.replace(",", info.thousand_separator)
        
        return formatted
    
    def get_philosophical_context(self, language: Optional[str] = None) -> Optional[str]:
        """Get philosophical tradition context for the language."""
        info = self.get_language_info(language)
        return info.philosophical_tradition
    
    def generate_language_css(self, language: Optional[str] = None) -> str:
        """Generate CSS for language-specific styling."""
        info = self.get_language_info(language)
        
        css = f"""
        <style>
        /* Language-specific styling for {info.name} */
        .main {{
            direction: {info.text_direction.value};
        }}
        
        /* Text direction specific adjustments */
        """
        
        if info.text_direction == TextDirection.RIGHT_TO_LEFT:
            css += """
            .stSidebar {
                right: 0;
                left: auto;
            }
            
            .stChatMessage {
                text-align: right;
            }
            
            .citation {
                border-right: 4px solid #6c757d;
                border-left: none;
                padding-right: 1rem;
                padding-left: 0.5rem;
            }
            """
        
        # Font adjustments for specific scripts
        if info.code in ["ar", "he"]:
            css += """
            body, .stApp {
                font-family: "Noto Sans Arabic", "Arial Unicode MS", sans-serif !important;
            }
            """
        elif info.code in ["zh-CN", "zh-TW"]:
            css += """
            body, .stApp {
                font-family: "Noto Sans CJK SC", "Microsoft YaHei", "SimHei", sans-serif !important;
            }
            """
        elif info.code == "ja":
            css += """
            body, .stApp {
                font-family: "Noto Sans CJK JP", "Hiragino Kaku Gothic Pro", "Meiryo", sans-serif !important;
            }
            """
        elif info.code == "ko":
            css += """
            body, .stApp {
                font-family: "Noto Sans CJK KR", "Malgun Gothic", "Dotum", sans-serif !important;
            }
            """
        elif info.code in ["hi", "sa"]:
            css += """
            body, .stApp {
                font-family: "Noto Sans Devanagari", "Mangal", "Arial Unicode MS", sans-serif !important;
            }
            """
        
        css += "</style>"
        return css
    
    def load_language_pack(self, language_code: str, file_path: Optional[Path] = None) -> bool:
        """Load translations from a language pack file."""
        if file_path is None:
            file_path = Path(f"locales/{language_code}.json")
        
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if language_code not in self.translations:
                    self.translations[language_code] = {}
                
                for key, value in data.items():
                    if isinstance(value, str):
                        self.translations[language_code][key] = TranslationEntry(
                            key=key,
                            text=value,
                            context="loaded"
                        )
                    elif isinstance(value, dict):
                        self.translations[language_code][key] = TranslationEntry(
                            key=key,
                            text=value.get('text', key),
                            context=value.get('context'),
                            plural_form=value.get('plural'),
                            description=value.get('description')
                        )
                
                return True
        except Exception as e:
            print(f"Error loading language pack {language_code}: {e}")
        
        return False
    
    def save_language_pack(self, language_code: str, file_path: Optional[Path] = None) -> bool:
        """Save translations to a language pack file."""
        if file_path is None:
            file_path = Path(f"locales/{language_code}.json")
        
        if language_code not in self.translations:
            return False
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {}
            for key, entry in self.translations[language_code].items():
                if entry.plural_form or entry.context or entry.description:
                    data[key] = {
                        'text': entry.text,
                        'context': entry.context,
                        'plural': entry.plural_form,
                        'description': entry.description
                    }
                else:
                    data[key] = entry.text
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving language pack {language_code}: {e}")
        
        return False
    
    def add_translation(self, language_code: str, key: str, text: str, 
                       context: Optional[str] = None, plural_form: Optional[str] = None,
                       description: Optional[str] = None) -> bool:
        """Add a new translation entry."""
        if language_code not in self.translations:
            self.translations[language_code] = {}
        
        self.translations[language_code][key] = TranslationEntry(
            key=key,
            text=text,
            context=context,
            plural_form=plural_form,
            description=description
        )
        
        return True
    
    def get_missing_translations(self, language_code: str) -> List[str]:
        """Get list of missing translations for a language."""
        if language_code not in self.translations:
            return list(self.translations[self.default_language.value].keys())
        
        default_keys = set(self.translations[self.default_language.value].keys())
        language_keys = set(self.translations[language_code].keys())
        
        return list(default_keys - language_keys)
    
    def get_translation_progress(self, language_code: str) -> float:
        """Get translation completion percentage for a language."""
        if language_code not in self.translations:
            return 0.0
        
        default_count = len(self.translations[self.default_language.value])
        language_count = len(self.translations[language_code])
        
        if default_count == 0:
            return 100.0
        
        return (language_count / default_count) * 100.0