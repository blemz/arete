#!/usr/bin/env python3
"""
Standalone AI Restructuring Script for Enhanced Markdown Files

This script takes enhanced markdown files (*_enhanced.md) and converts them
to AI-restructured files (*_ai_restructured.md) using the PhilosophicalTextRestructurer.

Usage:
    python restructure_enhanced_text.py "path/to/file_enhanced.md"

Example:
    python restructure_enhanced_text.py "data/processed/Plato The Republic (Cambridge, Tom Griffith) Clean_enhanced.md"

Output:
    Creates: "data/processed/Plato The Republic (Cambridge, Tom Griffith) Clean_ai_restructured.md"
"""

import asyncio
import sys
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arete.services.philosophical_text_restructurer import (
    PhilosophicalTextRestructurer,
    PhilosophicalContext,
    ProcessingMode
)


def extract_metadata_from_enhanced_file(file_path: Path) -> PhilosophicalContext:
    """Extract metadata from enhanced markdown file YAML frontmatter."""

    # Read the first part of the file to get YAML frontmatter
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Default context for philosophical texts
    context = PhilosophicalContext(
        author="Unknown",
        work_title=file_path.stem.replace('_enhanced', ''),
        philosophical_period="Ancient",
        text_type="dialogue",
        key_concepts=["wisdom", "virtue", "knowledge", "justice"],
        major_themes=["ethics", "epistemology", "metaphysics"]
    )

    # Try to extract from YAML frontmatter if present
    if content.startswith('---'):
        try:
            yaml_end = content.find('---', 3)
            if yaml_end > 0:
                yaml_content = content[3:yaml_end].strip()

                # Simple YAML parsing for common fields
                for line in yaml_content.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')

                        if key == 'title':
                            context.work_title = value
                        elif key == 'author':
                            context.author = value
                        elif key == 'philosophical_period':
                            context.philosophical_period = value
                        elif key == 'text_type':
                            context.text_type = value
        except Exception:
            # If YAML parsing fails, use defaults
            pass

    return context


async def restructure_enhanced_file(input_path: str) -> str:
    """
    Convert an enhanced markdown file to AI-restructured format.

    Args:
        input_path: Path to the *_enhanced.md file

    Returns:
        Path to the created *_ai_restructured.md file
    """

    input_file = Path(input_path)

    # Validate input file
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if not input_file.name.endswith('_enhanced.md'):
        raise ValueError(f"Input file must be an enhanced markdown file (*_enhanced.md): {input_file.name}")

    # Generate output filename
    output_file = input_file.parent / input_file.name.replace('_enhanced.md', '_ai_restructured.md')

    print(f"🏛️ AI Restructuring Enhanced Philosophical Text")
    print(f"================================================================================")
    print(f"📖 Input:  {input_file.name}")
    print(f"📄 Output: {output_file.name}")
    print(f"🤖 Mode:   Full AI Restructuring with Philosophical Analysis")
    print(f"================================================================================")

    # Extract context from enhanced file
    print(f"\n=== Step 1: Extracting Metadata ===")
    context = extract_metadata_from_enhanced_file(input_file)
    print(f"✅ Author: {context.author}")
    print(f"✅ Work: {context.work_title}")
    print(f"✅ Period: {context.philosophical_period}")
    print(f"✅ Type: {context.text_type}")

    # Initialize restructurer
    print(f"\n=== Step 2: Initializing AI Restructurer ===")
    restructurer = PhilosophicalTextRestructurer()
    print(f"✅ Provider: {restructurer.kg_provider}")
    print(f"✅ Model: {restructurer.kg_model}")

    # Perform restructuring
    print(f"\n=== Step 3: AI Restructuring Process ===")
    print(f"🔄 Processing with LLM-enhanced philosophical analysis...")

    try:
        result_path = await restructurer.restructure_file(
            input_file=input_file,
            output_file=output_file,
            mode=ProcessingMode.FULL_RESTRUCTURE,
            context=context
        )

        print(f"✅ AI restructuring completed successfully!")
        print(f"📊 Output file: {result_path}")

        # Show file statistics
        with open(result_path, 'r', encoding='utf-8') as f:
            content = f.read()
            char_count = len(content)
            line_count = len(content.split('\n'))

        print(f"\n=== Results ===")
        print(f"📄 File size: {char_count:,} characters")
        print(f"📝 Lines: {line_count:,}")
        print(f"🏛️ Enhanced with philosophical structure and analysis")
        print(f"🤖 Ready for superior RAG ingestion")

        return str(result_path)

    except Exception as e:
        print(f"❌ AI restructuring failed: {e}")
        raise


def main():
    """Main entry point for the restructuring script."""

    if len(sys.argv) != 2:
        print("Usage: python restructure_enhanced_text.py <path_to_enhanced_file>")
        print("\nExample:")
        print('  python restructure_enhanced_text.py "data/processed/Plato The Republic (Cambridge, Tom Griffith) Clean_enhanced.md"')
        print("\nSupported input:")
        print("  - Files ending with '_enhanced.md'")
        print("\nOutput:")
        print("  - Creates corresponding '_ai_restructured.md' file")
        print("  - Enhanced with AI philosophical analysis")
        print("  - Ready for RAG system ingestion")
        return

    input_path = sys.argv[1]

    try:
        result_path = asyncio.run(restructure_enhanced_file(input_path))
        print(f"\n🎉 SUCCESS: AI-restructured file created!")
        print(f"📂 Location: {result_path}")
        print(f"\n📋 Next steps:")
        print(f"  1. Review the AI-restructured content")
        print(f"  2. Ingest into RAG system if satisfied")
        print(f"  3. Test with chat interface")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()