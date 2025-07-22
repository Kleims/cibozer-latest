# APEX v4.2.1 Complete Iteration Flow

## 🚀 Start Phase (apex.sh)
1. ✅ **Initialize Tracking Files** - Creates if missing
2. ✅ **Check Tracking Health** - Warns if files are empty
3. ✅ **Load PROJECT_CONTEXT.md** - Sources configuration
4. ✅ **Resolve Merge Conflicts** - Auto-fixes PROJECT_CONTEXT.md conflicts
5. ✅ **Run Health Check** - Tests, security scan
6. ✅ **Determine Mode** - STANDARD/RECOVERY/FEATURE/ARCHITECTURE
7. ✅ **Select Focus Area** - Rotates through aspects
8. ✅ **Display Priorities** - Mode-specific tasks
9. ✅ **Show Project Context** - Architecture summary (NEW!)
10. ✅ **Save State** - Includes context in .apex_state (NEW!)

## 💻 Implementation Phase (AI Work)
- AI receives:
  - Current mode and focus area
  - Health metrics and issues
  - Project context summary
  - Specific priorities for the iteration
  - Previous trouble files

## ✅ Completion Phase (apex_complete.sh)
1. ✅ **Capture Final Metrics** - LOC, TODOs, tests, coverage
2. ✅ **Determine Result** - SUCCESS/PARTIAL/FAILED
3. ✅ **Update METRICS.md** - Full iteration details with change summary
4. ✅ **Update FAILED_ATTEMPTS.md** - If tests failed or issues found
5. ✅ **Update FIXES.log** - If successful fixes were made
6. ✅ **Update BASELINES.md** - Coverage, tests, LOC
7. ✅ **Pattern Analysis** - Every 10 iterations
8. ✅ **Git Operations** - Commit, merge, tag
9. ✅ **Rollback Protection** - Auto-rollback on critical regression

## 📊 Tracking Files Updated
- **METRICS.md** ✅ - Every iteration with comprehensive details
- **FAILED_ATTEMPTS.md** ✅ - When failures occur
- **FIXES.log** ✅ - When fixes are successful
- **BASELINES.md** ✅ - When metrics improve
- **PROJECT_CONTEXT.md** ✅ - Reviewed every iteration, updated in ARCHITECTURE mode

## 🔄 Iteration Modes
1. **STANDARD** - Fix issues (80%) + improvements (20%)
2. **RECOVERY** - Critical fixes only when health < 60%
3. **FEATURE** - New features (80%) + fixes (20%) every 5th iteration
4. **ARCHITECTURE** - Structural improvements every 10th iteration

## 📈 What's Tracked
- Test count and coverage
- Lines of code
- TODO/FIXME count
- Failing test details
- Security vulnerabilities
- Performance baselines
- Changed files
- Success/failure patterns
- Duration of iterations

## 🎯 Alignment Status: FULLY ALIGNED ✅

The iteration system now:
1. Maintains comprehensive tracking
2. Shows project context to AI
3. Updates all metrics automatically
4. Handles merge conflicts
5. Provides rollback protection
6. Analyzes patterns over time