#!/usr/bin/env python3
"""
Simple LLM Service Demo

Demonstrates user-controlled LLM provider selection for the Arete system.
"""

import asyncio
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from arete.services.simple_llm_service import (
    SimpleLLMService,
    quick_generate,
    show_provider_status
)
from arete.services.llm_provider import LLMMessage, MessageRole
from arete.config import get_settings


async def demo_basic_usage():
    """Demonstrate basic LLM usage."""
    print("\n" + "="*60)
    print("DEMO DEMO 1: Basic Usage")
    print("="*60)
    
    # Simple text generation
    print("Generating Generating response with default provider...")
    try:
        response = await quick_generate(
            "What is philosophy in one sentence?",
            temperature=0.7,
            max_tokens=100
        )
        print(f"Response: {response}")
    except Exception as e:
        print(f"ERROR: Error: {e}")


async def demo_provider_selection():
    """Demonstrate provider selection."""
    print("\n" + "="*60)
    print("DEMO DEMO 2: Provider Selection")
    print("="*60)
    
    service = SimpleLLMService()
    
    # Show current status
    print("Current provider configuration:")
    info = service.get_provider_info()
    print(f"  Active: {info['active_provider']}")
    print(f"  Configured: {', '.join(info['configured_providers'])}")
    print()
    
    # Try different providers
    providers_to_try = ["ollama", "anthropic", "openai"]
    
    for provider in providers_to_try:
        print(f"Testing Testing {provider}...")
        try:
            response = await quick_generate(
                f"Say hello from {provider}!",
                provider=provider,
                max_tokens=50
            )
            print(f"  [OK] {provider}: {response[:50]}...")
        except Exception as e:
            print(f"  ERROR: {provider}: {e}")


async def demo_philosophical_conversation():
    """Demonstrate philosophical tutoring scenario."""
    print("\n" + "="*60)
    print("DEMO DEMO 3: Philosophy Tutoring")
    print("="*60)
    
    service = SimpleLLMService()
    
    # Set up philosophical conversation
    messages = [
        LLMMessage(
            role=MessageRole.SYSTEM, 
            content="""You are a philosophy tutor specializing in ancient Greek philosophy. 
            Provide clear, educational explanations suitable for university students."""
        ),
        LLMMessage(
            role=MessageRole.USER,
            content="Can you briefly explain what Aristotle meant by 'eudaimonia' and how it differs from modern concepts of happiness?"
        )
    ]
    
    # Try with different providers to show differences
    preferred_providers = ["anthropic", "openai", "ollama"]
    
    for provider in preferred_providers:
        print(f"\nResponse from Response from {provider.upper()}:")
        print("-" * 40)
        
        try:
            response = await service.generate_response(
                messages,
                provider=provider,
                temperature=0.3,  # Lower temperature for educational accuracy
                max_tokens=200
            )
            
            print(response.content)
            print(f"\nMetadata: Metadata: {response.usage_tokens} tokens, provider: {response.provider}")
            
        except Exception as e:
            print(f"ERROR: Error with {provider}: {e}")


async def demo_environment_control():
    """Demonstrate environment variable control."""
    print("\n" + "="*60)
    print("DEMO DEMO 4: Environment Control")
    print("="*60)
    
    print("Current environment settings:")
    print(f"  SELECTED_LLM_PROVIDER: {os.getenv('SELECTED_LLM_PROVIDER', 'Not set')}")
    print(f"  SELECTED_LLM_MODEL: {os.getenv('SELECTED_LLM_MODEL', 'Not set')}")
    
    # Show how to change provider and model via environment
    print("\nSetting provider and model via environment variables...")
    os.environ["SELECTED_LLM_PROVIDER"] = "ollama"
    os.environ["SELECTED_LLM_MODEL"] = "llama2"
    
    service = SimpleLLMService()
    active_provider = service.get_active_provider_name()
    active_model = service.get_active_model_name()
    print(f"[OK] Active provider is now: {active_provider}")
    print(f"[OK] Active model is now: {active_model}")
    
    # Test the change
    try:
        response = await quick_generate("Hello from environment-controlled provider and model!")
        print(f"Response: {response[:100]}...")
    except Exception as e:
        print(f"ERROR: Error: {e}")


async def demo_provider_comparison():
    """Compare responses from different providers."""
    print("\n" + "="*60)
    print("DEMO DEMO 5: Provider Comparison")
    print("="*60)
    
    prompt = "What is virtue according to Aristotle?"
    providers = ["ollama", "anthropic", "openai"]
    
    print(f"Generating Comparing responses to: '{prompt}'\n")
    
    for provider in providers:
        print(f"- {provider.upper()}:")
        try:
            response = await quick_generate(
                prompt,
                provider=provider,
                temperature=0.5,
                max_tokens=150
            )
            
            # Truncate for comparison
            truncated = response[:200] + "..." if len(response) > 200 else response
            print(f"   {truncated}")
            
        except Exception as e:
            print(f"   ERROR: Error: {e}")
        
        print()


def demo_cli_usage():
    """Show CLI command examples."""
    print("\n" + "="*60)
    print("DEMO DEMO 6: CLI Usage Examples")
    print("="*60)
    
    cli_examples = [
        ("Check Status", "python scripts/llm_manager.py status"),
        ("Set Provider", "python scripts/llm_manager.py set anthropic"),
        ("List Providers", "python scripts/llm_manager.py list"),
        ("Test Provider", 'python scripts/llm_manager.py test "Hello world"'),
        ("Health Check", "python scripts/llm_manager.py health"),
        ("Start Chat", "python scripts/llm_manager.py chat --provider ollama")
    ]
    
    print("Available CLI commands:\n")
    for name, command in cli_examples:
        print(f"  {name:<15}: {command}")


async def main():
    """Run all demos."""
    print("Simple LLM Service Demonstration Simple LLM Service Demonstration")
    print("This demo shows user-controlled LLM provider selection")
    
    # Show initial status
    print("\n📊 Initial System Status:")
    show_provider_status()
    
    # Run async demos
    await demo_basic_usage()
    await demo_provider_selection()
    await demo_philosophical_conversation()
    await demo_environment_control()
    await demo_provider_comparison()
    
    # Show CLI examples
    demo_cli_usage()
    
    print("\n" + "="*60)
    print("[OK] Demo Complete!")
    print("="*60)
    print("Key takeaways:")
    print("1. You control which LLM provider to use")
    print("2. Set via environment variable or method calls") 
    print("3. Each provider has different strengths")
    print("4. Perfect for development and testing")
    print("5. CLI tools make it easy to manage")
    
    print(f"\nSee See SIMPLE_LLM_USAGE.md for complete documentation")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDemo interrupted. Goodbye! Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\nERROR: Demo error: {e}")
        import traceback
        traceback.print_exc()