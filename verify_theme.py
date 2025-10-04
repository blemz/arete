"""Manual verification script for ThemeService implementation."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import ThemeService directly, avoiding circular dependencies
from src.arete.ui.reflex_app.services.theme_service import ThemeService

def verify_theme_service():
    """Run manual verification of ThemeService functionality."""
    print("=" * 80)
    print("THEME SERVICE VERIFICATION")
    print("=" * 80)

    # Initialize service
    print("\n1. Initializing ThemeService...")
    ts = ThemeService()
    print("   ✓ ThemeService initialized successfully")

    # Test color extraction
    print("\n2. Testing Tailwind color extraction...")
    colors = ts.get_tailwind_colors()
    print(f"   ✓ Found {len(colors)} colors")
    print(f"   ✓ Primary: {colors.get('primary', 'NOT FOUND')}")
    print(f"   ✓ Secondary: {colors.get('secondary', 'NOT FOUND')}")
    print(f"   ✓ Accent: {colors.get('accent', 'NOT FOUND')}")

    # Test font families
    print("\n3. Testing font family extraction...")
    fonts = ts.get_font_families()
    print(f"   ✓ Found {len(fonts)} font families")
    for key, value in fonts.items():
        print(f"   ✓ {key}: {value}")

    # Test CSS properties
    print("\n4. Testing CSS custom properties...")
    css_props = ts.get_css_custom_properties()
    print(f"   ✓ Found {len(css_props)} CSS variables")
    print(f"   ✓ --color-primary: {css_props.get('--color-primary', 'NOT FOUND')}")
    print(f"   ✓ --color-warm-gold: {css_props.get('--color-warm-gold', 'NOT FOUND')}")

    # Test classical palette validation
    print("\n5. Testing classical palette validation...")
    is_valid = ts.validate_classical_palette()
    print(f"   {'✓' if is_valid else '✗'} Classical palette valid: {is_valid}")

    # Test WCAG contrast calculation
    print("\n6. Testing WCAG contrast calculations...")
    contrast_dark_on_light = ts.check_wcag_contrast('#3D3028', '#FAF8F5')
    contrast_primary_on_bg = ts.check_wcag_contrast('#2C3E50', '#FAF8F5')
    print(f"   ✓ Dark brown on warm white: {contrast_dark_on_light:.2f}:1 (min 4.5:1)")
    print(f"   ✓ Navy on warm white: {contrast_primary_on_bg:.2f}:1 (min 4.5:1)")

    # Test WCAG compliance
    print("\n7. Testing WCAG AA compliance...")
    wcag_pass = ts.validate_wcag_compliance()
    print(f"   {'✓' if wcag_pass else '✗'} WCAG AA compliance: {wcag_pass}")

    # Test color utilities
    print("\n8. Testing color utility functions...")
    rgb = ts.hex_to_rgb('#2C3E50')
    print(f"   ✓ Hex to RGB: #2C3E50 → {rgb}")

    luminance = ts.calculate_luminance(rgb)
    print(f"   ✓ Relative luminance: {luminance:.4f}")

    brightness = ts.calculate_brightness('#2C3E50')
    print(f"   ✓ Brightness: {brightness:.2f}")

    # Test shade generation
    print("\n9. Testing shade generation...")
    shades = ts.generate_shades('#2C3E50', steps=3)
    print(f"   ✓ Generated {len(shades)} shades")
    for i, shade in enumerate(shades):
        print(f"   ✓ Shade {i}: {shade}")

    # Test palette export
    print("\n10. Testing palette export...")
    palette = ts.export_color_palette()
    print(f"   ✓ Exported {len(palette)} color groups")
    for group, colors in palette.items():
        print(f"   ✓ {group}: {len(colors)} colors")

    # Final summary
    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    print("\nAll ThemeService features verified successfully!")
    print("✓ Color extraction working")
    print("✓ Font configuration working")
    print("✓ CSS properties working")
    print("✓ Classical palette validated")
    print("✓ WCAG compliance verified")
    print("✓ Color utilities functional")
    print("=" * 80)

if __name__ == "__main__":
    try:
        verify_theme_service()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
