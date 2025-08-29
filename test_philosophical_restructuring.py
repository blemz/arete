#!/usr/bin/env python3
"""
Test script for Philosophical Text Restructuring Service

Demonstrates the restructuring of the Socratic Dialogues file using
KG_LLM_PROVIDER and KG_LLM_MODEL configuration.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from arete.services.philosophical_text_restructurer import (
    PhilosophicalTextRestructurer,
    ProcessingMode,
    PhilosophicalContext,
    restructure_socratic_dialogue
)


async def test_socratic_dialogues_restructuring():
    """Test restructuring of the Socratic Dialogues file."""
    
    print("Philosophical Text Restructuring Test")
    print("=" * 60)
    print()
    
    # File paths
    input_file = Path("processed_texts/Socratis Dialogues_First_2_books_structured.md")
    output_dir = Path("restructured_texts")
    output_dir.mkdir(exist_ok=True)
    
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        print("Please ensure the file exists or update the path")
        return
    
    print(f"📖 Input file: {input_file}")
    print(f"📁 Output directory: {output_dir}")
    print()
    
    # Initialize restructurer
    print("🔧 Initializing Philosophical Text Restructurer...")
    restructurer = PhilosophicalTextRestructurer()
    print(f"   Provider: {restructurer.kg_provider}")
    print(f"   Model: {restructurer.kg_model}")
    print()
    
    # Create context for Socratic dialogues
    context = PhilosophicalContext(
        author="Plato",
        work_title="Socratic Dialogues (Apology & Charmides)",
        philosophical_period="Ancient",
        text_type="dialogue",
        key_concepts=["wisdom", "temperance", "virtue", "knowledge", "justice", "piety"],
        major_themes=["epistemology", "ethics", "virtue theory", "Socratic method"]
    )
    
    print("📋 Processing Context:")
    print(f"   Author: {context.author}")
    print(f"   Work: {context.work_title}")
    print(f"   Type: {context.text_type}")
    print(f"   Key Concepts: {', '.join(context.key_concepts[:3])}...")
    print()
    
    # Test different processing modes
    test_modes = [
        (ProcessingMode.DIALOGUE_SEPARATION, "Dialogue Speaker Separation"),
        (ProcessingMode.ARGUMENT_EXTRACTION, "Philosophical Argument Extraction"),
        (ProcessingMode.ENTITY_MARKUP, "Entity Identification & Markup"),
        (ProcessingMode.CITATION_FORMATTING, "Citation-Ready Formatting")
    ]
    
    results = {}
    
    for mode, description in test_modes:
        print(f"🔄 Processing: {description}")
        print(f"   Mode: {mode.value}")
        
        try:
            # Process the file
            output_file = await restructurer.restructure_file(
                input_file=input_file,
                output_file=output_dir / f"socratic_dialogues_{mode.value}.md",
                mode=mode,
                context=context
            )
            
            # Check results
            with open(output_file, 'r', encoding='utf-8') as f:
                restructured_content = f.read()
            
            results[mode] = {
                'output_file': output_file,
                'original_size': input_file.stat().st_size,
                'restructured_size': len(restructured_content),
                'success': True
            }
            
            print(f"   ✅ Success: {output_file.name}")
            print(f"   📏 Size: {input_file.stat().st_size:,} → {len(restructured_content):,} chars")
            print()
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results[mode] = {'success': False, 'error': str(e)}
            print()
    
    # Test full restructuring with convenience function
    print("🔄 Testing Convenience Function: Socratic Dialogue Restructuring")
    try:
        # Read a sample from the original file for testing
        with open(input_file, 'r', encoding='utf-8') as f:
            sample_text = f.read()[:3000]  # First 3000 chars for testing
        
        result = await restructure_socratic_dialogue(
            text=sample_text,
            author="Plato",
            work_title="Apology"
        )
        
        # Save sample result
        sample_output = output_dir / "socratic_dialogue_sample.md"
        with open(sample_output, 'w', encoding='utf-8') as f:
            f.write("# Sample Socratic Dialogue Restructuring\n\n")
            f.write(f"**Original Length:** {len(sample_text)} characters\n")
            f.write(f"**Restructured Length:** {len(result.restructured_text)} characters\n")
            f.write(f"**Processing Mode:** {result.processing_mode.value}\n\n")
            f.write("---\n\n")
            f.write(result.restructured_text)
        
        print(f"   ✅ Success: {sample_output.name}")
        print(f"   📏 Sample: {len(sample_text):,} → {len(result.restructured_text):,} chars")
        print()
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print()
    
    # Summary
    print("📊 Processing Summary")
    print("=" * 30)
    successful = sum(1 for r in results.values() if r.get('success'))
    total = len(results)
    
    print(f"✅ Successful: {successful}/{total} processing modes")
    
    if successful > 0:
        print()
        print("📁 Generated Files:")
        for mode, result in results.items():
            if result.get('success'):
                print(f"   • {result['output_file'].name}")
        
        print()
        print("🎯 Next Steps:")
        print("   1. Review generated files in restructured_texts/")
        print("   2. Compare original vs restructured formats")
        print("   3. Test RAG retrieval with restructured content")
        print("   4. Integrate with your existing RAG pipeline")
    
    print()
    print("✨ Philosophical Text Restructuring Test Complete!")


async def demo_processing_modes():
    """Demonstrate different processing modes with sample text."""
    
    print("\n🎭 Processing Modes Demonstration")
    print("=" * 40)
    
    # Sample Socratic dialogue text
    sample_text = """
    How you, O Athenians, have been affected by my accusers, I cannot tell; but I know that they almost made me forget who I was--so persuasively did they speak; and yet they have hardly uttered a word of truth. But of the many falsehoods told by them, there was one which quite amazed me;--I mean when they said that you should be upon your guard and not allow yourselves to be deceived by the force of my eloquence. To say this, when they were certain to be detected as soon as I opened my lips and proved myself to be anything but a great speaker, did indeed appear to me most shameless--unless by the force of eloquence they mean the force of truth; for is such is their meaning, I admit that I am eloquent. But in how different a way from theirs! Well, as I was saying, they have scarcely spoken the truth at all; but from me you shall hear the whole truth.
    """
    
    restructurer = PhilosophicalTextRestructurer()
    
    context = PhilosophicalContext(
        author="Plato",
        work_title="Apology",
        philosophical_period="Ancient",
        text_type="dialogue"
    )
    
    modes_to_test = [
        ProcessingMode.DIALOGUE_SEPARATION,
        ProcessingMode.ARGUMENT_EXTRACTION,
        ProcessingMode.ENTITY_MARKUP
    ]
    
    for mode in modes_to_test:
        print(f"\n📝 Mode: {mode.value.replace('_', ' ').title()}")
        print("-" * 30)
        
        try:
            result = await restructurer.restructure_text(
                text=sample_text,
                mode=mode,
                context=context
            )
            
            # Show first 300 chars of result
            preview = result.restructured_text[:300]
            if len(result.restructured_text) > 300:
                preview += "..."
            
            print(preview)
            print(f"\n📊 Stats: {result.processing_stats}")
            
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Run the philosophical text restructuring test."""
    
    print("Starting Philosophical Text Restructuring Test")
    print()
    
    # Run main test
    asyncio.run(test_socratic_dialogues_restructuring())
    
    # Run demo
    asyncio.run(demo_processing_modes())


if __name__ == "__main__":
    main()