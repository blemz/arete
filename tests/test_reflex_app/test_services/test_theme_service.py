"""
Tests for classical theme configuration service.

TDD RED Phase: These tests MUST fail initially to confirm proper TDD workflow.
Tests validate classical color palette, typography, and accessibility requirements
from planning/aesthetics_plan.md.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import json
import re


# Classical color palette constants from planning/aesthetics_plan.md
CLASSICAL_COLORS = {
    "primary": {
        "deep_navy": "#2C3E50",
        "deep_navy_focus": "#1a252f",
        "deep_navy_content": "#FAF8F5"
    },
    "secondary": {
        "warm_gold": "#D4A574",
        "golden_accent": "#C9A961",
        "golden_accent_focus": "#B89751",
        "warm_gold_content": "#3D3028"
    },
    "background": {
        "warm_white": "#FAF8F5",
        "light_beige": "#F5F0E8",
        "cream_parchment": "#E8DCC8"
    },
    "text": {
        "dark_brown": "#3D3028",
        "medium_gray": "#6B625A",
        "soft_gray": "#9B8B7E"
    },
    "status": {
        "sage_green": "#7B9E87",
        "warning_gold": "#C9A961",
        "error_terracotta": "#A85B52"
    }
}

# Classical typography requirements from planning/aesthetics_plan.md
CLASSICAL_FONTS = {
    "headings": "Cinzel",
    "body": "EB Garamond",
    "greek": "GFS Didot",
    "ui": "Inter"
}

# WCAG AA contrast requirements
MIN_CONTRAST_RATIO = 4.5


class TestThemeService:
    """Test classical theme configuration validation service."""

    @pytest.fixture
    def theme_service(self):
        """ThemeService instance for testing."""
        # Import will fail in RED phase - this is expected
        from src.arete.ui.reflex_app.services.theme_service import ThemeService
        return ThemeService()

    @pytest.fixture
    def tailwind_config_path(self):
        """Path to tailwind.config.js."""
        return Path("C:/Users/blemo/Coding/arete/src/arete/ui/reflex_app/tailwind.config.js")

    @pytest.fixture
    def global_css_path(self):
        """Path to global.css."""
        return Path("C:/Users/blemo/Coding/arete/src/arete/ui/reflex_app/assets/styles/global.css")

    # ========================================================================
    # Color Configuration Tests
    # ========================================================================

    def test_classical_colors_defined_in_tailwind_config(self, theme_service, tailwind_config_path):
        """Test that all classical colors are defined in tailwind.config.js."""
        colors = theme_service.get_tailwind_colors(tailwind_config_path)

        # Verify all primary colors exist
        assert "arete" in colors, "Arete color namespace missing"
        assert colors["arete"]["primary"] == CLASSICAL_COLORS["primary"]["deep_navy"]
        assert colors["arete"]["secondary"] == CLASSICAL_COLORS["secondary"]["warm_gold"]
        assert colors["arete"]["accent"] == CLASSICAL_COLORS["secondary"]["golden_accent"]

    def test_primary_color_is_deep_navy(self, theme_service, tailwind_config_path):
        """Test primary color is Deep Navy Blue #2C3E50."""
        colors = theme_service.get_tailwind_colors(tailwind_config_path)
        assert colors["arete"]["primary"] == "#2C3E50"

    def test_secondary_color_is_warm_gold(self, theme_service, tailwind_config_path):
        """Test secondary color is Warm Gold #D4A574."""
        colors = theme_service.get_tailwind_colors(tailwind_config_path)
        assert colors["arete"]["secondary"] == "#D4A574"

    def test_accent_color_is_golden_accent(self, theme_service, tailwind_config_path):
        """Test accent color is Golden Accent #C9A961."""
        colors = theme_service.get_tailwind_colors(tailwind_config_path)
        assert colors["arete"]["accent"] == "#C9A961"

    def test_background_colors_defined(self, theme_service, tailwind_config_path):
        """Test all three background colors are defined correctly."""
        colors = theme_service.get_tailwind_colors(tailwind_config_path)

        # base-100 should be warmest white
        assert colors["arete"]["base-100"] == CLASSICAL_COLORS["background"]["warm_white"]
        # base-200 should be light beige
        assert colors["arete"]["base-200"] == CLASSICAL_COLORS["background"]["light_beige"]
        # base-300 should be cream parchment
        assert colors["arete"]["base-300"] == CLASSICAL_COLORS["background"]["cream_parchment"]

    def test_text_colors_defined(self, theme_service, tailwind_config_path):
        """Test text colors are defined with proper hierarchy."""
        colors = theme_service.get_tailwind_colors(tailwind_config_path)

        # Primary text should be dark brown
        assert colors["arete"]["base-content"] == CLASSICAL_COLORS["text"]["dark_brown"]
        # Neutral should be medium gray
        assert colors["arete"]["neutral"] == CLASSICAL_COLORS["text"]["medium_gray"]

    def test_status_colors_defined(self, theme_service, tailwind_config_path):
        """Test status colors (success, warning, error) are defined."""
        colors = theme_service.get_tailwind_colors(tailwind_config_path)

        assert colors["arete"]["success"] == CLASSICAL_COLORS["status"]["sage_green"]
        assert colors["arete"]["warning"] == CLASSICAL_COLORS["status"]["warning_gold"]
        assert colors["arete"]["error"] == CLASSICAL_COLORS["status"]["error_terracotta"]

    def test_focus_state_colors_defined(self, theme_service, tailwind_config_path):
        """Test focus states for primary, secondary, and accent colors."""
        colors = theme_service.get_tailwind_colors(tailwind_config_path)

        # Focus states should be darker variants
        assert "primary-focus" in colors["arete"]
        assert "secondary-focus" in colors["arete"]
        assert "accent-focus" in colors["arete"]

        # Verify specific focus colors
        assert colors["arete"]["primary-focus"] == CLASSICAL_COLORS["primary"]["deep_navy_focus"]
        assert colors["arete"]["secondary-focus"] == CLASSICAL_COLORS["secondary"]["golden_accent"]
        assert colors["arete"]["accent-focus"] == CLASSICAL_COLORS["secondary"]["golden_accent_focus"]

    # ========================================================================
    # DaisyUI Theme Configuration Tests
    # ========================================================================

    def test_daisyui_theme_configured(self, theme_service, tailwind_config_path):
        """Test DaisyUI theme section is properly configured."""
        config = theme_service.get_tailwind_config(tailwind_config_path)

        assert "daisyui" in config, "DaisyUI configuration missing"
        assert "themes" in config["daisyui"], "DaisyUI themes array missing"

    def test_classical_theme_exists_in_daisyui(self, theme_service, tailwind_config_path):
        """Test 'classical' theme is defined in DaisyUI themes array."""
        config = theme_service.get_tailwind_config(tailwind_config_path)
        themes = config["daisyui"]["themes"]

        # Find classical theme object in themes array
        classical_theme = None
        for theme in themes:
            if isinstance(theme, dict) and "classical" in theme:
                classical_theme = theme["classical"]
                break

        assert classical_theme is not None, "Classical theme not found in DaisyUI themes"

    def test_classical_theme_is_default(self, theme_service, tailwind_config_path):
        """Test classical theme is the first/default theme."""
        config = theme_service.get_tailwind_config(tailwind_config_path)
        themes = config["daisyui"]["themes"]

        # First theme should be classical
        assert isinstance(themes[0], dict), "First theme should be classical object"
        assert "classical" in themes[0], "Classical theme should be first (default)"

    def test_semantic_color_mappings_in_daisyui(self, theme_service, tailwind_config_path):
        """Test DaisyUI semantic color mappings match classical palette."""
        config = theme_service.get_tailwind_config(tailwind_config_path)
        themes = config["daisyui"]["themes"]

        # Extract classical theme
        classical_theme = None
        for theme in themes:
            if isinstance(theme, dict) and "classical" in theme:
                classical_theme = theme["classical"]
                break

        # Verify semantic mappings
        assert classical_theme["primary"] == CLASSICAL_COLORS["primary"]["deep_navy"]
        assert classical_theme["secondary"] == CLASSICAL_COLORS["secondary"]["warm_gold"]
        assert classical_theme["accent"] == CLASSICAL_COLORS["secondary"]["golden_accent"]
        assert classical_theme["neutral"] == CLASSICAL_COLORS["text"]["medium_gray"]
        assert classical_theme["base-100"] == CLASSICAL_COLORS["background"]["warm_white"]

    # ========================================================================
    # Typography Tests
    # ========================================================================

    def test_classical_fonts_configured(self, theme_service, tailwind_config_path):
        """Test classical font families are configured in Tailwind."""
        config = theme_service.get_tailwind_config(tailwind_config_path)

        assert "theme" in config
        assert "extend" in config["theme"]
        assert "fontFamily" in config["theme"]["extend"]

    def test_cinzel_for_headings(self, theme_service, tailwind_config_path):
        """Test Cinzel font is configured for headings."""
        fonts = theme_service.get_font_families(tailwind_config_path)

        # Should have a heading or serif category with Cinzel
        assert "heading" in fonts or "serif" in fonts
        font_family = fonts.get("heading") or fonts.get("serif")
        assert "Cinzel" in str(font_family)

    def test_eb_garamond_for_body(self, theme_service, tailwind_config_path):
        """Test EB Garamond font is configured for body text."""
        fonts = theme_service.get_font_families(tailwind_config_path)

        # Should have serif category with EB Garamond
        assert "serif" in fonts
        assert "EB Garamond" in str(fonts["serif"])

    def test_gfs_didot_for_greek(self, theme_service, tailwind_config_path):
        """Test GFS Didot font is configured for Greek text."""
        fonts = theme_service.get_font_families(tailwind_config_path)

        # Should have greek category
        assert "greek" in fonts, "Greek font category missing"
        assert "GFS Didot" in str(fonts["greek"])

    def test_inter_preserved_for_ui(self, theme_service, tailwind_config_path):
        """Test Inter font is preserved for UI elements."""
        fonts = theme_service.get_font_families(tailwind_config_path)

        # Sans category should still have Inter
        assert "sans" in fonts
        assert "Inter" in str(fonts["sans"])

    # ========================================================================
    # CSS Custom Properties Tests
    # ========================================================================

    def test_css_custom_properties_defined(self, theme_service, global_css_path):
        """Test CSS custom properties for classical colors are defined."""
        css_vars = theme_service.get_css_custom_properties(global_css_path)

        # Check for color variables
        assert "--color-primary" in css_vars or "--classical-primary" in css_vars
        assert "--color-secondary" in css_vars or "--classical-secondary" in css_vars
        assert "--color-background" in css_vars or "--classical-background" in css_vars

    def test_parchment_background_styling(self, theme_service, global_css_path):
        """Test parchment background styling is applied in global CSS."""
        css_content = theme_service.read_css_file(global_css_path)

        # Should have parchment-related styling
        assert "parchment" in css_content.lower() or "E8DCC8" in css_content

    def test_classical_typography_rules_in_css(self, theme_service, global_css_path):
        """Test classical typography rules are defined in global CSS."""
        css_content = theme_service.read_css_file(global_css_path)

        # Should reference classical fonts
        assert "Cinzel" in css_content or "EB Garamond" in css_content or "GFS Didot" in css_content

    def test_warm_shadow_effects_defined(self, theme_service, global_css_path):
        """Test warm shadow effects are defined for classical aesthetic."""
        css_content = theme_service.read_css_file(global_css_path)

        # Should have custom shadow definitions
        # Look for box-shadow with warm colors or custom shadow variables
        assert "box-shadow" in css_content or "--shadow" in css_content

    def test_greek_text_styling(self, theme_service, global_css_path):
        """Test Greek text has special styling rules."""
        css_content = theme_service.read_css_file(global_css_path)

        # Should have .greek-text class or similar
        assert ".greek-text" in css_content or "greek" in css_content.lower()

    # ========================================================================
    # Accessibility & Contrast Tests
    # ========================================================================

    def test_wcag_aa_contrast_compliance(self, theme_service):
        """Test theme meets WCAG AA contrast requirements."""
        is_compliant = theme_service.validate_wcag_compliance()
        assert is_compliant is True, "Theme does not meet WCAG AA standards"

    def test_primary_text_on_background_contrast(self, theme_service):
        """Test primary text on background meets 4.5:1 contrast ratio."""
        text_color = CLASSICAL_COLORS["text"]["dark_brown"]
        bg_color = CLASSICAL_COLORS["background"]["warm_white"]

        contrast_ratio = theme_service.check_wcag_contrast(text_color, bg_color)
        assert contrast_ratio >= MIN_CONTRAST_RATIO, f"Contrast ratio {contrast_ratio} below minimum {MIN_CONTRAST_RATIO}"

    def test_primary_button_contrast(self, theme_service):
        """Test primary button (navy on warm white) meets contrast requirements."""
        button_bg = CLASSICAL_COLORS["primary"]["deep_navy"]
        button_text = CLASSICAL_COLORS["primary"]["deep_navy_content"]

        contrast_ratio = theme_service.check_wcag_contrast(button_text, button_bg)
        assert contrast_ratio >= MIN_CONTRAST_RATIO

    def test_secondary_text_contrast(self, theme_service):
        """Test secondary text (medium gray) on background meets contrast requirements."""
        text_color = CLASSICAL_COLORS["text"]["medium_gray"]
        bg_color = CLASSICAL_COLORS["background"]["light_beige"]

        contrast_ratio = theme_service.check_wcag_contrast(text_color, bg_color)
        assert contrast_ratio >= MIN_CONTRAST_RATIO

    def test_error_text_contrast(self, theme_service):
        """Test error text (terracotta) meets contrast requirements."""
        error_color = CLASSICAL_COLORS["status"]["error_terracotta"]
        bg_color = CLASSICAL_COLORS["background"]["warm_white"]

        contrast_ratio = theme_service.check_wcag_contrast(error_color, bg_color)
        assert contrast_ratio >= MIN_CONTRAST_RATIO

    # ========================================================================
    # Theme Validation Tests
    # ========================================================================

    def test_validate_classical_palette_complete(self, theme_service, tailwind_config_path):
        """Test complete classical palette validation."""
        is_valid = theme_service.validate_classical_palette(tailwind_config_path)
        assert is_valid is True, "Classical palette validation failed"

    def test_validate_all_required_colors_present(self, theme_service, tailwind_config_path):
        """Test all required color categories are present."""
        colors = theme_service.get_tailwind_colors(tailwind_config_path)

        required_keys = [
            "primary", "primary-focus", "primary-content",
            "secondary", "secondary-focus", "secondary-content",
            "accent", "accent-focus", "accent-content",
            "neutral", "neutral-focus", "neutral-content",
            "base-100", "base-200", "base-300", "base-content",
            "info", "success", "warning", "error"
        ]

        for key in required_keys:
            assert key in colors["arete"], f"Required color key '{key}' missing"

    def test_color_hex_format_validation(self, theme_service, tailwind_config_path):
        """Test all colors are in valid hex format."""
        colors = theme_service.get_tailwind_colors(tailwind_config_path)

        hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')

        for key, value in colors["arete"].items():
            if isinstance(value, str) and value.startswith('#'):
                assert hex_pattern.match(value), f"Invalid hex color format for {key}: {value}"

    def test_no_modern_tech_colors_remain(self, theme_service, tailwind_config_path):
        """Test modern tech colors (blue/purple) are replaced with classical palette."""
        colors = theme_service.get_tailwind_colors(tailwind_config_path)

        # Old colors that should NOT be present
        old_colors = ["#1e40af", "#7c3aed", "#059669"]  # Old blue, purple, green

        for color_value in colors["arete"].values():
            if isinstance(color_value, str):
                assert color_value not in old_colors, f"Old color {color_value} still present"

    # ========================================================================
    # Integration Tests
    # ========================================================================

    def test_theme_service_initialization(self, theme_service):
        """Test ThemeService initializes with correct config paths."""
        assert theme_service is not None
        assert hasattr(theme_service, 'tailwind_config_path')
        assert hasattr(theme_service, 'global_css_path')

    def test_get_classical_color_by_name(self, theme_service):
        """Test retrieval of specific classical colors by semantic name."""
        primary = theme_service.get_color("primary")
        assert primary == CLASSICAL_COLORS["primary"]["deep_navy"]

        secondary = theme_service.get_color("secondary")
        assert secondary == CLASSICAL_COLORS["secondary"]["warm_gold"]

        background = theme_service.get_color("background")
        assert background in CLASSICAL_COLORS["background"].values()

    def test_export_color_palette_for_documentation(self, theme_service):
        """Test color palette can be exported for documentation."""
        palette = theme_service.export_color_palette()

        assert "primary" in palette
        assert "secondary" in palette
        assert "background" in palette
        assert "text" in palette
        assert "status" in palette

    def test_validate_font_loading_in_css(self, theme_service, global_css_path):
        """Test font imports are present in global CSS."""
        css_content = theme_service.read_css_file(global_css_path)

        # Should have @import statements for Google Fonts
        assert "@import" in css_content
        assert "fonts.googleapis.com" in css_content or "Cinzel" in css_content


