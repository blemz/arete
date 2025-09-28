#!/usr/bin/env python3
"""Script to fix Reflex icon issues"""

import os
import re

def fix_icon_issues(file_path):
    """Fix icon tag and size issues in Reflex files"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Show current content around line 220
    lines = content.split('\n')
    if len(lines) >= 220:
        print(f"Around line 220 in {file_path}:")
        for i in range(max(0, 215), min(len(lines), 225)):
            print(f"{i+1:3d}: {lines[i]}")

    # Fix help_circle -> circle_help
    content = content.replace('tag="help_circle"', 'tag="circle_help"')
    content = content.replace("tag='help_circle'", "tag='circle_help'")

    # Fix size strings to integers
    size_replacements = {
        'size="sm"': 'size=16',
        "size='sm'": 'size=16',
        'size="md"': 'size=20',
        "size='md'": 'size=20',
        'size="lg"': 'size=24',
        "size='lg'": 'size=24',
        'size="xl"': 'size=32',
        "size='xl'": 'size=32'
    }

    for old, new in size_replacements.items():
        content = content.replace(old, new)

    # Write back the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Fixed icon issues in {file_path}")

# Fix the main file
target_file = "D:\\Coding\\arete\\src\\arete\\ui\\reflex_app\\components\\chat_components.py"
fix_icon_issues(target_file)

# Also check other component files for similar issues
component_dir = "D:\\Coding\\arete\\src\\arete\\ui\\reflex_app\\components"
if os.path.exists(component_dir):
    for filename in os.listdir(component_dir):
        if filename.endswith('.py') and filename != 'chat_components.py':
            filepath = os.path.join(component_dir, filename)
            fix_icon_issues(filepath)