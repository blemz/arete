#!/usr/bin/env python3
"""
Simple test for Philosophical Text Restructuring Service
"""

import sys
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arete.services.philosophical_text_restructurer import (
    PhilosophicalTextRestructurer,
    ProcessingMode,
    PhilosophicalContext
)


async def simple_test():
    """Simple test of the restructuring service."""
    
    print("Philosophical Text Restructuring Test")
    print("=" * 50)
    
    # Sample text from Socratic dialogue
    sample_text = """
How you, O Athenians, have been affected by my accusers, I cannot tell; but I know that they almost made me forget who I was--so persuasively did they speak; and yet they have hardly uttered a word of truth. But of the many falsehoods told by them, there was one which quite amazed me;--I mean when they said that you should be upon your guard and not allow yourselves to be deceived by the force of my eloquence. To say this, when they were certain to be detected as soon as I opened my lips and proved myself to be anything but a great speaker, did indeed appear to me most shameless--unless by the force of eloquence they mean the force of truth; for is such is their meaning, I admit that I am eloquent.
"""
    
    print("Initializing restructurer...")
    restructurer = PhilosophicalTextRestructurer()
    print(f"Provider: {restructurer.kg_provider}")
    print(f"Model: {restructurer.kg_model}")
    print()
    
    # Test dialogue separation
    print("Testing dialogue separation...")
    context = PhilosophicalContext(
        author="Plato",
        work_title="Apology",
        philosophical_period="Ancient",
        text_type="dialogue"
    )
    
    try:
        result = await restructurer.restructure_text(
            text=sample_text,
            mode=ProcessingMode.DIALOGUE_SEPARATION,
            context=context
        )
        
        print("SUCCESS!")
        print(f"Original length: {len(sample_text)}")
        print(f"Restructured length: {len(result.restructured_text)}")
        print()
        print("First 500 characters of result:")
        print("-" * 30)
        print(result.restructured_text[:500])
        print("-" * 30)
        
        # Save result
        output_file = Path("test_output.md")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.restructured_text)
        print(f"Saved to: {output_file}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


def main():
    asyncio.run(simple_test())


if __name__ == "__main__":
    main()