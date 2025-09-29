#!/usr/bin/env python3
"""Apply specific icon fixes to Reflex app"""

import os
import re

def apply_fixes():
    """Apply icon fixes to all component files"""

    # Main file to fix
    file_path = "D:\\Coding\\arete\\src\\arete\\ui\\reflex_app\\components\\chat_components.py"

    if os.path.exists(file_path):
        print(f"Fixing {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Track changes
        changes_made = []

        # Fix 1: help_circle -> circle_help
        if 'help_circle' in content:
            content = re.sub(r'tag=["\']help_circle["\']', 'tag="circle_help"', content)
            changes_made.append("Fixed help_circle -> circle_help")

        # Fix 2: String sizes to integers
        size_fixes = [
            (r'size=["\']sm["\']', 'size=16'),
            (r'size=["\']md["\']', 'size=20'),
            (r'size=["\']lg["\']', 'size=24'),
            (r'size=["\']xl["\']', 'size=32'),
            (r'size=["\']xs["\']', 'size=12'),
        ]

        for pattern, replacement in size_fixes:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made.append(f"Fixed {pattern} -> {replacement}")

        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"Changes made: {changes_made}")
    else:
        print(f"File not found: {file_path}")

    # Check other component files
    component_dir = "D:\\Coding\\arete\\src\\arete\\ui\\reflex_app\\components"

    if os.path.exists(component_dir):
        for filename in os.listdir(component_dir):
            if filename.endswith('.py') and 'chat_components' not in filename:
                filepath = os.path.join(component_dir, filename)

                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check if fixes needed
                needs_fix = False

                if 'help_circle' in content:
                    content = re.sub(r'tag=["\']help_circle["\']', 'tag="circle_help"', content)
                    needs_fix = True

                for pattern, replacement in size_fixes:
                    if re.search(pattern, content):
                        content = re.sub(pattern, replacement, content)
                        needs_fix = True

                if needs_fix:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Fixed icons in {filename}")

if __name__ == "__main__":
    apply_fixes()
    print("Icon fixes completed!")