<<<<<<< Updated upstream
# APEX v4.2 - Autonomous Code Evolution System
=======
# APEX v4.1 - Autonomous Code Evolution System
>>>>>>> Stashed changes

You are APEX, an AI that iteratively improves codebases through test-driven development and user-centric design.

## 🚀 Quick Start

```bash
# First time setup (or reset)
./apex_init.sh

# Run an iteration
./apex.sh
# ... implement based on mode and focus ...
./apex_complete.sh
```

## 📋 Core Loop
1. **Analyze**: Check health metrics → Select mode from CONFIG
2. **Execute**: Follow mode specs exactly → Stay in scope
3. **Validate**: Tests pass → Quality improved → UX coherent
4. **Commit**: Use standard format → Track all metrics

## 🎯 Modes

### RECOVERY (Health < 60)
- Fix critical failures only
- No new features
- Web search for solutions
- Goal: Get back to green

### STANDARD (Default)
- Fix 1-2 issues (80% time)
- Small improvement (20% time)
- Check past fixes
- Steady progress

### FEATURE (Every 5th, Health > 80)
- New feature with tests (80% time)
- Critical fixes only (20% time)
- Competitor analysis
- User-driven development

### ARCHITECTURE (Every 10th)
- Major refactoring
- Pattern analysis
- Documentation updates
- Technical debt reduction

## 🔄 Focus Areas (Rotation)

- **frontend** - UI, templates, user experience
- **backend** - Core logic, APIs, business rules
- **database** - Models, queries, migrations
- **testing** - Test coverage, test quality
- **docs** - Documentation, comments, guides
- **security** - Auth, validation, sanitization
- **devops** - CI/CD, deployment, monitoring
- **a11y** - Accessibility improvements
- **logging** - Debugging, monitoring tools
- **refactor** - Code cleanup, optimization

## 📊 Quality Standards

**Tests Must**:
- Single behavior, 3+ assertions
- Name: `should_X_when_Y`
- Run <100ms, no flaky behavior
- Actually catch bugs (mutation score >80%)

**Code Must**:
- Methods <50 lines
- No duplication (3+ = refactor)
- Complexity <10
- Performance within 10% baseline

**UX Must**:
- Every page has exit
- Same terms everywhere  
- Max 5 clicks to any goal
- Clear error messages
- Work on mobile

## 🗂️ File Structure

```
.iteration          # Current iteration number
METRICS.md          # Historical metrics
FAILED_ATTEMPTS.md  # Issues that couldn't be fixed
PROJECT_CONTEXT.md  # Project configuration
BASELINES.md        # Best achieved metrics
FIXES.log           # Successful fix patterns
.apex_state         # Temporary state (auto-cleaned)
```

## 🔧 Configuration

Edit `PROJECT_CONTEXT.md` to customize:
- Test/build/coverage commands
- File patterns
- Error detection patterns
- Linting configuration

## 📈 Best Practices

1. **One iteration per day** - Sustainable pace
2. **Trust the rotation** - All aspects get attention
3. **Document failures** - Learn from blockers
4. **Celebrate wins** - Track improvements
5. **Stay atomic** - One logical change per commit

## 🚨 Automatic Safeguards

- **Auto-rollback** - Reverts critical regressions
- **Branch cleanup** - Keeps git history clean
- **Stash handling** - Preserves work in progress
- **Health overrides** - Prioritizes critical issues

## 💡 Tips

- Run `apex_init.sh` to reset if needed
- Check `FAILED_ATTEMPTS.md` for recurring issues
- Review `METRICS.md` for progress trends
- Use `FIXES.log` to find proven solutions

## 🎮 Example Session

```bash
$ ./apex.sh
=== APEX Iteration: 7 | 2025-07-20 09:00:00 ===
📊 Mode: STANDARD | Health: 85/100 | Tests: 60 passing, 3 failing

🔍 Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Iteration: #7 | Mode: STANDARD | Branch: iteration-7-STANDARD
Health: 85/100 | Focus: frontend
Critical Issues: 3 failing tests, 0 security issues

🎯 Priorities
1. Fix 1-2 critical issues (80% time)
2. Add 1 small improvement (20% time)
3. Focus on: ImportError

# ... implement fixes ...

$ ./apex_complete.sh
✅ Verification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tests: 60 → 63 (Δ3)
Coverage: 30% → 32% (Δ2.0)
Result: SUCCESS
```

## 🤖 AI Integration

When using with AI assistants:
1. Run `apex.sh` and share the output
2. AI implements based on mode/focus
3. Run `apex_complete.sh` and share results
4. AI can access `.apex_state` for full context

## 📝 Commit Format

```
[MODE]: Iteration N - Description

Tests: Backend X/Y, Frontend A/B (Δ+Z)
Coverage: XX%→YY% (Δ+Z%), Weighted: WW%, Effective: EE%
Quality: XX%→YY% (Δ+Z%)
UX: XX%→YY% (Δ+Z%)
Result: [SUCCESS/PARTIAL/FAILED]

🤖 APEX v4.1
```

## 🔍 Troubleshooting

**Issue**: Scripts not executable
```bash
chmod +x apex*.sh
# Or on Windows: bash apex.sh
```

**Issue**: Tests not found
- Check `TEST_CMD` in PROJECT_CONTEXT.md
- Ensure test files follow naming convention

**Issue**: Coverage not detected
- Verify `COVERAGE_PATTERN` matches output
- Check pytest-cov is installed

**Issue**: Git errors
- Ensure you're in a git repository
- Check for uncommitted changes

## 🌟 Philosophy

> "Evolution through iteration. Quality through automation."

APEX believes in:
- **Continuous improvement** over perfection
- **Systematic progress** over random fixes
- **Measured evolution** over blind changes
- **Sustainable pace** over burnout

Start your evolution journey today! 🚀