class TestThemeServiceUtilities:
    """Test utility methods for theme service."""

    @pytest.fixture
    def theme_service(self):
        """ThemeService instance for testing utilities."""
        from src.arete.ui.reflex_app.services.theme_service import ThemeService
        return ThemeService()

    def test_hex_to_rgb_conversion(self, theme_service):
        """Test hex color to RGB conversion."""
        rgb = theme_service.hex_to_rgb("#2C3E50")
        assert rgb == (44, 62, 80)

    def test_calculate_relative_luminance(self, theme_service):
        """Test relative luminance calculation for WCAG."""
        # White should have luminance of 1.0
        white_luminance = theme_service.calculate_luminance("#FFFFFF")
        assert white_luminance == pytest.approx(1.0, rel=0.01)

        # Black should have luminance of 0.0
        black_luminance = theme_service.calculate_luminance("#000000")
        assert black_luminance == pytest.approx(0.0, abs=0.01)

    def test_contrast_ratio_calculation(self, theme_service):
        """Test contrast ratio calculation between two colors."""
        # Black on white should be 21:1
        contrast = theme_service.check_wcag_contrast("#000000", "#FFFFFF")
        assert contrast == pytest.approx(21.0, rel=0.1)

    def test_color_brightness_calculation(self, theme_service):
        """Test color brightness calculation for automatic text color selection."""
        # Dark colors should return low brightness
        dark_brightness = theme_service.calculate_brightness(CLASSICAL_COLORS["primary"]["deep_navy"])
        assert dark_brightness < 128

        # Light colors should return high brightness
        light_brightness = theme_service.calculate_brightness(CLASSICAL_COLORS["background"]["warm_white"])
        assert light_brightness > 200

    def test_generate_color_shades(self, theme_service):
        """Test generation of color shades for hover/focus states."""
        base_color = CLASSICAL_COLORS["primary"]["deep_navy"]
        shades = theme_service.generate_shades(base_color, steps=5)

        assert len(shades) == 5
        # Should have darker and lighter variants
        assert shades[0] != shades[-1]


