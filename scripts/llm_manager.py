#!/usr/bin/env python3
"""
LLM Provider Management CLI

Simple command-line utility for managing LLM provider selection and testing.
"""

import asyncio
import argparse
import sys
import os
from typing import Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from arete.services.simple_llm_service import (
    SimpleLLMService, 
    show_provider_status, 
    set_provider_interactive,
    quick_generate
)
from arete.services.llm_provider import LLMMessage, MessageRole
from arete.config import get_settings


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LLM Provider Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python llm_manager.py status                    # Show current provider status
  python llm_manager.py set ollama                # Set provider to Ollama
  python llm_manager.py set anthropic             # Set provider to Anthropic
  python llm_manager.py set-model "gpt-4"         # Set specific model
  python llm_manager.py clear-model               # Use provider default model
  python llm_manager.py test "Hello world"        # Test active provider
  python llm_manager.py test "Hello" --provider openai  # Test specific provider
  python llm_manager.py interactive               # Interactive provider selection
  python llm_manager.py list                      # List available providers

Environment Variables:
  SELECTED_LLM_PROVIDER=ollama    # Set active provider via environment
  SELECTED_LLM_MODEL=gpt-4        # Set active model via environment
  ANTHROPIC_API_KEY=sk-...        # API keys for providers
  OPENAI_API_KEY=sk-...
  GEMINI_API_KEY=...
  OPENROUTER_API_KEY=...
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    subparsers.add_parser('status', help='Show current provider status')
    
    # Set command
    set_parser = subparsers.add_parser('set', help='Set active provider')
    set_parser.add_argument('provider', help='Provider name (ollama, openai, anthropic, gemini, openrouter)')
    
    # Set-model command
    set_model_parser = subparsers.add_parser('set-model', help='Set active model')
    set_model_parser.add_argument('model', help='Model name to use')
    
    # Clear-model command
    subparsers.add_parser('clear-model', help='Clear model selection (use provider default)')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test provider with a prompt')
    test_parser.add_argument('prompt', help='Test prompt to send')
    test_parser.add_argument('--provider', help='Specific provider to test')
    test_parser.add_argument('--model', help='Specific model to use')
    test_parser.add_argument('--temperature', type=float, default=0.7, help='Temperature (0.0-2.0)')
    test_parser.add_argument('--max-tokens', type=int, help='Maximum tokens to generate')
    
    # Interactive command
    subparsers.add_parser('interactive', help='Interactive provider selection')
    
    # List command  
    subparsers.add_parser('list', help='List available providers')
    
    # Health command
    health_parser = subparsers.add_parser('health', help='Check provider health')
    health_parser.add_argument('--provider', help='Specific provider to check')
    
    # Chat command
    chat_parser = subparsers.add_parser('chat', help='Start interactive chat session')
    chat_parser.add_argument('--provider', help='Provider to use for chat')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'status':
            show_provider_status()
            
        elif args.command == 'set':
            service = SimpleLLMService()
            service.set_provider(args.provider)
            print(f"[OK] Provider set to: {args.provider}")
            
        elif args.command == 'set-model':
            service = SimpleLLMService()
            service.set_model(args.model)
            print(f"[OK] Model set to: {args.model}")
            
        elif args.command == 'clear-model':
            service = SimpleLLMService()
            service.clear_model_selection()
            print("[OK] Model selection cleared, using provider default")
            
        elif args.command == 'test':
            asyncio.run(test_provider(args))
            
        elif args.command == 'interactive':
            set_provider_interactive()
            
        elif args.command == 'list':
            list_providers()
            
        elif args.command == 'health':
            asyncio.run(check_health(args.provider))
            
        elif args.command == 'chat':
            asyncio.run(start_chat(args.provider))
            
    except KeyboardInterrupt:
        print("\nGoodbye! Goodbye!")
    except Exception as e:
        print(f"[--] Error: {e}")
        sys.exit(1)


def list_providers():
    """List available providers with status."""
    service = SimpleLLMService()
    info = service.get_provider_info()
    
    print("LLM Available LLM Providers")
    print("=" * 40)
    
    for provider in info['available_providers']:
        configured = "[OK]" if provider in info['configured_providers'] else "[--]"
        active = "<-- ACTIVE" if provider == info['active_provider'] else ""
        print(f"  {provider:12} {configured} {active}")
    
    print("\n[OK] = Configured    [--] = Missing API key")


async def test_provider(args):
    """Test provider with a prompt."""
    print(f"Testing Testing provider: {args.provider or 'active'}")
    print(f"Prompt: Prompt: {args.prompt}")
    print("-" * 50)
    
    try:
        kwargs = {}
        if args.model:
            kwargs['model'] = args.model
        if args.temperature:
            kwargs['temperature'] = args.temperature
        if args.max_tokens:
            kwargs['max_tokens'] = args.max_tokens
        
        response = await quick_generate(
            args.prompt,
            provider=args.provider,
            **kwargs
        )
        
        print(f"LLM Response:\n{response}")
        
    except Exception as e:
        print(f"[--] Test failed: {e}")


async def check_health(provider_name: Optional[str] = None):
    """Check provider health."""
    service = SimpleLLMService()
    
    if provider_name:
        providers_to_check = [provider_name]
        print(f"Health check: Checking health: {provider_name}")
    else:
        info = service.get_provider_info()
        providers_to_check = info['configured_providers']
        print("Health check: Checking health of all configured providers")
    
    print("=" * 50)
    
    for provider in providers_to_check:
        try:
            health = service.get_provider_health(provider)
            status = health.get('status', 'unknown')
            
            if status == 'healthy':
                print(f"[OK] {provider:12}: Healthy")
            elif status == 'error':
                error = health.get('error', 'Unknown error')
                print(f"[--] {provider:12}: Error - {error}")
            else:
                print(f"[WARN]  {provider:12}: {status}")
                
        except Exception as e:
            print(f"[--] {provider:12}: Failed to check - {e}")


async def start_chat(provider_name: Optional[str] = None):
    """Start interactive chat session."""
    service = SimpleLLMService()
    
    if provider_name:
        service.set_provider(provider_name)
    
    info = service.get_provider_info()
    active_provider = info['active_provider']
    
    print(f"Chat Starting chat with {active_provider}")
    print("Type 'quit', 'exit', or Ctrl+C to end the chat")
    print("=" * 50)
    
    messages = []
    
    while True:
        try:
            user_input = input("\nYou: You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                break
            
            if not user_input:
                continue
            
            # Add user message
            messages.append(LLMMessage(role=MessageRole.USER, content=user_input))
            
            print("LLM Assistant: ", end="", flush=True)
            
            # Generate response
            response = await service.generate_response(messages)
            print(response.content)
            
            # Add assistant response to conversation
            messages.append(LLMMessage(role=MessageRole.ASSISTANT, content=response.content))
            
            # Keep conversation manageable (last 10 messages)
            if len(messages) > 10:
                messages = messages[-10:]
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n[--] Error: {e}")
            print("Continuing chat...")
    
    print("\nGoodbye! Chat ended!")


if __name__ == "__main__":
    main()