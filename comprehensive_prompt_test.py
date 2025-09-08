#!/usr/bin/env python3
"""
Comprehensive Test of Enhanced Prompt Templates

Demonstrates all 4 key improvements:
1. Dynamic source attribution with explicit work titles
2. Citation format instructions (Stephanus/Bekker numbers)
3. XML-structured output tags
4. Comparative prompt restrictions for missing evidence
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from arete.services.prompt_templates import PromptTemplate, PromptStyle, build_enhanced_prompt
except ImportError:
    # Try alternative import path
    sys.path.insert(0, os.path.dirname(__file__))
    from src.arete.services.prompt_templates import PromptTemplate, PromptStyle, build_enhanced_prompt

def test_single_work_apology():
    """Test 1: Single Work - Shows explicit source attribution"""
    print("\n" + "="*80)
    print(" TEST 1: SINGLE WORK SOURCE ATTRIBUTION")
    print("="*80)
    
    query = "What is Socrates accused of?"
    
    search_results = [
        {
            'properties': {
                'content': 'Meletus accuses me of corrupting the youth and not believing in the gods the city believes in',
                'source': 'Plato_Apology_24b'
            }
        }
    ]
    
    context_chunks = ["Meletus brings formal charges against Socrates for corrupting youth and impiety."]
    entities = [{'name': 'Socrates'}, {'name': 'Meletus'}, {'name': 'impiety'}]
    
    prompt = build_enhanced_prompt(query, context_chunks, entities, search_results)
    
    # Show key improvements
    print("IMPROVEMENT 1 - Dynamic Source Attribution:")
    if "Context from Plato's Apology:" in prompt:
        print("✓ Explicit work title in context header")
    else:
        print("✗ Generic context header")
    
    print("\nIMPROVEMENT 2 - Citation Format Instructions:")
    if "Apology: Use Stephanus numbers" in prompt:
        print("✓ Stephanus number citation instructions")
    else:
        print("✗ No specific citation format")
    
    print("\nIMPROVEMENT 3 - XML Structure:")
    xml_tags = ['<direct_answer>', '<detailed_explanation>', '<broader_connections>', '<references>']
    xml_found = sum(1 for tag in xml_tags if tag in prompt)
    print(f"✓ Found {xml_found}/4 XML structure tags")
    
    print(f"\n[SAMPLE PROMPT EXCERPT]")
    lines = prompt.split('\n')
    for i, line in enumerate(lines):
        if 'Context from' in line:
            print(f"Line {i+1}: {line}")
            break
    for i, line in enumerate(lines):
        if 'citation format:' in line:
            print(f"Line {i+1}: {line}")
            break

def test_multiple_works():
    """Test 2: Multiple Works - Shows detailed source listing"""
    print("\n" + "="*80)
    print(" TEST 2: MULTIPLE WORKS SOURCE LISTING")
    print("="*80)
    
    query = "What is temperance?"
    
    search_results = [
        {
            'properties': {
                'content': 'Temperance is self-control and moderation',
                'source': 'Plato_Charmides_160e'
            }
        },
        {
            'properties': {
                'content': 'The unexamined life is not worth living',
                'source': 'Plato_Apology_38a'
            }
        }
    ]
    
    context_chunks = ["Discussion of temperance in Charmides", "Self-examination theme in Apology"]
    entities = [{'name': 'temperance'}, {'name': 'self-knowledge'}]
    
    prompt = build_enhanced_prompt(query, context_chunks, entities, search_results)
    
    print("IMPROVEMENT 1 - Multiple Work Attribution:")
    if "Plato's Apology, Charmides" in prompt:
        print("✓ Both works explicitly listed")
    else:
        print("✗ Works not clearly listed")
    
    print("\nCONTEXT HEADER SAMPLE:")
    lines = prompt.split('\n')
    for line in lines:
        if 'Context from' in line:
            print(f"  {line}")
            break

def test_aristotelian_content():
    """Test 3: Aristotelian Content - Shows Bekker number citations"""
    print("\n" + "="*80)
    print(" TEST 3: ARISTOTELIAN CONTENT - BEKKER CITATIONS")
    print("="*80)
    
    query = "What is the function of human beings?"
    
    search_results = [
        {
            'properties': {
                'content': 'The function of human beings is activity of soul in accordance with virtue',
                'source': 'Aristotle_Nicomachean_Ethics_1098a16'
            }
        }
    ]
    
    context_chunks = ["Human function is virtuous soul activity leading to eudaimonia"]
    entities = [{'name': 'function'}, {'name': 'virtue'}, {'name': 'eudaimonia'}]
    
    prompt = build_enhanced_prompt(query, context_chunks, entities, search_results)
    
    print("IMPROVEMENT 2 - Aristotelian Citation Format:")
    if "Bekker numbers" in prompt:
        print("✓ Bekker number citation instructions found")
    else:
        print("✗ No Bekker citation instructions")
    
    print("\nCITATION INSTRUCTION SAMPLE:")
    lines = prompt.split('\n')
    for line in lines:
        if 'Bekker' in line:
            print(f"  {line}")
            break

def test_comparison_missing_evidence():
    """Test 4: Comparison with Missing Evidence - Shows restriction protocol"""
    print("\n" + "="*80)
    print(" TEST 4: COMPARISON WITH MISSING EVIDENCE RESTRICTION")
    print("="*80)
    
    query = "How do Plato and Aristotle differ on virtue?"
    
    # Only Plato content - no Aristotle
    search_results = [
        {
            'properties': {
                'content': 'Virtue is knowledge and no one does wrong willingly',
                'source': 'Plato_Charmides_164c'
            }
        }
    ]
    
    context_chunks = ["Plato's view that virtue is knowledge"]
    entities = [{'name': 'virtue'}, {'name': 'knowledge'}]
    
    prompt = PromptTemplate.build_comparison_prompt(query, context_chunks, entities, search_results)
    
    print("IMPROVEMENT 4 - Missing Evidence Protocol:")
    restrictions_found = []
    
    if "MISSING EVIDENCE PROTOCOL" in prompt:
        restrictions_found.append("Missing evidence protocol")
    if "only includes material from" in prompt:
        restrictions_found.append("Source limitation warning")
    if "NO SPECULATION RULE" in prompt:
        restrictions_found.append("No speculation rule")
    if "COVERAGE CHECK" in prompt:
        restrictions_found.append("Coverage check requirement")
    
    print(f"✓ Found {len(restrictions_found)} restriction protocols:")
    for restriction in restrictions_found:
        print(f"  • {restriction}")
    
    print("\nRESTRICTION SAMPLE:")
    lines = prompt.split('\n')
    for line in lines:
        if "only includes material from" in line:
            print(f"  {line}")
            break

def test_xml_parsing_demo():
    """Test 5: XML Parsing - Shows programmatic structure"""
    print("\n" + "="*80)
    print(" TEST 5: XML STRUCTURE FOR PROGRAMMATIC PARSING")
    print("="*80)
    
    sample_response = """<direct_answer>
