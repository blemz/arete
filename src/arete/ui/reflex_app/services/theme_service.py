"""
Service for validating and managing classical theme configuration.

Validates classical color palette, typography, and WCAG accessibility requirements.
"""
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import re


class ThemeService:
    """
    Service for validating classical theme configuration.

    Responsibilities:
    - Parse and validate Tailwind config for classical colors
    - Validate DaisyUI theme configuration
    - Check WCAG contrast compliance
    - Parse CSS custom properties
    - Validate typography configuration
    """

    # ========================================================================
    # WCAG Accessibility Constants
    # ========================================================================
    WCAG_AA_CONTRAST_RATIO = 4.5  # Minimum for normal text (WCAG 2.1 AA)
    WCAG_AAA_CONTRAST_RATIO = 7.0  # Enhanced contrast (WCAG 2.1 AAA)

    # ========================================================================
    # Color Brightness Constants (ITU-R BT.601)
    # ========================================================================
    BRIGHTNESS_R = 0.299  # Red channel weight for brightness calculation
    BRIGHTNESS_G = 0.587  # Green channel weight (human eye most sensitive)
    BRIGHTNESS_B = 0.114  # Blue channel weight

    # ========================================================================
    # Luminance Constants (WCAG 2.1)
    # ========================================================================
    LUMINANCE_R = 0.2126  # Red channel weight for relative luminance
    LUMINANCE_G = 0.7152  # Green channel weight
    LUMINANCE_B = 0.0722  # Blue channel weight

    # ========================================================================
    # Gamma Correction Constants (WCAG 2.1)
    # ========================================================================
    GAMMA_THRESHOLD = 0.03928      # Threshold for linear vs exponential gamma
    GAMMA_DIVISOR = 12.92          # Linear gamma divisor
    GAMMA_OFFSET = 0.055           # Exponential gamma offset
    GAMMA_MULTIPLIER = 1.055       # Exponential gamma multiplier
    GAMMA_EXPONENT = 2.4           # Exponential gamma exponent

    # ========================================================================
    # Regex Patterns (compiled for performance)
    # ========================================================================
    COLOR_PATTERN = re.compile(r"['\"]?([a-z0-9-]+)['\"]?:\s*['\"]?(#[A-Fa-f0-9]{6})['\"]?")
    FONT_PATTERN = re.compile(r"([a-z]+):\s*\[([^\]]+)\]")
    CSS_VAR_PATTERN = re.compile(r'(--[a-z-]+):\s*([^;]+);')
    DAISYUI_PATTERN = re.compile(r'classical:\s*{([^}]+)}')
    HEX_FORMAT_PATTERN = re.compile(r'^[0-9A-Fa-f]{6}$')

    def __init__(
        self,
        tailwind_config_path: Optional[Path] = None,
        global_css_path: Optional[Path] = None
    ):
        """
        Initialize theme service with configuration file paths.

        Args:
            tailwind_config_path: Path to tailwind.config.js
            global_css_path: Path to global.css
        """
        if tailwind_config_path is None:
            self.tailwind_config_path = Path(__file__).parent.parent / "tailwind.config.js"
        else:
            self.tailwind_config_path = tailwind_config_path

        if global_css_path is None:
            self.global_css_path = Path(__file__).parent.parent / "assets" / "styles" / "global.css"
        else:
            self.global_css_path = global_css_path

    # ========================================================================
    # Tailwind Configuration Methods
    # ========================================================================

    @lru_cache(maxsize=1)
    def _read_tailwind_config_cached(self, config_path_str: str) -> str:
        """
        Read tailwind.config.js with caching.

        Args:
            config_path_str: String path to config file (for hashable caching)

        Returns:
            File contents as string

        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        config_path = Path(config_path_str)
        if not config_path.exists():
            raise FileNotFoundError(f"Tailwind config not found: {config_path}")
        return config_path.read_text()

    def get_tailwind_config(self, config_path: Path) -> Dict[str, Any]:
        """
        Read and parse tailwind.config.js file.

        Args:
            config_path: Path to tailwind.config.js

        Returns:
            Parsed configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config parsing fails
        """
        content = self._read_tailwind_config_cached(str(config_path))

        # Parse DaisyUI themes
        config = {}
        config["daisyui"] = self._parse_daisyui_config(content)
        config["theme"] = self._parse_theme_config(content)

        return config

    def get_tailwind_colors(self, config_path: Path) -> Dict[str, Any]:
        """
        Extract color definitions from tailwind.config.js.

        Args:
            config_path: Path to tailwind.config.js

        Returns:
            Dictionary of color definitions with 'arete' namespace

        Example:
            {
                "arete": {
                    "primary": "#2C3E50",
                    "secondary": "#D4A574",
                    ...
                }
            }
        """
        content = self._read_tailwind_config_cached(str(config_path))

        # Extract arete colors from theme.extend.colors
        arete_colors = {}

        # Pattern to match arete color block
        arete_pattern = r'arete:\s*{([^}]+)}'
        match = re.search(arete_pattern, content, re.DOTALL)

        if match:
            arete_block = match.group(1)
            # Use pre-compiled pattern for performance
            colors = self.COLOR_PATTERN.findall(arete_block)
            arete_colors = {key: value for key, value in colors}

        return {"arete": arete_colors}

    def get_font_families(self, config_path: Path) -> Dict[str, List[str]]:
        """
        Extract font family definitions from tailwind.config.js.

        Args:
            config_path: Path to tailwind.config.js

        Returns:
            Dictionary of font families by category

        Example:
            {
                "heading": ["Cinzel", "serif"],
                "serif": ["EB Garamond", "Georgia", "serif"],
                "greek": ["GFS Didot", "serif"],
                "sans": ["Inter", "sans-serif"]
            }
        """
        content = self._read_tailwind_config_cached(str(config_path))

        fonts = {}

        # Extract fontFamily block
        font_pattern = r'fontFamily:\s*{([^}]+)}'
        match = re.search(font_pattern, content, re.DOTALL)

        if match:
            font_block = match.group(1)
            # Use pre-compiled pattern for performance
            categories = self.FONT_PATTERN.findall(font_block)

            for category, font_list in categories:
                # Clean up font names
                fonts_cleaned = [
                    f.strip().strip("'\"")
                    for f in font_list.split(',')
                ]
                fonts[category] = fonts_cleaned

        return fonts

    def _parse_daisyui_config(self, content: str) -> Dict[str, Any]:
        """Parse DaisyUI configuration from tailwind config."""
        daisyui = {}

        # Extract themes array
        themes_pattern = r'themes:\s*\[([^\]]+(?:\[[^\]]*\][^\]]*)*)\]'
        themes_match = re.search(themes_pattern, content, re.DOTALL)

        if themes_match:
            themes_content = themes_match.group(1)

            # Parse classical theme object using pre-compiled pattern
            classical_match = self.DAISYUI_PATTERN.search(themes_content)

            if classical_match:
                classical_block = classical_match.group(1)
                # Use pre-compiled COLOR_PATTERN for performance
                colors = self.COLOR_PATTERN.findall(classical_block)
                classical_theme = {key: value for key, value in colors}

                daisyui["themes"] = [{"classical": classical_theme}]

        return daisyui

    def _parse_theme_config(self, content: str) -> Dict[str, Any]:
        """Parse theme.extend configuration."""
        theme = {}

        # Check for extend.fontFamily
        if "fontFamily:" in content:
            theme["extend"] = {"fontFamily": self.get_font_families(Path(self.tailwind_config_path))}

        return theme

    # ========================================================================
    # CSS Methods
    # ========================================================================

    @lru_cache(maxsize=1)
    def _read_css_file_cached(self, css_path_str: str) -> str:
        """
        Read CSS file with caching.

        Args:
            css_path_str: String path to CSS file (for hashable caching)

        Returns:
            File contents as string

        Raises:
            FileNotFoundError: If CSS file doesn't exist
        """
        css_path = Path(css_path_str)
        if not css_path.exists():
            raise FileNotFoundError(f"CSS file not found: {css_path}")
        return css_path.read_text()

    def read_css_file(self, css_path: Path) -> str:
        """
        Read CSS file contents.

        Args:
            css_path: Path to CSS file

        Returns:
            CSS file contents as string

        Raises:
            FileNotFoundError: If CSS file doesn't exist
        """
        return self._read_css_file_cached(str(css_path))

    def get_css_custom_properties(self, css_path: Path) -> Dict[str, str]:
        """
        Extract CSS custom properties (variables) from global.css.

        Args:
            css_path: Path to global.css

        Returns:
            Dictionary of CSS custom properties

        Example:
            {
                "--color-primary": "#2C3E50",
                "--classical-background": "#E8DCC8",
                ...
            }
        """
        content = self.read_css_file(css_path)

        css_vars = {}

        # Extract CSS custom properties from :root
        root_pattern = r':root\s*{([^}]+)}'
        match = re.search(root_pattern, content, re.DOTALL)

        if match:
            root_block = match.group(1)
            # Use pre-compiled pattern for performance
            variables = self.CSS_VAR_PATTERN.findall(root_block)
            css_vars = {key: value.strip() for key, value in variables}

        return css_vars

    # ========================================================================
    # Validation Methods
    # ========================================================================

    def validate_classical_palette(self, config_path: Optional[Path] = None) -> bool:
        """
        Validate that classical color palette is properly configured.

        Args:
            config_path: Path to tailwind.config.js (uses default if None)

        Returns:
            True if palette is valid and complete, False otherwise
        """
        if config_path is None:
            config_path = self.tailwind_config_path

        try:
            colors = self.get_tailwind_colors(config_path)

            # Required color keys for classical palette
            required_keys = [
                "primary", "primary-focus", "primary-content",
                "secondary", "secondary-focus", "secondary-content",
                "accent", "accent-focus", "accent-content",
                "neutral", "neutral-focus", "neutral-content",
                "base-100", "base-200", "base-300", "base-content",
                "info", "success", "warning", "error"
            ]

            # Check all required keys exist in arete namespace
            if "arete" not in colors:
                return False

            for key in required_keys:
                if key not in colors["arete"]:
                    return False

            return True
        except Exception:
            return False

    def validate_wcag_compliance(self) -> bool:
        """
        Validate that theme meets WCAG AA contrast requirements.

        Returns:
            True if all color combinations meet WCAG AA (4.5:1 contrast), False otherwise
        """
        # Define critical color combinations to test
        test_combinations = [
            ("#3D3028", "#FAF8F5"),  # Dark brown text on warm white
            ("#FAF8F5", "#2C3E50"),  # Warm white text on deep navy (buttons)
            ("#6B625A", "#F5F0E8"),  # Medium gray on light beige
            ("#A85B52", "#FAF8F5"),  # Error terracotta on warm white
        ]

        for fg, bg in test_combinations:
            ratio = self.check_wcag_contrast(fg, bg)
            if ratio < self.WCAG_AA_CONTRAST_RATIO:
                return False

        return True

    def check_wcag_contrast(self, foreground: str, background: str) -> float:
        """
        Calculate WCAG contrast ratio between two colors.

        Args:
            foreground: Foreground color (hex format)
            background: Background color (hex format)

        Returns:
            Contrast ratio as float (1.0 to 21.0)

        Example:
            >>> service.check_wcag_contrast("#000000", "#FFFFFF")
            21.0
        """
        fg_luminance = self.calculate_luminance(foreground)
        bg_luminance = self.calculate_luminance(background)

        lighter = max(fg_luminance, bg_luminance)
        darker = min(fg_luminance, bg_luminance)

        return (lighter + 0.05) / (darker + 0.05)

    # ========================================================================
    # Color Utility Methods
    # ========================================================================

    def hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """
        Convert hex color to RGB tuple.

        Args:
            hex_color: Color in hex format (e.g., "#2C3E50")

        Returns:
            RGB tuple (r, g, b) with values 0-255

        Raises:
            ValueError: If hex color format is invalid

        Example:
            >>> service.hex_to_rgb("#2C3E50")
            (44, 62, 80)
        """
        # Validate and clean input
        if not hex_color.startswith('#'):
            raise ValueError(f"Color must start with #, got: {hex_color}")

        # Remove # prefix
        hex_color = hex_color.lstrip('#')

        # Validate length
        if len(hex_color) != 6:
            raise ValueError(f"Color must be 7 characters (#RRGGBB), got {len(hex_color) + 1}: #{hex_color}")

        # Validate format using pre-compiled pattern
        if not self.HEX_FORMAT_PATTERN.match(hex_color):
            raise ValueError(f"Invalid hex characters in: #{hex_color}")

        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        return (r, g, b)

    def calculate_luminance(self, hex_color: str) -> float:
        """
        Calculate relative luminance for WCAG contrast calculations.

        Args:
            hex_color: Color in hex format

        Returns:
            Relative luminance (0.0 to 1.0)

        Reference:
            https://www.w3.org/TR/WCAG20/#relativeluminancedef
        """
        r, g, b = self.hex_to_rgb(hex_color)

        # Convert to 0-1 range
        r = r / 255.0
        g = g / 255.0
        b = b / 255.0

        # Apply gamma correction using class constants
        def adjust(channel: float) -> float:
            if channel <= self.GAMMA_THRESHOLD:
                return channel / self.GAMMA_DIVISOR
            return ((channel + self.GAMMA_OFFSET) / self.GAMMA_MULTIPLIER) ** self.GAMMA_EXPONENT

        r = adjust(r)
        g = adjust(g)
        b = adjust(b)

        # Calculate relative luminance using WCAG weights
        return self.LUMINANCE_R * r + self.LUMINANCE_G * g + self.LUMINANCE_B * b

    def calculate_brightness(self, hex_color: str) -> float:
        """
        Calculate perceived brightness of a color.

        Args:
            hex_color: Color in hex format

        Returns:
            Brightness value (0-255)

        Note:
            Uses ITU-R BT.601 luma coefficients for perceived brightness.
            Human eye is more sensitive to green channel.
        """
        r, g, b = self.hex_to_rgb(hex_color)

        # Perceived brightness using ITU-R BT.601 weighted average
        return (r * self.BRIGHTNESS_R + g * self.BRIGHTNESS_G + b * self.BRIGHTNESS_B)

    def generate_shades(self, base_color: str, steps: int = 5) -> List[str]:
        """
        Generate color shades from a base color.

        Args:
            base_color: Base color in hex format
            steps: Number of shade variations to generate

        Returns:
            List of hex colors from darkest to lightest

        Used for generating hover/focus state colors.
        """
        r, g, b = self.hex_to_rgb(base_color)

        shades = []

        # Generate darker to lighter shades
        for i in range(steps):
            # Factor from 0.5 (darkest) to 1.5 (lightest)
            factor = 0.5 + (i / (steps - 1))

            # Apply factor
            new_r = min(255, int(r * factor))
            new_g = min(255, int(g * factor))
            new_b = min(255, int(b * factor))

            # Convert back to hex
            hex_shade = f"#{new_r:02x}{new_g:02x}{new_b:02x}"
            shades.append(hex_shade)

        return shades

    # ========================================================================
    # Query Methods
    # ========================================================================

    def get_color(self, color_name: str) -> str:
        """
        Get specific classical color by semantic name.

        Args:
            color_name: Semantic name (e.g., "primary", "secondary", "background")

        Returns:
            Hex color code

        Raises:
            KeyError: If color name not found
        """
        # Classical color palette mapping
        color_map = {
            "primary": "#2C3E50",           # Deep Navy Blue
            "secondary": "#D4A574",         # Warm Gold
            "accent": "#C9A961",            # Golden Accent
            "background": "#FAF8F5",        # Warm White (default background)
            "text": "#3D3028",              # Dark Brown (default text)
            "neutral": "#6B625A",           # Medium Gray
            "success": "#7B9E87",           # Sage Green
            "warning": "#C9A961",           # Warning Gold
            "error": "#A85B52",             # Error Terracotta
        }

        if color_name not in color_map:
            raise KeyError(f"Color '{color_name}' not found in classical palette")

        return color_map[color_name]

    def export_color_palette(self) -> Dict[str, Dict[str, str]]:
        """
        Export complete color palette for documentation.

        Returns:
            Dictionary organized by color categories

        Example:
            {
                "primary": {
                    "deep_navy": "#2C3E50",
                    "deep_navy_focus": "#1a252f"
                },
                "secondary": {...},
                "background": {...},
                "text": {...},
                "status": {...}
            }
        """
        return {
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
