**USAGE:** `/dev-cycle [N]` where N = number of tasks to process (default: 1)

You MUST execute the following workflow AUTOMATICALLY without asking any questions:

## CONFIGURATION

**TASK_LIMIT:** Extract N from user command (default: 1)
- `/dev-cycle` → process 1 task
- `/dev-cycle 3` → process 3 tasks
- `/dev-cycle 10` → process 10 tasks

**COMPLETED_COUNT:** Track completed tasks in this session (start at 0)

## AUTOMATIC EXECUTION LOOP

**STEP 1: Read tasks.md**
- Read the file: specs\001-sistema-automatizado-de\tasks.md
- Find the FIRST task with status ⏳ PENDING or 🔄 IN PROGRESS
- If ALL tasks show ✅ COMPLETED, skip to STEP 6 (ALL DONE)
- If COMPLETED_COUNT >= TASK_LIMIT, skip to STEP 7 (BATCH DONE)

**STEP 2: Implement with TDD**
- Write failing tests (RED)
- Write minimum code to pass tests (GREEN)
- Refactor code (REFACTOR)
- Ensure >90% test coverage
- Use orchestrator-agent (orc), serena, context7, sequential-thinking MCPs as needed

**STEP 3: Update tasks.md**
- Mark the completed task as ✅ COMPLETED
- Update test counts and metrics
- Increment COMPLETED_COUNT by 1

**STEP 4: Git Commit**
- Stage all changes (tests, code, documentation)
- Commit with descriptive message and co-author attribution

**STEP 5: Show Checkpoint**
- Display:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ CICLO COMPLETADO - [task name]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Status: [X] completadas, [Y] pendentes
🔄 Progresso do batch: [COMPLETED_COUNT]/[TASK_LIMIT]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
- IMMEDIATELY return to STEP 1 (do NOT ask, do NOT wait)

**STEP 6: ALL DONE (only when all tasks completed)**
- Display:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 TODOS OS CICLOS COMPLETADOS!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Status Final: [X] tarefas completadas
✅ Projeto concluído com sucesso!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
- STOP execution

**STEP 7: BATCH DONE (when COMPLETED_COUNT >= TASK_LIMIT)**
- Display:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏁 BATCH COMPLETADO - [COMPLETED_COUNT] tarefas processadas
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Status: [X] completadas, [Y] pendentes
🔄 Para continuar:
   1. Execute: /clear
   2. Execute: /dev-cycle [N]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
- STOP execution

## CRITICAL RULES

DO NOT:
- ❌ Ask what to do
- ❌ Explain the command
- ❌ Wait for confirmation
- ❌ Ask if I want to continue
- ❌ Stop between tasks (unless BATCH DONE)

DO:
- ✅ Execute immediately
- ✅ Loop automatically until TASK_LIMIT reached
- ✅ Follow TDD strictly (Red-Green-Refactor)
- ✅ Stop cleanly at TASK_LIMIT for /clear

START EXECUTION NOW - Begin with STEP 1.
