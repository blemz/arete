# Arete Development Scripts

This directory contains development, testing, and utility scripts for the Arete project.

## Testing Scripts

### `test_minimal.py`
Basic connectivity test for Neo4j and Weaviate databases. Use this to verify core components are working.

```bash
python scripts/test_minimal.py
```

### `comprehensive_prompt_test.py`
Tests enhanced prompt templates with different philosophical scenarios. Demonstrates:
- Dynamic source attribution
- Citation format instructions
- XML-structured output
- Comparative analysis restrictions

### `test_enhanced_prompt.py`
Additional prompt template testing script.

### `test_file.py`
Generic test file for development experiments.

## Database Utilities

### `clear_databases.py`
**⚠️ DANGER**: Clears all data from Neo4j and Weaviate databases. Use with extreme caution.

```bash
python scripts/clear_databases.py
```

### `check_weaviate_data.py`
Inspects Weaviate vector database content and schema.

```bash
python scripts/check_weaviate_data.py
```

### `debug_embeddings.py`
Debug embedding generation and vector operations.

## Verification Scripts

### `verify_databases.py`
Comprehensive database health check for all services (Neo4j, Weaviate, Redis).

```bash
python scripts/verify_databases.py
```

### `verify_database_content.py`
Verifies ingested content integrity and relationship accuracy.

```bash
python scripts/verify_database_content.py
```

### `verify_final.py`
Final verification script for complete system validation.

## Usage Notes

- Run scripts from the project root directory
- Ensure `.env` file is configured with proper credentials
- Most scripts require database services to be running
- Use scripts for development and debugging only, not in production

## Environment Setup

```bash
# Start required services
docker-compose up -d neo4j weaviate

# Run verification
python scripts/verify_databases.py

# Check specific components
python scripts/test_minimal.py
```