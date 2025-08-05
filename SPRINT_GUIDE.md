# 🚀 Cibozer Sprint System Guide

## Quick Start

Just run ONE command to start a new sprint:

```bash
sprint
```

Or on Unix/Mac:
```bash
python new_sprint.py
```

That's it! The system will:
1. **Analyze** current status
2. **Recommend** sprint options based on priorities
3. **Let you choose** what to focus on
4. **Plan** the sprint tasks
5. **Execute** the work
6. **Review** the results
7. **Document** everything for next session

## How It Works

### 1️⃣ Status Check
The system automatically:
- Runs all tests to see coverage
- Scans for security issues
- Checks code quality
- Reviews last sprint's remaining tasks

### 2️⃣ Smart Recommendations
Based on status, you'll see prioritized options like:
- 🔴 **HIGH**: Fix critical security issues
- 🟡 **MEDIUM**: Improve test coverage
- 🟢 **LOW**: Add new features

### 3️⃣ Your Choice
You simply pick a number (1-5) for what to work on. The system handles the rest.

### 4️⃣ Automatic Execution
The system will:
- Create a detailed task list
- Execute fixes automatically where possible
- Track what worked and what needs manual help
- Measure improvements

### 5️⃣ Documentation & Continuity
At the end, everything is:
- Saved to sprint history
- Prepared as a git commit
- Ready for the next session

## Commands

### Windows
```bash
sprint              # Start new sprint
sprint status       # Check current status
sprint history      # View past sprints
sprint commit       # Commit changes
```

### Unix/Mac/Linux
```bash
python new_sprint.py          # Start new sprint
python new_sprint.py status   # Check current status
python new_sprint.py history  # View past sprints
```

## Sprint Workflow

```
┌─────────────┐
│   START     │
│ "sprint"    │
└──────┬──────┘
       ↓
┌─────────────┐
│   STATUS    │ → Shows tests, issues, quality
└──────┬──────┘
       ↓
┌─────────────┐
│ RECOMMEND   │ → 5 prioritized options
└──────┬──────┘
       ↓
┌─────────────┐
│   CHOOSE    │ → You pick (1-5)
└──────┬──────┘
       ↓
┌─────────────┐
│    PLAN     │ → Creates task list
└──────┬──────┘
       ↓
┌─────────────┐
│  EXECUTE    │ → Runs fixes
└──────┬──────┘
       ↓
┌─────────────┐
│   REVIEW    │ → Shows improvements
└──────┬──────┘
       ↓
┌─────────────┐
│  DOCUMENT   │ → Saves for next time
└──────┬──────┘
       ↓
┌─────────────┐
│    DONE!    │
│ Ready to    │
│   commit    │
└─────────────┘
```

## File Structure

```
.sprint/
├── current_sprint.json      # Active sprint data
├── sprint_history.json      # All past sprints
├── recommendations.json     # Last recommendations
├── next_commit.txt         # Ready commit message
├── last_sprint_summary.md  # Summary for next session
└── sprint_001.json         # Archived sprints
    sprint_002.json
    ...
```

## Best Practices

1. **One Sprint Per Day**: Focus on completing one sprint well
2. **Always Commit**: Use `sprint commit` after each sprint
3. **Review History**: Check `sprint history` before starting
4. **Trust the Priorities**: The system knows what needs attention

## Typical Session

```bash
# Monday morning - start new session
$ sprint

🚀 UNIFIED SPRINT SYSTEM - STARTING NEW SPRINT CYCLE
──────────────────────────────────────────────────────

📊 STEP 1: ANALYZING CURRENT STATUS...
   Tests: 137/201 passing (68.2%)
   Critical Issues: 7
   Code Quality: 7/10

💡 STEP 2: SPRINT RECOMMENDATIONS

1. 🔴 Security & Critical Issues [HIGH]
   Fix 7 critical security issues
   Impact: Eliminates security vulnerabilities

2. 🟡 Test Coverage Improvement [MEDIUM]
   Increase test coverage from 68.2% to 90%+
   Impact: Fix 64 failing tests, add missing tests

👉 Select sprint focus (1-5) or 'q' to quit: 1

✅ Selected: Security & Critical Issues

[... system runs automatically ...]

✅ SPRINT CYCLE COMPLETE!

$ sprint commit
Sprint committed!
```

## Next Session

When you return, just run `sprint` again. The system remembers everything and continues from where you left off.

## Troubleshooting

- **Tests timing out**: The system has 60-second timeout, will use cached values
- **Can't find sprint**: Check you're in the project root (where .sprint/ exists)
- **Permission errors**: Make sure you have write access to .sprint/ directory

## Philosophy

This sprint system follows the principle of **"One Command, Full Cycle"**:
- Minimize decisions
- Maximize automation
- Track everything
- Always move forward

Every sprint makes the codebase better. No sprint is wasted.