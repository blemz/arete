"""Custom styles and theme configuration for Arete."""

import reflex as rx

# Color palette inspired by classical philosophy
colors = {
    "primary": {
        "50": "#f9fafb",
        "100": "#f3f4f6", 
        "200": "#e5e7eb",
        "300": "#d1d5db",
        "400": "#9ca3af",
        "500": "#6b7280",
        "600": "#4b5563",
        "700": "#374151",
        "800": "#1f2937",
        "900": "#111827",
    },
    "accent": {
        "50": "#fef7ee",
        "100": "#fdecdc",
        "200": "#fad5b8", 
        "300": "#f6b583",
        "400": "#f1924c",
        "500": "#ed7525",
        "600": "#de5f1b",
        "700": "#b84a18",
        "800": "#923c1a",
        "900": "#773318",
    }
}

# Typography scale
typography = {
    "fonts": {
        "body": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "heading": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "mono": "'JetBrains Mono', 'SF Mono', Monaco, Inconsolata, 'Roboto Mono', monospace"
    },
    "font_sizes": {
        "xs": "0.75rem",
        "sm": "0.875rem", 
        "base": "1rem",
        "lg": "1.125rem",
        "xl": "1.25rem",
        "2xl": "1.5rem",
        "3xl": "1.875rem",
        "4xl": "2.25rem"
    },
    "line_heights": {
        "tight": "1.25",
        "snug": "1.375",
        "normal": "1.5",
        "relaxed": "1.625",
        "loose": "2"
    }
}

# Spacing scale
spacing = {
    "0": "0",
    "1": "0.25rem",
    "2": "0.5rem", 
    "3": "0.75rem",
    "4": "1rem",
    "5": "1.25rem",
    "6": "1.5rem",
    "8": "2rem",
    "10": "2.5rem",
    "12": "3rem",
    "16": "4rem",
    "20": "5rem",
    "24": "6rem"
}

# Border radius
border_radius = {
    "sm": "0.125rem",
    "base": "0.25rem",
    "md": "0.375rem",
    "lg": "0.5rem",
    "xl": "0.75rem",
    "2xl": "1rem",
    "full": "9999px"
}

# Shadows for depth
shadows = {
    "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
    "base": "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
    "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
    "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
    "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)"
}

# Component-specific styles
button_styles = {
    "base": {
        "font_weight": "500",
        "border_radius": border_radius["md"],
        "transition": "all 0.2s ease-in-out",
        "cursor": "pointer",
        "_hover": {
            "transform": "translateY(-1px)",
            "box_shadow": shadows["md"]
        },
        "_active": {
            "transform": "translateY(0)"
        },
        "_disabled": {
            "opacity": "0.6",
            "cursor": "not-allowed",
            "_hover": {
                "transform": "none"
            }
        }
    },
    "primary": {
        "background": colors["accent"]["600"],
        "color": "white",
        "_hover": {
            "background": colors["accent"]["700"]
        }
    },
    "secondary": {
        "background": colors["primary"]["100"],
        "color": colors["primary"]["900"],
        "_hover": {
            "background": colors["primary"]["200"]
        }
    }
}

card_styles = {
    "background": "white",
    "border_radius": border_radius["lg"],
    "box_shadow": shadows["base"],
    "border": f"1px solid {colors['primary']['200']}",
    "transition": "all 0.2s ease-in-out",
    "_hover": {
        "box_shadow": shadows["md"],
        "border_color": colors["accent"]["300"]
    }
}

input_styles = {
    "border": f"1px solid {colors['primary']['300']}",
    "border_radius": border_radius["md"],
    "padding": f"{spacing['2']} {spacing['3']}",
    "font_size": typography["font_sizes"]["base"],
    "transition": "all 0.2s ease-in-out",
    "_focus": {
        "outline": "none",
        "border_color": colors["accent"]["500"],
        "box_shadow": f"0 0 0 3px {colors['accent']['100']}"
    },
    "_disabled": {
        "background": colors["primary"]["50"],
        "cursor": "not-allowed"
    }
}

# Accessibility styles
accessibility_styles = {
    # High contrast mode
    "@media (prefers-contrast: high)": {
        "border_color": colors["primary"]["900"],
        "color": colors["primary"]["900"]
    },
    
    # Reduced motion
    "@media (prefers-reduced-motion: reduce)": {
        "animation": "none",
        "transition": "none"
    },
    
    # Focus visible styles
    "_focus_visible": {
        "outline": f"2px solid {colors['accent']['600']}",
        "outline_offset": "2px"
    }
}

# Dark theme overrides
dark_theme = {
    "background": colors["primary"]["900"],
    "color": colors["primary"]["50"],
    "card_background": colors["primary"]["800"],
    "border_color": colors["primary"]["700"]
}

# Export main style object
main_style = {
    "font_family": typography["fonts"]["body"],
    "line_height": typography["line_heights"]["normal"],
    "color": colors["primary"]["900"],
    "background": colors["primary"]["50"],
    **accessibility_styles
}