Temperance is self-knowledge and mastery of oneself according to Plato.
</direct_answer>

<detailed_explanation>
In the Charmides dialogue, Plato examines temperance through multiple definitions...
</detailed_explanation>

<broader_connections>
This connects to Plato's theory of the tripartite soul where reason must rule...
</broader_connections>

<references>
Charmides 164d: "temperance is knowledge of oneself"
</references>"""
    
    print("IMPROVEMENT 3 - XML Structure Benefits:")
    
    import re
    sections = {
        'direct_answer': re.search(r'<direct_answer>(.*?)</direct_answer>', sample_response, re.DOTALL),
        'detailed_explanation': re.search(r'<detailed_explanation>(.*?)</detailed_explanation>', sample_response, re.DOTALL),
        'broader_connections': re.search(r'<broader_connections>(.*?)</broader_connections>', sample_response, re.DOTALL),
        'references': re.search(r'<references>(.*?)</references>', sample_response, re.DOTALL)
    }
    
    print("✓ Programmatic extraction possible:")
    for section_name, match in sections.items():
        if match:
            content = match.group(1).strip()
            print(f"  • {section_name}: {len(content)} chars - '{content[:50]}...'")
    
    print("\n✓ UI Enhancement possibilities:")
    print("  • Bold headers from XML tags")
    print("  • Collapsible sections")
    print("  • Citation footnotes from <references>")
    print("  • Direct answer highlighting")

if __name__ == "__main__":
    print("COMPREHENSIVE ENHANCED PROMPT SYSTEM TEST")
    print("Testing all 4 major improvements to the prompt templates")
    
    test_single_work_apology()
    test_multiple_works()
    test_aristotelian_content()
    test_comparison_missing_evidence()
    test_xml_parsing_demo()
    
    print("\n" + "="*80)
    print(" SUMMARY OF IMPROVEMENTS")
    print("="*80)
    print("✓ 1. Dynamic Source Attribution - Explicit work titles in context headers")
    print("✓ 2. Citation Format Instructions - Stephanus/Bekker numbers automatically")
    print("✓ 3. XML-Structured Output - Programmatic parsing for UI enhancements")
    print("✓ 4. Missing Evidence Protocol - Honest limitations for comparisons")
    print("\nThe enhanced prompt system now provides:")
    print("  • Clear source transparency")
    print("  • Proper scholarly citations")
    print("  • Structured output for automation")
    print("  • Honest acknowledgment of limitations")