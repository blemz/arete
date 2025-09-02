"""
Responsive Design Service for Streamlit UI.

This service provides responsive design capabilities for the Arete Streamlit
interface, ensuring optimal user experience across different devices and screen sizes.
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum


class BreakpointSize(Enum):
    """Standard responsive breakpoint sizes."""
    MOBILE = 480
    TABLET = 768
    DESKTOP = 1024
    WIDE = 1440


class DeviceType(Enum):
    """Device type classifications."""
    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"
    WIDE_DESKTOP = "wide_desktop"


@dataclass
class ResponsiveConfig:
    """Configuration for responsive design features."""
    enable_mobile_optimization: bool = True
    enable_tablet_optimization: bool = True
    mobile_breakpoint: int = 480
    tablet_breakpoint: int = 768
    desktop_breakpoint: int = 1024
    compact_sidebar_on_mobile: bool = True
    stack_columns_on_mobile: bool = True
    adjust_font_sizes: bool = True


class ResponsiveDesignService:
    """Service for implementing responsive design in Streamlit."""
    
    def __init__(self, config: Optional[ResponsiveConfig] = None):
        """Initialize the responsive design service."""
        self.config = config or ResponsiveConfig()
        
    def generate_responsive_css(
        self,
        compact_mode: bool = False,
        font_scale: float = 1.0
    ) -> str:
        """Generate responsive CSS for the Streamlit app."""
        css_methods = [
            self._get_base_responsive_css(),
            self._get_mobile_css(),
            self._get_tablet_css(),
            self._get_desktop_css()
        ]
        
        if compact_mode:
            css_methods.append(self._get_compact_mode_css())
            
        if font_scale != 1.0:
            css_methods.append(self._get_font_scale_css(font_scale))
        
        # Extract CSS content from each method (remove <style> tags)
        css_content_parts = []
        for css_block in filter(None, css_methods):
            # Remove <style> and </style> tags and extract content
            content = css_block.strip()
            if content.startswith('<style>'):
                content = content[7:]  # Remove <style>
            if content.endswith('</style>'):
                content = content[:-8]  # Remove </style>
            css_content_parts.append(content.strip())
        
        # Combine all CSS content into a single <style> block
        combined_css = "\n".join(css_content_parts)
        return f"<style>\n{combined_css}\n</style>"
    
    def _get_base_responsive_css(self) -> str:
        """Get base responsive CSS that applies to all screen sizes."""
        return """
        <style>
        /* Base Responsive Design */
        
        /* Responsive containers */
        .main {
            max-width: 100% !important;
            overflow-x: hidden !important;
        }
        
        /* Responsive images */
        img {
            max-width: 100% !important;
            height: auto !important;
        }
        
        /* Flexible layouts */
        .stColumns {
            flex-wrap: wrap !important;
        }
        
        /* Responsive text */
        .stMarkdown {
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
        }
        </style>
        """
        
    def _get_mobile_css(self) -> str:
        """Get CSS optimizations for mobile devices."""
        if not self.config.enable_mobile_optimization:
            return ""
            
        return f"""
        <style>
        /* Mobile Optimizations */
        @media (max-width: {self.config.mobile_breakpoint}px) {{
            .main {{
                padding: 0.5rem !important;
            }}
            
            .stSidebar {{
                width: 100% !important;
                position: relative !important;
            }}
            
            /* Stack columns on mobile */
            .stColumns > div {{
                width: 100% !important;
                margin-bottom: 1rem !important;
            }}
            
            /* Larger touch targets for mobile */
            .stButton > button {{
                min-height: 44px !important;
                min-width: 44px !important;
                font-size: 1.1rem !important;
            }}
            
            /* Prevent zoom on input focus */
            .stTextInput input, .stTextArea textarea {{
                font-size: 16px !important;
            }}
            
            /* Mobile-friendly chat */
            .stChatMessage {{
                margin: 0.25rem 0 !important;
                padding: 0.75rem !important;
            }}
        }}
        </style>
        """
        
    def _get_tablet_css(self) -> str:
        """Get CSS optimizations for tablet devices."""
        if not self.config.enable_tablet_optimization:
            return ""
            
        return f"""
        <style>
        /* Tablet Optimizations */
        @media (min-width: {self.config.mobile_breakpoint + 1}px) and (max-width: {self.config.tablet_breakpoint}px) {{
            .main {{
                padding: 1rem 0.75rem !important;
            }}
            
            .stSidebar {{
                width: 250px !important;
            }}
            
            /* Tablet button sizing */
            .stButton > button {{
                min-height: 40px !important;
                min-width: 40px !important;
            }}
            
            /* Tablet chat sizing */
            .stChatMessage {{
                margin: 0.5rem 0 !important;
                padding: 1rem !important;
            }}
        }}
        </style>
        """
        
    def _get_desktop_css(self) -> str:
        """Get CSS optimizations for desktop devices."""
        return f"""
        <style>
        /* Desktop Optimizations */
        @media (min-width: {self.config.desktop_breakpoint}px) {{
            .main {{
                padding: 1rem 2rem !important;
                max-width: 1200px !important;
                margin: 0 auto !important;
            }}
            
            .stSidebar {{
                width: 300px !important;
            }}
            
            /* Desktop spacing */
            .stChatMessage {{
                margin: 0.75rem 0 !important;
                padding: 1.25rem !important;
            }}
        }}
        </style>
        """
        
    def _get_compact_mode_css(self) -> str:
        """Get CSS for compact mode."""
        return """
        <style>
        /* Compact Mode */
        .main {
            padding-top: 0.5rem !important;
        }
        
        .stChatMessage {
            margin: 0.25rem 0 !important;
            padding: 0.5rem !important;
        }
        
        .stButton > button {
            padding: 0.25rem 0.5rem !important;
        }
        
        h1, h2, h3, h4, h5, h6 {
            margin: 0.5rem 0 !important;
        }
        </style>
        """
        
    def _get_font_scale_css(self, scale: float) -> str:
        """Get CSS for font scaling."""
        return f"""
        <style>
        /* Font Scaling */
        .main {{
            font-size: {scale}rem !important;
        }}
        
        h1 {{ font-size: {scale * 2.5}rem !important; }}
        h2 {{ font-size: {scale * 2}rem !important; }}
        h3 {{ font-size: {scale * 1.75}rem !important; }}
        h4 {{ font-size: {scale * 1.5}rem !important; }}
        h5 {{ font-size: {scale * 1.25}rem !important; }}
        h6 {{ font-size: {scale * 1.1}rem !important; }}
        </style>
        """
        
    def get_device_type(self, width: int) -> DeviceType:
        """Determine device type based on screen width."""
        if width <= self.config.mobile_breakpoint:
            return DeviceType.MOBILE
        elif width <= self.config.tablet_breakpoint:
            return DeviceType.TABLET
        elif width <= self.config.desktop_breakpoint:
            return DeviceType.DESKTOP
        else:
            return DeviceType.WIDE_DESKTOP
            
    def get_optimal_sidebar_state(self, device_type: DeviceType) -> str:
        """Get optimal sidebar state for device type."""
        if device_type == DeviceType.MOBILE:
            return "collapsed"
        elif device_type == DeviceType.TABLET:
            return "auto"
        else:
            return "expanded"

    def detect_device_type(self) -> DeviceType:
        """Detect device type using browser user agent (Streamlit compatible)."""
        # For Streamlit, we'll default to desktop and let CSS handle responsiveness
        # In a real implementation, this would use JavaScript to detect screen width
        return DeviceType.DESKTOP
        
    def get_responsive_layout_config(self, device_type: Optional[DeviceType] = None) -> Dict[str, Any]:
        """Get responsive layout configuration for the given device type."""
        if device_type is None:
            device_type = self.detect_device_type()
            
        return {
            'layout': 'wide' if device_type in [DeviceType.DESKTOP, DeviceType.WIDE_DESKTOP] else 'centered',
            'sidebar_state': self.get_optimal_sidebar_state(device_type),
            'initial_sidebar_state': self.get_optimal_sidebar_state(device_type)
        }

    def generate_viewport_meta_tag(self) -> str:
        """Generate viewport meta tag for responsive design."""
        return '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">'

        
    def get_responsive_css(self, device_type: Optional[DeviceType] = None) -> str:
        """Get responsive CSS for the given device type."""
        return self.generate_responsive_css(
            compact_mode=(device_type == DeviceType.MOBILE if device_type else False),
            font_scale=0.9 if device_type == DeviceType.MOBILE else 1.0
        )

        
    def optimize_for_mobile(self) -> None:
        """Optimize the service configuration for mobile devices."""
        # This is a placeholder method for mobile optimization
        # In a real implementation, this might adjust configuration settings
        # or prepare mobile-specific resources
        pass
