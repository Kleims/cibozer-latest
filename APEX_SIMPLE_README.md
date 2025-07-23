# APEX Simple - Lean Iteration System

One command, consistent results, real progress.

## Quick Start

```bash
# Run a new iteration
./simple.sh

# Complete an iteration
./simple.sh complete 1

# View history
./simple.sh history
```

## How It Works

1. **Assess** - Quickly checks project health:
   - Test passing rate
   - Errors in logs
   - Technical debt (TODOs)
   - Critical files present

2. **Focus** - Automatically decides what to work on:
   - FIX_TESTS - If tests < 70% passing
   - FIX_ERRORS - If many errors in logs
   - FIX_STRUCTURE - If critical files missing
   - CLEAN_DEBT - If too many TODOs
   - IMPROVE_TESTS - If tests < 90%
   - BUILD_FEATURE - If everything healthy

3. **Execute** - Generates ONE clear prompt with:
   - Current state
   - Specific task
   - Clear rules
   - No ambiguity

## Files

- `apex_simple.py` - The core system
- `simple.sh` - Convenience launcher
- `.apex_simple/` - Iteration history (auto-created)

## Key Benefits

- **Simple** - No complex configuration
- **Consistent** - Same process every time
- **Focused** - One task per iteration
- **Real** - No stub implementations allowed
- **Tracked** - Full history of progress

## Example

```bash
$ ./simple.sh
============================================================
APEX SIMPLE - ITERATION #1
============================================================

ASSESSING PROJECT HEALTH...

Running tests...

ASSESSMENT COMPLETE
Focus: FIX_TESTS
Reason: Tests only 64.1% passing

[Generated prompt with specific instructions...]
```

That's it. Simple, effective, consistent.