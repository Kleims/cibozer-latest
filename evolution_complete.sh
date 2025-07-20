#!/bin/bash
# Complete the evolution iteration after implementation

# Load state
if [ ! -f .evolution_state ]; then
    echo "Error: .evolution_state not found. Run evolution_engine.sh first."
    exit 1
fi

source .evolution_state

# Load commands
eval "$(grep "^[A-Z_]*=" PROJECT_CONTEXT.md)"

# Capture after metrics (universal)
AFTER_LOC=$(find . -type f -name "${FILE_PATTERN:-*.py}" -not -path "./.git/*" -not -path "./venv/*" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
AFTER_TODOS=$(grep -r 'TODO\|FIXME' . --include="${FILE_PATTERN}" --exclude-dir={node_modules,.git,target,dist,build,venv} 2>/dev/null | wc -l)
AFTER_COV=$($COVERAGE_CMD 2>&1 | grep -oE "${COVERAGE_PATTERN:-[0-9]+%}" | head -1 | tr -d '%' || echo 0)
AFTER_TESTS=$(python -m pytest --collect-only -q 2>&1 | grep -oE "[0-9]+ test" | grep -oE "[0-9]+" || echo 0)
AFTER_PERF=$(date +%s)
PERF_TIME=$((AFTER_PERF - BEFORE_PERF))

# Check critical tests
CRITICAL_FAILS=$($TEST_CMD 2>&1 | grep -E "login|payment|auth|core|critical" | grep -ciE "${TEST_FAIL_PATTERN:-fail|error}" || echo 0)

# Determine result
TESTS_DELTA=$((AFTER_TESTS - BEFORE_TESTS))
COV_DELTA=$((AFTER_COV - BEFORE_COV))
RESULT="SUCCESS"
[ $TESTS_DELTA -lt 0 ] && RESULT="PARTIAL"
[ $CRITICAL_FAILS -gt 0 ] && RESULT="FAILED"
[ $TESTS_DELTA -lt -3 ] && RESULT="FAILED"

# Auto-rollback if critical regression
if [ "$RESULT" = "FAILED" ] && [ $TESTS_DELTA -lt -5 ]; then
    git checkout main
    git branch -D "iteration-$ITER-$MODE"
    echo "ROLLBACK: Tests -$TESTS_DELTA" >> METRICS.md
    exit 1
fi

# Save successful fixes
if [ $TESTS_DELTA -gt 0 ] && [ -n "$ERROR_TYPE" ]; then
    FIX_DIFF=$(git diff --stat HEAD~1 2>/dev/null | head -2 | tr '\n' ' ')
    echo "$(date +%Y%m%d)|$ERROR_TYPE|$FIX_DIFF|+$TESTS_DELTA tests" >> FIXES.log
fi

# Update baselines if improved
[ $AFTER_COV -gt $COV ] && sed -i "s/COV=.*/COV=$AFTER_COV/" BASELINES.md
[ $AFTER_TESTS -gt $TESTS ] && sed -i "s/TESTS=.*/TESTS=$AFTER_TESTS/" BASELINES.md

# Increment iteration
echo "$ITER" > .iteration

# Commit with proper format
git add -A
git commit -m "chore($NEXT_FOCUS): Iteration $ITER complete

Mode: $MODE | Result: $RESULT
Coverage: $AFTER_COV% (Δ$COV_DELTA) | Tests: $AFTER_TESTS (Δ$TESTS_DELTA)
LOC: $AFTER_LOC | TODOs: $AFTER_TODOS | Time: ${PERF_TIME}s"

# Merge if not failed
if [ "$RESULT" != "FAILED" ]; then
    git checkout main
    git merge --no-ff "iteration-$ITER-$MODE" -m "Merge: Iteration $ITER - $MODE - $(date)"
    git tag "iteration-$ITER-complete"
fi

# Update METRICS.md
cat >> METRICS.md << EOF
## Iteration #$ITER - $(date '+%Y-%m-%d %H:%M:%S')
- Mode: $MODE | Health: $HEALTH/100
- Focus: $NEXT_FOCUS
- Result: $RESULT
- Coverage: $AFTER_COV% (Δ$COV_DELTA) | Tests: $AFTER_TESTS (Δ$TESTS_DELTA)
- LOC: $AFTER_LOC | TODOs: $AFTER_TODOS
- Unresolved: $(grep -c "Priority: HIGH" FAILED_ATTEMPTS.md 2>/dev/null || echo 0) high priority issues
- Time: ${PERF_TIME}s
EOF

# Pattern learning every 10
if [ $((ITER % 10)) -eq 0 ]; then
    echo "=== PATTERNS ===" >> METRICS.md
    grep "SUCCESS" METRICS.md | grep "Focus:" | sort | uniq -c | sort -nr >> METRICS.md
    grep -A1 "Priority: ARCHITECTURAL" FAILED_ATTEMPTS.md 2>/dev/null | head -10 >> METRICS.md
fi

# Clean up
rm -f .evolution_state

echo ""
echo "=== Evolution Complete ==="
echo "Result: $RESULT"
echo "Coverage: $BEFORE_COV% → $AFTER_COV% (Δ$COV_DELTA)"
echo "Tests: $BEFORE_TESTS → $AFTER_TESTS (Δ$TESTS_DELTA)"
echo "Time: ${PERF_TIME}s"