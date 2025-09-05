#!/usr/bin/env python3
"""
Arete Reflex Application Launcher

This script launches the Arete classical philosophy chat interface built with Reflex.
It includes automatic dependency checking and service initialization.
"""

import asyncio
import sys
import os
import subprocess
import logging
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_dependencies() -> bool:
    """Check if required dependencies are installed"""
    required_packages = [
        'reflex',
        'pydantic',
        'asyncio',
        'datetime'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {missing_packages}")
        logger.info("Install with: pip install -r requirements_reflex.txt")
        return False
    
    return True


def check_rag_services() -> bool:
    """Check if RAG services are configured"""
    required_paths = [
        "src/arete/services/llm_service.py",
        "src/arete/services/retrieval_service.py",
        "src/arete/services/embedding_service.py",
        "src/arete/database/weaviate_client.py",
        "src/arete/database/neo4j_client.py",
        "src/arete/core/config.py"
    ]
    
    missing_files = []
    base_path = Path(__file__).parent
    
    for path in required_paths:
        if not (base_path / path).exists():
            missing_files.append(path)
    
    if missing_files:
        logger.warning(f"Missing RAG service files: {missing_files}")
        logger.info("RAG functionality may be limited without these files")
        return False
    
    return True


def check_environment() -> bool:
    """Check environment configuration"""
    env_file = Path(__file__).parent / ".env"
    
    if not env_file.exists():
        logger.warning(".env file not found. Creating template...")
        create_env_template()
        logger.info("Please configure .env file with your API keys and settings")
        return False
    
    # Check for critical environment variables
    critical_vars = [
        'OPENAI_API_KEY',
        'NEO4J_URI', 
        'NEO4J_USER',
        'NEO4J_PASSWORD',
        'WEAVIATE_URL'
    ]
    
    missing_vars = []
    
    # Simple env file parsing
    try:
        with open(env_file, 'r') as f:
            env_content = f.read()
            for var in critical_vars:
                if f"{var}=" not in env_content:
                    missing_vars.append(var)
    except Exception as e:
        logger.error(f"Error reading .env file: {e}")
        return False
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {missing_vars}")
        logger.info("RAG functionality requires these variables to be configured")
    
    return True


def create_env_template():
    """Create a template .env file"""
    template = """# Arete Reflex Application Environment Configuration

# OpenAI Configuration (for embeddings and LLM)
OPENAI_API_KEY=your_openai_api_key_here
EMBEDDING_PROVIDER=openai

# Neo4j Database Configuration (for knowledge graph)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=neo4j

# Weaviate Vector Database Configuration
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=

# LLM Provider Configuration
KG_LLM_PROVIDER=openai  # Options: openai, openrouter, gemini, anthropic, ollama

# Application Settings
DEBUG=true
LOG_LEVEL=INFO

# Optional: Additional Provider Keys
OPENROUTER_API_KEY=
GEMINI_API_KEY=
ANTHROPIC_API_KEY=

# Performance Settings
MAX_RETRIEVAL_CHUNKS=5
SIMILARITY_THRESHOLD=0.7
MAX_CONTEXT_MESSAGES=10
"""
    
    env_file = Path(__file__).parent / ".env"
    with open(env_file, 'w') as f:
        f.write(template)


def initialize_reflex():
    """Initialize Reflex application"""
    logger.info("Initializing Reflex application...")
    
    try:
        # Change to application directory
        app_dir = Path(__file__).parent
        os.chdir(app_dir)
        
        # Initialize Reflex if needed
        if not (app_dir / ".web").exists():
            logger.info("First time setup - initializing Reflex...")
            subprocess.run([sys.executable, "-m", "reflex", "init"], check=True)
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to initialize Reflex: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during initialization: {e}")
        return False


def start_reflex_dev():
    """Start Reflex development server"""
    logger.info("Starting Reflex development server...")
    logger.info("Access the application at: http://localhost:3000/chat")
    
    try:
        # Start Reflex development server
        subprocess.run([sys.executable, "-m", "reflex", "run"], check=True)
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start Reflex server: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False
    
    return True


def main():
    """Main launcher function"""
    logger.info("=" * 60)
    logger.info("🏛️  ARETE - Classical Philosophy Chat Interface")
    logger.info("   Reflex-based RAG Chat System")
    logger.info("=" * 60)
    
    # Pre-flight checks
    logger.info("Running pre-flight checks...")
    
    if not check_dependencies():
        logger.error("❌ Dependency check failed")
        sys.exit(1)
    
    logger.info("✅ Dependencies OK")
    
    rag_services_ok = check_rag_services()
    if rag_services_ok:
        logger.info("✅ RAG services configured")
    else:
        logger.warning("⚠️  RAG services partially configured")
    
    env_ok = check_environment()
    if env_ok:
        logger.info("✅ Environment configured")
    else:
        logger.warning("⚠️  Environment needs configuration")
        logger.info("You can still run the interface, but RAG functionality may be limited")
    
    # Initialize Reflex
    if not initialize_reflex():
        logger.error("❌ Failed to initialize Reflex")
        sys.exit(1)
    
    logger.info("✅ Reflex initialized")
    
    # Launch application
    logger.info("\n🚀 Launching Arete Chat Interface...")
    logger.info("Features available:")
    logger.info("  • Interactive chat with classical philosophy AI")
    logger.info("  • Real-time citation display from ancient texts")
    if rag_services_ok and env_ok:
        logger.info("  • Full RAG pipeline with Neo4j knowledge graph")
        logger.info("  • Vector similarity search via Weaviate")
        logger.info("  • Multi-provider LLM integration")
    logger.info("  • Conversation export and management")
    logger.info("  • Performance monitoring and analytics")
    logger.info("")
    logger.info("Navigation:")
    logger.info("  • Main Interface: http://localhost:3000/chat")
    logger.info("  • Settings: http://localhost:3000/chat/settings")
    logger.info("  • Landing Page: http://localhost:3000/")
    logger.info("")
    
    if not start_reflex_dev():
        logger.error("❌ Failed to start application")
        sys.exit(1)
    
    logger.info("Application finished")


if __name__ == "__main__":
    main()