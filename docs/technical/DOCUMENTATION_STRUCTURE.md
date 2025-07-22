# Cibozer Documentation Structure

## Iteration Tracking Files

### 1. ITERATION_LOG.md
**Purpose**: Consolidated log of all iteration results
**Updates**: After each iteration
**Contents**:
- Before state
- Execution details (real vs fake)
- After state
- Next steps

### 2. METRICS.md
**Purpose**: High-level metrics tracking
**Updates**: After each iteration
**Contents**:
- Iteration number, date, mode
- Phase and progress
- Key metrics (test coverage, health score)
- Brief change summary

### 3. CHANGELOG.md
**Purpose**: Detailed task-by-task changes
**Updates**: Automatically by launch_automation.py
**Contents**:
- Task starts/completions/failures
- Timestamped entries

### 4. launch_metrics.json
**Purpose**: Machine-readable metrics
**Updates**: Automatically
**Contents**:
- Test coverage history
- Performance metrics
- User metrics

## Other Key Files

### 30_DAY_LAUNCH_PLAN.md
- Master plan with weekly breakdown
- Success metrics and targets
- Not modified by automation

### REAL_SCRIPTS_AUDIT.md
- Lists which scripts do real work vs simulation
- Reference for what needs fixing

### .launch_progress.json
- Current phase and completed tasks
- Updated by automation

## What NOT to Create
❌ Individual iteration files (ITERATION_XX_BEFORE.md)
❌ Duplicate tracking files
❌ Temporary status files

## Best Practices
1. One source of truth per metric
2. Consolidate related information
3. Keep machine-readable separate from human-readable
4. Document real work vs simulations