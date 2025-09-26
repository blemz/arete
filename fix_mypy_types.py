#!/usr/bin/env python3
"""
Script to fix mypy type errors by adding -> None return type annotations.
"""

import os
import re

def fix_file(filepath):
    """Fix return type annotations in a Python file."""
    print(f"Fixing {filepath}...")

    # Read the file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern to match function definitions without return type annotations
    # This matches: def function_name(...): but not def function_name(...) -> ReturnType:
    pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)(?!\s*->):'

    def replacement(match):
        # Extract the full function signature
        full_match = match.group(0)
        # Add -> None before the colon
        return full_match[:-1] + ' -> None:'

    # Apply the replacement
    fixed_content = re.sub(pattern, replacement, content)

    # Write back to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(fixed_content)

    print(f"✅ Fixed {filepath}")

def main():
    """Fix all script files."""
    files_to_fix = [
        'scripts/test_minimal.py',
        'scripts/test_enhanced_prompt.py',
        'scripts/comprehensive_prompt_test.py',
        'scripts/verify_final.py',
        'scripts/verify_databases.py',
        'scripts/verify_database_content.py',
        'scripts/debug_embeddings.py',
        'scripts/clear_databases.py'
    ]

    base_path = 'D:/Coding/arete'

    for file_path in files_to_fix:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            fix_file(full_path)
        else:
            print(f"⚠️ File not found: {full_path}")

    print("🎉 All files processed!")

if __name__ == "__main__":
    main()