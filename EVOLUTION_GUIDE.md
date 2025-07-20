# Universal Codebase Evolution Engine - Usage Guide

## Quick Start

1. **Start an iteration:**
   ```bash
   ./evolution_engine.sh
   ```

2. **AI implements based on mode and focus area shown**

3. **Complete the iteration:**
   ```bash
   ./evolution_complete.sh
   ```

## Execution Flow

### 1. evolution_engine.sh
- Detects project stack (Python, Node.js, Go, etc.)
- Calculates health score
- Determines mode (RECOVERY/STANDARD/FEATURE/ARCHITECTURE)
- Selects focus area via intelligent rotation
- Creates git branch and checkpoint
- Captures before metrics
- Saves state to `.evolution_state`

### 2. AI Implementation Phase
Based on the mode:

#### RECOVERY Mode (health < 60)
- Fix critical breaks only
- Web search for persistent errors
- Skip new features

#### STANDARD Mode (default)
- Fix 1-2 issues (80%)
- Add 1 improvement (20%)
- Check git history for similar fixes

#### FEATURE Mode (every 5th iteration, health > 80)
- Web search competitors/trends
- Implement NEW feature with tests
- Critical fixes only (20%)

#### ARCHITECTURE Mode (every 10th iteration)
- Review patterns in FAILED_ATTEMPTS.md
- Refactor repeated code
- Update documentation
- Big picture improvements

### 3. evolution_complete.sh
- Captures after metrics
- Determines success/failure
- Auto-rollbacks if critical regression
- Updates baselines
- Commits with proper format
- Merges to main if successful
- Updates METRICS.md

## Git Commit Format

```
type(aspect): description

Mode: MODE | Result: RESULT
Coverage: X% (ΔY) | Tests: A (ΔB)
LOC: N | TODOs: M | Time: Ts
```

Types: feat, fix, docs, style, refactor, perf, test, chore

Aspects: frontend, backend, database, testing, docs, security, devops, a11y, logging, refactor

## Files Created/Updated

- `.iteration` - Current iteration number
- `METRICS.md` - Historical metrics
- `FAILED_ATTEMPTS.md` - Documented failures
- `PROJECT_CONTEXT.md` - Stack detection & commands
- `BASELINES.md` - Best achieved metrics
- `FIXES.log` - Successful fix patterns
- `.evolution_state` - Temporary state between scripts

## Example Workflow

```bash
# Start iteration 7
$ ./evolution_engine.sh
Iteration: 6 | 2025-07-20 07:15:00
Mode: STANDARD (Health: 95/100)
Next focus area: frontend
Error type: ImportError
=== Evolution Engine Ready ===

# AI reads state and implements...
# - Fixes ImportError issue
# - Improves frontend dashboard
# - Adds tests

# Complete iteration
$ ./evolution_complete.sh
=== Evolution Complete ===
Result: SUCCESS
Coverage: 30% → 35% (Δ5)
Tests: 60 → 65 (Δ5)
Time: 180s
```

## Tips

1. **Always run both scripts** - Don't skip evolution_complete.sh
2. **Check .evolution_state** - Contains all context for AI
3. **Review FAILED_ATTEMPTS.md** - Patterns emerge over time
4. **Trust the rotation** - Ensures balanced improvements
5. **Document failures** - If stuck, update FAILED_ATTEMPTS.md

## Customization

Edit PROJECT_CONTEXT.md to adjust:
- Test commands
- Build commands
- File patterns
- Error patterns

## Troubleshooting

- **"command not found"**: Make scripts executable: `chmod +x evolution_*.sh`
- **Wrong mode**: Check health calculation in METRICS.md
- **No aspect found**: Ensure commits use format: `type(aspect): message`
- **Metrics not updating**: Check command patterns in PROJECT_CONTEXT.md