---
description: Run comprehensive static analysis (mypy, ruff, black, pylance, etc.) and systematically fix all issues
allowed-tools: Bash(*), Edit(*), View(*)
argument-hint: [optional: specific directory or file path]
---

# Code Quality Analysis and Systematic Fixes

Run comprehensive static analysis on the repository and systematically fix all identified issues without breaking functionality.

## Supported Languages and Tools

### Python
- **mypy**: Type checking
- **ruff**: Linting and formatting (replaces flake8, isort, etc.)
- **black**: Code formatting
- **pylint**: Additional linting (if available)

### JavaScript/TypeScript
- **ESLint**: Linting
- **Prettier**: Formatting
- **TypeScript compiler**: Type checking

### Other Languages
- **Go**: gofmt, golangci-lint, go vet
- **Rust**: rustfmt, clippy
- **Java**: checkstyle, spotless
- **C#**: dotnet format

## Analysis Process

### Phase 1: Detection and Setup
1. **Detect project language(s)** by examining:
   - File extensions in the repository
   - Configuration files (package.json, pyproject.toml, go.mod, Cargo.toml, etc.)
   - Existing tool configurations

2. **Check for existing tool configurations**:
   - pyproject.toml, setup.cfg, .flake8, .pylintrc
   - .eslintrc, .prettierrc, tsconfig.json
   - .golangci.yml, rustfmt.toml, etc.

3. **Install missing tools** (only if not already available):
   - Use appropriate package managers (pip, npm, cargo, etc.)
   - Prefer project-local installations when possible

### Phase 2: Analysis
4. **Run all applicable static analysis tools** in read-only mode:
   - Execute each tool and capture all errors/warnings
   - Organize findings by severity: errors → warnings → style issues
   - Create a summary report of all findings

5. **Categorize issues**:
   - **Critical**: Type errors, syntax errors, security issues
   - **High**: Unused imports, undefined variables, deprecated APIs
   - **Medium**: Code style violations, complexity warnings
   - **Low**: Formatting inconsistencies, docstring issues

### Phase 3: Systematic Fixes

6. **Fix issues in priority order** with safety checks:

   **For CRITICAL issues:**
   - Fix type errors by adding proper type hints or correcting types
   - Never use `# type: ignore` unless absolutely necessary
   - Document why any type ignores are needed
   
   **For HIGH priority issues:**
   - Remove unused imports and variables
   - Fix undefined variable references
   - Update deprecated API usage with modern equivalents
   
   **For MEDIUM priority issues:**
   - Fix linting violations (naming conventions, complexity)
   - Refactor overly complex functions if safe
   - Add missing error handling
   
   **For LOW priority issues:**
   - Apply automatic formatting (black, prettier, etc.)
   - Fix docstring formatting
   - Organize imports

7. **Apply fixes incrementally**:
   - Fix one category at a time
   - After each category, re-run analysis to verify no new issues
   - If new issues appear, investigate and resolve carefully

### Phase 4: Verification

8. **Run comprehensive verification**:
   - Re-run all static analysis tools to confirm 0 issues
   - Run the project's test suite (if available)
   - Build the project (if applicable)
   - Check for any import errors or runtime issues

9. **Create a summary report** showing:
   - Total issues found and fixed by category
   - Any remaining issues that couldn't be auto-fixed (with explanations)
   - Verification results (tests passed, build succeeded, etc.)

## Safety Guidelines

**CRITICAL: Follow these rules to avoid breaking functionality:**

1. **Never modify logic**:
   - Only fix code quality issues, not business logic
   - Don't change algorithm implementations
   - Don't alter control flow unless fixing actual bugs

2. **Preserve behavior**:
   - Keep function signatures compatible
   - Maintain API contracts
   - Don't change return types without careful consideration

3. **Test after changes**:
   - Run existing tests after each major fix batch
   - If tests fail, investigate immediately and revert if necessary
   - Add regression tests for any bugs found and fixed

4. **Use version control**:
   - Create a feature branch for these fixes
   - Commit changes incrementally by category
   - Use descriptive commit messages

5. **When in doubt, ask**:
   - For complex type errors, ask for clarification
   - For deprecated APIs, verify replacement is correct
   - For refactoring suggestions, get approval first

## Target Path

${ARGUMENTS:-"Run analysis on the entire repository"}

## Execution Instructions

Start by detecting the project type and available tools, then proceed through each phase systematically. Report progress after each phase and ask for confirmation before proceeding if you encounter complex issues that might require manual intervention.

Remember: **Code correctness > Code quality**. If a fix might change behavior, skip it and report it instead.
