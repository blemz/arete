---
description: Aggressively fix Python code quality issues (mypy, ruff, black)
allowed-tools: Bash(*), Edit(*), View(*)
argument-hint: [optional: path]
---

# Python Code Quality - Aggressive Mode

Fix all Python code quality issues automatically and aggressively.

## Tools Used
- **ruff check --fix**: Auto-fix linting issues
- **ruff format**: Format code (replaces black)
- **mypy**: Type checking with fixes where possible

## Process

### 1. Format First
```bash
# Format all Python files
ruff format ${ARGUMENTS:-.}
```

### 2. Auto-Fix Linting Issues
```bash
# Fix all auto-fixable issues
ruff check --fix ${ARGUMENTS:-.}

# Show remaining issues
ruff check ${ARGUMENTS:-.}
```

### 3. Type Checking
```bash
# Run mypy
mypy ${ARGUMENTS:-.}
```

For mypy errors:
- Add missing type hints
- Fix type inconsistencies
- Add `# type: ignore[specific-error]` only as last resort with explanation

### 4. Final Verification
```bash
# Verify no issues remain
ruff check ${ARGUMENTS:-.}
ruff format --check ${ARGUMENTS:-.}
mypy ${ARGUMENTS:-.}

# Run tests if they exist
python -m pytest 2>/dev/null || python -m unittest discover 2>/dev/null || echo "No tests found"
```

## Configuration Priority

Use existing configurations if found:
1. `pyproject.toml` (preferred)
2. `ruff.toml`
3. `.ruff.toml`
4. `mypy.ini`

If no configuration exists, use sensible defaults:
- Line length: 100
- Target Python version: 3.8+
- Enable all safe auto-fixes

## Safety Notes

This is **aggressive mode** - it will:
- ✅ Automatically format all code
- ✅ Fix all auto-fixable linting issues
- ✅ Add missing imports from common sources
- ⚠️ May change code appearance significantly

It will **NOT**:
- ❌ Change business logic
- ❌ Modify algorithms
- ❌ Break API contracts

Target: **${ARGUMENTS:-.}**
