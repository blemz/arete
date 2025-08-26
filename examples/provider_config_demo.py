#!/usr/bin/env python3
"""
Provider Configuration Management Demo

Demonstrates the advanced provider configuration management capabilities
introduced in Phase 4.4 of the Arete Graph-RAG system.

Features demonstrated:
- Provider configuration creation and management
- Health monitoring and status tracking
- Configuration validation
- Backup and restore functionality
- Environment integration
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from arete.services.provider_config_service import (
    ProviderConfigurationService,
    ProviderStatus
)
from arete.services.simple_llm_service import SimpleLLMService
from arete.config import Settings


async def main():
    """Demonstrate provider configuration management features."""
    
    print("Arete Phase 4.4: Provider Configuration Management Demo")
    print("=" * 60)
    
    # Create temporary directory for demo
    demo_dir = Path.home() / ".arete_demo"
    demo_dir.mkdir(exist_ok=True)
    
    try:
        # Initialize services
        settings = Settings()
        config_service = ProviderConfigurationService(settings, demo_dir)
        llm_service = SimpleLLMService(settings)
        
        print("\n1. Creating Provider Configurations")
        print("-" * 40)
        
        # Configure Ollama (local)
        config_service.create_configuration(
            "ollama",
            enabled=True,
            base_url="http://localhost:11434",
            timeout=30,
            tags=["local", "fast"],
            metadata={"description": "Local Ollama instance"}
        )
        print("[OK] Configured Ollama (local)")
        
        # Configure Anthropic (with fake API key for demo)
        config_service.create_configuration(
            "anthropic",
            api_key="sk-demo-key-12345",
            enabled=True,
            timeout=45,
            max_retries=3,
            tags=["cloud", "premium"],
            metadata={"description": "Anthropic Claude API"}
        )
        print("[OK] Configured Anthropic")
        
        # Configure disabled provider
        config_service.create_configuration(
            "openai",
            api_key="sk-demo-openai-67890",
            enabled=False,
            timeout=30,
            tags=["cloud", "disabled"]
        )
        print("[OK] Configured OpenAI (disabled)")
        
        print("\n2. Configuration Overview")
        print("-" * 40)
        
        configurations = config_service.list_configurations()
        for config in configurations:
            status = "[ENABLED]" if config.enabled else "[DISABLED]"
            api_key_status = "[API-KEY]" if config.api_key else "[NO-KEY]"
            print(f"{config.provider.upper()}: {status} {api_key_status}")
            print(f"  Timeout: {config.timeout}s, Retries: {config.max_retries}")
            print(f"  Tags: {', '.join(config.tags) if config.tags else 'None'}")
            print()
        
        print("3. Configuration Validation")
        print("-" * 40)
        
        for provider in ["ollama", "anthropic", "openai"]:
            errors = config_service.validate_configuration(provider)
            if errors:
                print(f"[ERROR] {provider.upper()}: {', '.join(errors)}")
            else:
                print(f"[OK] {provider.upper()}: Valid configuration")
        
        print("\n4. Health Monitoring")
        print("-" * 40)
        
        # Check health of all providers
        for provider in ["ollama", "anthropic", "openai"]:
            try:
                health = await config_service.check_provider_health(provider)
                status_symbol = {
                    ProviderStatus.HEALTHY: "[HEALTHY]",
                    ProviderStatus.UNAVAILABLE: "[UNAVAILABLE]", 
                    ProviderStatus.UNCONFIGURED: "[UNCONFIGURED]",
                    ProviderStatus.AUTHENTICATON_FAILED: "[AUTH-FAILED]"
                }.get(health.status, "[UNKNOWN]")
                
                print(f"{status_symbol} {provider.upper()}: {health.status.value}")
                if health.error_message:
                    print(f"  Error: {health.error_message}")
                if health.response_time:
                    print(f"  Response Time: {health.response_time:.3f}s")
                    
            except Exception as e:
                print(f"[ERROR] {provider.upper()}: Health check failed - {e}")
        
        print("\n5. Provider Switching")
        print("-" * 40)
        
        # Set active provider
        config_service.set_active_provider("ollama")
        print("[OK] Set active provider to Ollama")
        
        # Show current provider status via LLM service
        info = llm_service.get_provider_info()
        print(f"Active Provider: {info['active_provider']}")
        print(f"Available Providers: {', '.join(info['available_providers'])}")
        print(f"Configured Providers: {', '.join(info['configured_providers'])}")
        
        print("\n6. Backup & Restore")
        print("-" * 40)
        
        # Create backup
        backup_path = config_service.create_backup("demo_backup")
        print(f"[OK] Created backup: {backup_path.name}")
        
        # List backups
        backups = config_service.list_backups()
        print(f"Available backups: {len(backups)}")
        for backup_file, timestamp in backups[:3]:  # Show first 3
            print(f"  - {backup_file.name} ({timestamp.strftime('%Y-%m-%d %H:%M')})")
        
        # Test validation with all configurations
        print("\n7. Comprehensive Validation")
        print("-" * 40)
        
        validation_results = config_service.validate_all_configurations()
        if validation_results:
            print("[ERROR] Configuration issues found:")
            for provider, errors in validation_results.items():
                print(f"  {provider}: {', '.join(errors)}")
        else:
            print("[OK] All configurations are valid!")
        
        # Environment integration
        print("\n8. Environment Integration")
        print("-" * 40)
        
        # Sync with environment variables
        os.environ["ANTHROPIC_API_KEY"] = "sk-updated-key-99999"
        config_service.sync_with_environment()
        print("[OK] Synchronized with environment variables")
        
        # Check updated configuration
        updated_config = config_service.get_configuration("anthropic")
        if updated_config and updated_config.api_key == "sk-updated-key-99999":
            print("[OK] Configuration updated from environment")
        
        print("\n9. Health Summary")
        print("-" * 40)
        
        healthy_providers = config_service.get_healthy_providers()
        enabled_providers = config_service.get_enabled_providers()
        
        print(f"Healthy providers: {len(healthy_providers)}")
        print(f"Enabled providers: {len(enabled_providers)}")
        print(f"Total configured: {len(configurations)}")
        
        print("\nDemo Complete!")
        print("=" * 60)
        print("Phase 4.4 Provider Configuration Management Features:")
        print("[OK] Advanced configuration management with validation")
        print("[OK] Real-time health monitoring and status tracking")
        print("[OK] Backup and restore with automatic cleanup")
        print("[OK] Environment variable synchronization")
        print("[OK] Provider switching and selection management")
        print("[OK] Comprehensive CLI tools for operations")
        
    except Exception as e:
        print(f"[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        try:
            config_service.cleanup()
            # Remove demo directory
            import shutil
            shutil.rmtree(demo_dir, ignore_errors=True)
            print("\nDemo cleanup complete")
        except Exception as e:
            print(f"[WARNING] Cleanup warning: {e}")


if __name__ == "__main__":
    asyncio.run(main())