# Simple LLM Service - User-Controlled Provider Selection

The SimpleLLMService provides direct, user-controlled access to multiple LLM providers without the complexity of intelligent routing. Perfect for development and testing.

## 🎯 **How It Works**

Instead of automatic provider selection, YOU choose which LLM provider to use via:
1. **Environment Variable**: `SELECTED_LLM_PROVIDER=anthropic`
2. **Direct Method Calls**: `service.generate_response(messages, provider="openai")`
3. **CLI Commands**: `python scripts/llm_manager.py set gemini`

## 🚀 **Quick Start**

### 1. Set Your Preferred Provider

```bash
# Option 1: Environment Variable (recommended)
export SELECTED_LLM_PROVIDER=ollama  # Linux/Mac
set SELECTED_LLM_PROVIDER=ollama     # Windows

# Option 2: CLI Command
python scripts/llm_manager.py set ollama
python scripts/llm_manager.py set-model "llama2"

# Option 3: In Code
from arete.services.simple_llm_service import SimpleLLMService
service = SimpleLLMService()
service.set_provider("ollama")
service.set_model("llama2")
```

### 2. Configure API Keys (if needed)

```bash
# Only needed for cloud providers (Ollama runs locally)
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export GEMINI_API_KEY="..."
export OPENROUTER_API_KEY="..."
```

### 3. Use the Service

```python
from arete.services.simple_llm_service import quick_generate

# Simple text generation
response = await quick_generate("What is philosophy?")
print(response)

# Or with specific provider
response = await quick_generate("Explain virtue ethics", provider="anthropic")
print(response)
```

## 📋 **CLI Commands**

```bash
# Check current status
python scripts/llm_manager.py status

# List all providers
python scripts/llm_manager.py list

# Set active provider
python scripts/llm_manager.py set ollama
python scripts/llm_manager.py set anthropic
python scripts/llm_manager.py set openai

# Set active model
python scripts/llm_manager.py set-model "llama2"
python scripts/llm_manager.py set-model "gpt-4"
python scripts/llm_manager.py clear-model

# Test a provider
python scripts/llm_manager.py test "Hello world"
python scripts/llm_manager.py test "Explain Aristotle" --provider anthropic

# Check provider health
python scripts/llm_manager.py health
python scripts/llm_manager.py health --provider openai

# Interactive chat
python scripts/llm_manager.py chat
python scripts/llm_manager.py chat --provider gemini
```

## 🔧 **Available Providers**

| Provider | Local/Cloud | API Key Required | Best For |
|----------|-------------|------------------|----------|
| **ollama** | Local | No | Free, fast, private |
| **anthropic** | Cloud | Yes | Philosophy, education |
| **openai** | Cloud | Yes | General purpose |
| **gemini** | Cloud | Yes | Competitive pricing |
| **openrouter** | Cloud | Yes | Multiple models |

## 💻 **Code Examples**

### Basic Usage
```python
from arete.services.simple_llm_service import SimpleLLMService, quick_generate
from arete.services.llm_provider import LLMMessage, MessageRole

# Quick generation
response_text = await quick_generate("What is eudaimonia?")

# Full service usage
service = SimpleLLMService()

# Create conversation
messages = [
    LLMMessage(role=MessageRole.SYSTEM, content="You are a philosophy tutor."),
    LLMMessage(role=MessageRole.USER, content="Explain Aristotelian virtue ethics.")
]

# Generate with active provider
response = await service.generate_response(messages)

# Generate with specific provider
response = await service.generate_response(
    messages, 
    provider="anthropic",
    temperature=0.7,
    max_tokens=1000
)

print(response.content)
print(f"Used: {response.provider}")
print(f"Tokens: {response.usage_tokens}")
```

### Provider Management
```python
from arete.services.simple_llm_service import SimpleLLMService

service = SimpleLLMService()

# Check what's configured
info = service.get_provider_info()
print(f"Active: {info['active_provider']}")
print(f"Configured: {info['configured_providers']}")

# Set provider
service.set_provider("anthropic")

# Check health
health = service.get_provider_health("anthropic")
print(f"Status: {health['status']}")
```

## 🎛️ **Priority Order**

The service selects providers and models in this priority order:

**Provider Selection:**
1. **Environment Variable**: `SELECTED_LLM_PROVIDER`
2. **Settings Selection**: `selected_llm_provider` in config
3. **Default Setting**: `default_llm_provider` in config (usually "ollama")

**Model Selection:**
1. **Environment Variable**: `SELECTED_LLM_MODEL`
2. **Settings Selection**: `selected_llm_model` in config
3. **Provider Default**: Let the provider choose its default model

## 🔍 **Provider Status Check**

```bash
python scripts/llm_manager.py status
```

Output:
```
LLM Provider Status
==================================================
Active Provider: anthropic
Active Model: claude-3-sonnet
Available Providers: ollama, openrouter, gemini, anthropic, openai
Configured Providers: ollama, anthropic

Provider Configuration Source:
  Environment Variable: anthropic
  Settings Selected: Not set
  Settings Default: ollama

Model Configuration Source:
  Environment Variable: claude-3-sonnet
  Settings Selected: Not set
```

## ⚙️ **Environment Variables**

```bash
# Provider and Model Selection
SELECTED_LLM_PROVIDER=ollama        # Active provider
SELECTED_LLM_MODEL=llama2           # Active model

# API Keys
ANTHROPIC_API_KEY=sk-ant-...        # Anthropic Claude
OPENAI_API_KEY=sk-...               # OpenAI GPT
GEMINI_API_KEY=...                  # Google Gemini
OPENROUTER_API_KEY=...              # OpenRouter

# Optional Settings
LLM_MAX_TOKENS=4000                 # Max response length
LLM_TEMPERATURE=0.7                 # Creativity level
LLM_TIMEOUT=30                      # Request timeout
```

## 🏃‍♂️ **Quick Test**

```bash
# 1. Set provider to free local Ollama
python scripts/llm_manager.py set ollama

# 2. Check status
python scripts/llm_manager.py status

# 3. Test it
python scripts/llm_manager.py test "What is 2+2?"

# 4. Start chat (optional)
python scripts/llm_manager.py chat
```

## 🔄 **Switching Providers**

```bash
# Switch to different providers for different tasks
python scripts/llm_manager.py set ollama      # For quick/free queries
python scripts/llm_manager.py set anthropic   # For philosophy questions
python scripts/llm_manager.py set openai      # For complex analysis
```

## 🆚 **vs. Intelligent Router**

| Feature | SimpleLLMService | IntelligentRouter |
|---------|------------------|-------------------|
| Control | **User chooses** | AI chooses |
| Complexity | Simple | Advanced |
| Use Case | Development, Testing | Production |
| Provider Selection | Manual | Automatic |
| Cost Optimization | Manual | Automatic |
| Failover | None | Automatic |

## 🎓 **Philosophy Tutoring Example**

```python
# Set best provider for education
service.set_provider("anthropic")  # Best for philosophical accuracy

messages = [
    LLMMessage(role=MessageRole.SYSTEM, content="""
    You are a philosophy tutor. Provide accurate, well-sourced explanations 
    of philosophical concepts suitable for university students.
    """),
    LLMMessage(role=MessageRole.USER, content="Explain the difference between Plato's and Aristotle's views on virtue.")
]

response = await service.generate_response(messages, temperature=0.3)  # Lower temp for accuracy
print(response.content)
```

This gives you full control over which LLM provider handles your philosophical tutoring queries!

---

**Perfect for**: Development, testing, specific provider requirements, cost control, API experimentation
**Ready for**: Immediate use with any of the 5 supported LLM providers