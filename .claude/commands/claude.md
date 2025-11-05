**USAGE:** `/claude`

You MUST execute the following workflow to implement Claude Code best practices for project documentation.

## OBJECTIVE

Restructure project documentation following Claude Code best practices:
- Split large docs into focused, topic-specific files
- Create directory-specific documentation near relevant code
- Maintain a lightweight root CLAUDE.md as navigation index

## AUTOMATIC EXECUTION WORKFLOW

**STEP 1: Analyze Current Documentation**
- Read existing CLAUDE.md (if exists)
- Identify main topics/sections that can be split
- Check for existing .claude/ directory structure

**STEP 2: Create .claude/ Directory Structure**
Create focused documentation files in .claude/:
```
.claude/
├── README.md           # Overview & quick start
├── architecture.md     # System design & patterns
├── conventions.md      # Coding standards
├── deployment.md       # Deploy procedures
└── troubleshooting.md  # Common issues
```

**STEP 3: Create Directory-Specific Documentation**
Identify main source directories and create relevant docs:
```
src/
├── api/
│   └── API.md         # API-specific guidelines
├── services/
│   └── SERVICES.md    # Services patterns
├── models/
│   └── MODELS.md      # Data models guide
└── lib/
    └── LIB.md         # Utility functions guide
```

**STEP 4: Migrate Content**
- Extract content from existing CLAUDE.md to appropriate new files
- Keep each file under 500-1000 lines
- Preserve all important information
- Cross-reference between files using markdown links

**STEP 5: Create Lightweight Root CLAUDE.md**
Create minimal root file as navigation index:
```markdown
# Project Guide

## Quick Links
- [Overview & Quick Start](.claude/README.md)
- [Architecture & Design](.claude/architecture.md)
- [Coding Conventions](.claude/conventions.md)
- [Deployment Procedures](.claude/deployment.md)
- [Troubleshooting](.claude/troubleshooting.md)

## Domain Documentation
- [API Documentation](src/api/API.md)
- [Services Patterns](src/services/SERVICES.md)
- [Data Models](src/models/MODELS.md)
- [Libraries & Utils](src/lib/LIB.md)

## Current Focus
[Brief 2-3 sentence project status]

## Common Commands
[Most-used commands only - reference .claude/README.md for complete list]
```

**STEP 6: Git Commit**
- Stage all new documentation files
- Commit with message:
  ```
  docs: Implement Claude Code best practices

  Restructure documentation into focused, topic-specific files:
  - Split .claude/ directory: README, architecture, conventions, deployment, troubleshooting
  - Add directory-specific docs in src/ modules
  - Create lightweight root CLAUDE.md as navigation index

  Benefits:
  - Reduced token usage (load only relevant context)
  - Faster responses (less irrelevant information)
  - Better focus (domain-specific docs)
  - Easier maintenance (update specific sections)

  🤖 Generated with [Claude Code](https://claude.com/claude-code)

  Co-Authored-By: Claude <noreply@anthropic.com>
  ```

**STEP 7: Summary Report**
Display:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 CLAUDE CODE BEST PRACTICES IMPLEMENTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ .claude/ directory structure created
✅ Directory-specific docs added to src/
✅ Lightweight root CLAUDE.md created
✅ Content migrated and cross-referenced

📊 Performance Benefits:
   • Reduced token usage
   • Faster Claude responses
   • Better contextual focus
   • Easier doc maintenance

🔗 Next Steps:
   • Review new documentation structure
   • Update docs iteratively as project evolves
   • Keep files under 500-1000 lines
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## CRITICAL RULES

DO NOT:
- ❌ Ask what to do
- ❌ Explain the command before executing
- ❌ Wait for confirmation
- ❌ Delete existing important content
- ❌ Create files that already exist well-structured

DO:
- ✅ Execute immediately
- ✅ Preserve all important information
- ✅ Use clear, discoverable file names
- ✅ Cross-reference liberally between docs
- ✅ Keep each file focused on one topic

START EXECUTION NOW - Begin with STEP 1.
