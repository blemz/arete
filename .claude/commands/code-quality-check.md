---
description: Run comprehensive code quality checks WITHOUT making any changes (report only)
allowed-tools: Bash(*), View(*)
argument-hint: [optional: path]
---

# Code Quality Check (Report Only)

Run all static analysis tools and generate a comprehensive report without making any changes to the code.

## Analysis Only - No Modifications

This command will:
- ✅ Run all available linting and formatting checks
- ✅ Generate detailed reports of all issues
- ✅ Categorize issues by severity
- ✅ Suggest fixes but NOT apply them
- ❌ NOT modify any files

## Process

### 1. Detect Project Type
```bash
# Detect languages in use
echo "Detecting project type..."
```

### 2. Run Python Checks (if applicable)
```bash
if [ -f "pyproject.toml" ] || [ -f "setup.py" ] || [ -n "$(find . -maxdepth 2 -name '*.py' -print -quit)" ]; then
    echo "=== PYTHON ANALYSIS ==="
    
    # Ruff check
    ruff check ${ARGUMENTS:-.} || true
    
    # Mypy
    mypy ${ARGUMENTS:-.} || true
    
    # Black check
    black --check ${ARGUMENTS:-.} || true
fi
```

### 3. Run JavaScript/TypeScript Checks (if applicable)
```bash
if [ -f "package.json" ] || [ -f "tsconfig.json" ]; then
    echo "=== JAVASCRIPT/TYPESCRIPT ANALYSIS ==="
    
    # ESLint
    npx eslint ${ARGUMENTS:-.} || true
    
    # Prettier check
    npx prettier --check ${ARGUMENTS:-.} || true
    
    # TypeScript check
    if [ -f "tsconfig.json" ]; then
        npx tsc --noEmit || true
    fi
fi
```

### 4. Run Other Language Checks
```bash
# Go
if [ -f "go.mod" ]; then
    echo "=== GO ANALYSIS ==="
    gofmt -l ${ARGUMENTS:-.} || true
    go vet ${ARGUMENTS:-.} || true
    golangci-lint run ${ARGUMENTS:-.} || true
fi

# Rust
if [ -f "Cargo.toml" ]; then
    echo "=== RUST ANALYSIS ==="
    cargo fmt --check || true
    cargo clippy -- -D warnings || true
fi
```

### 5. Generate Summary Report

After running all checks, create a summary with:

#### Issue Categories
1. **Critical** (Errors that will cause runtime failures)
   - Type errors
   - Syntax errors
   - Import errors

2. **High Priority** (Should fix soon)
   - Unused imports/variables
   - Deprecated APIs
   - Security issues

3. **Medium Priority** (Good to fix)
   - Code complexity warnings
   - Best practice violations
   - Maintainability issues

4. **Low Priority** (Nice to have)
   - Formatting inconsistencies
   - Docstring style
   - Comment improvements

#### Recommendations
For each category, provide:
- Count of issues found
- Most common issue types
- Suggested fix commands
- Estimated effort to fix

## Output Format

```
CODE QUALITY REPORT
===================

Target: ${ARGUMENTS:-.}

SUMMARY:
- Critical Issues: X
- High Priority: Y
- Medium Priority: Z
- Low Priority: W

BREAKDOWN BY TOOL:
[Detailed listing]

RECOMMENDATIONS:
1. Start with critical issues (type errors, syntax)
2. Fix high priority (unused code, deprecated APIs)
3. Apply automated formatters (black, prettier, ruff format)
4. Address remaining linting issues

SUGGESTED COMMANDS:
- For Python: claude /python:fix-aggressive
- For TypeScript: claude /typescript:fix
- For comprehensive fix: claude /quality:fix-all
```

## Next Steps

After reviewing this report, you can:
1. Run the appropriate fix command for your language
2. Fix issues manually
3. Configure tools to ignore certain rules
4. Add pre-commit hooks to prevent future issues

**No files will be modified by this command.**

Target: **${ARGUMENTS:-.}**