class TestThemeServiceErrorHandling:
    """Test error handling in theme service."""

    @pytest.fixture
    def theme_service(self):
        """ThemeService instance for testing errors."""
        from src.arete.ui.reflex_app.services.theme_service import ThemeService
        return ThemeService()

    def test_missing_tailwind_config_raises_error(self, theme_service):
        """Test error when tailwind.config.js is missing."""
        with pytest.raises(FileNotFoundError):
            theme_service.get_tailwind_config(Path("/nonexistent/tailwind.config.js"))

    def test_missing_global_css_raises_error(self, theme_service):
        """Test error when global.css is missing."""
        with pytest.raises(FileNotFoundError):
            theme_service.read_css_file(Path("/nonexistent/global.css"))

    def test_invalid_color_format_raises_error(self, theme_service):
        """Test error when color format is invalid."""
        with pytest.raises(ValueError):
            theme_service.hex_to_rgb("invalid-color")

    def test_incomplete_palette_validation_fails(self, theme_service):
        """Test validation fails when palette is incomplete."""
        # Mock incomplete palette
        with patch.object(theme_service, 'get_tailwind_colors') as mock_colors:
            mock_colors.return_value = {"arete": {"primary": "#2C3E50"}}  # Missing most colors

            is_valid = theme_service.validate_classical_palette(Path("dummy.js"))
            assert is_valid is False
