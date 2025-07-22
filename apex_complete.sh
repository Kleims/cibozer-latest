#!/bin/bash
# APEX v4.1 - Complete iteration after implementation

# Load state
if [ ! -f .apex_state ]; then
    echo "❌ Error: .apex_state not found. Run apex.sh first."
    exit 1
fi

source .apex_state
source PROJECT_CONTEXT.md
source BASELINES.md

# Capture AFTER metrics
echo "📏 Capturing final metrics..."
AFTER_LOC=$(find . -type f -name "${FILE_PATTERN:-*.*}" -not -path "./.git/*" -not -path "*/node_modules/*" -not -path "*/venv/*" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)
AFTER_TODOS=$(grep -r "TODO\|FIXME" . --include="${FILE_PATTERN:-*.*}" --exclude-dir={.git,node_modules,dist,build,venv} 2>/dev/null | wc -l)

# Run tests and coverage
TEST_OUTPUT=$($TEST_CMD 2>&1 || true)
AFTER_COV=$($COVERAGE_CMD 2>&1 | grep -oE "${COVERAGE_PATTERN:-[0-9]+\.?[0-9]*}" | head -1 | tr -d '%' || echo 0)
AFTER_TESTS=$(echo "$TEST_OUTPUT" | grep -ciE "${TEST_PASS_PATTERN:-pass|ok|SUCCESS}" || echo 0)

# Check for critical test failures
CRITICAL_FAILS=$(echo "$TEST_OUTPUT" | grep -E "login|payment|auth|core|critical" | grep -ciE "${TEST_FAIL_PATTERN:-fail|error}" || echo 0)

# Calculate deltas
TESTS_DELTA=$((AFTER_TESTS - BEFORE_TESTS))
COV_DELTA=$(awk "BEGIN {printf \"%.1f\", $AFTER_COV - $BEFORE_COV}")
TODOS_DELTA=$((AFTER_TODOS - BEFORE_TODOS))

# Determine result
RESULT="SUCCESS"
[ $TESTS_DELTA -lt 0 ] && RESULT="PARTIAL"
[ $CRITICAL_FAILS -gt 0 ] && RESULT="FAILED"
[ $TESTS_DELTA -lt -3 ] && RESULT="FAILED"

# Auto-rollback on critical regression
if [ "$RESULT" = "FAILED" ] && [ $TESTS_DELTA -lt -5 ]; then
    echo "🚨 Critical regression detected! Rolling back..."
    git checkout $MAIN_BRANCH
    git branch -m "$BRANCH" "failed-$BRANCH"
    echo "ROLLBACK: Tests dropped by $TESTS_DELTA" >> METRICS.md
    rm -f .apex_state
    exit 1
fi

# Run linter if available
if [ -n "$LINT_CMD" ]; then
    echo "🔍 Running linter..."
    $LINT_CMD 2>/dev/null || true
fi

# Save successful patterns
if [ $TESTS_DELTA -gt 0 ] && [ -n "$ERROR_TYPE" ]; then
    FIXED_FILES=$(git diff --name-only 2>/dev/null | head -3 | tr '\n' ',')
    echo "$(date +%Y%m%d)|$STACK|$ERROR_TYPE|$FIXED_FILES|+$TESTS_DELTA tests" >> FIXES.log
fi

# Update baselines if improved
if [ $(awk "BEGIN {print ($AFTER_COV > $COV)}") -eq 1 ]; then
    sed -i.bak "s/COV=.*/COV=$AFTER_COV/" BASELINES.md && rm -f BASELINES.md.bak
fi
if [ $AFTER_TESTS -gt $TESTS ]; then
    sed -i.bak "s/TESTS=.*/TESTS=$AFTER_TESTS/" BASELINES.md && rm -f BASELINES.md.bak
fi

# Get list of changed files
CHANGED_FILES=$(git diff --name-only 2>/dev/null | head -5 | sed 's/^/- /')

# Increment counter
echo "$((ITER+1))" > .iteration

# Commit with comprehensive message
git add -A
git commit -m "$MODE: Iteration $ITER complete | Focus: $NEXT_FOCUS

Result: $RESULT
Tests: $BEFORE_TESTS → $AFTER_TESTS (Δ$TESTS_DELTA)
Coverage: $BEFORE_COV% → $AFTER_COV% (Δ$COV_DELTA)
TODOs: $BEFORE_TODOS → $AFTER_TODOS (Δ$TODOS_DELTA)

Changes:
$CHANGED_FILES"

# Merge if successful
if [ "$RESULT" != "FAILED" ]; then
    git checkout $MAIN_BRANCH
    git merge --no-ff "$BRANCH" -m "Merge: Iteration $ITER - $MODE - $(date)"
    git tag "iteration-$ITER-complete"
    
    # Clean up iteration branch
    git branch -d "$BRANCH" 2>/dev/null || true
fi

# Restore stashed changes if any
[ "$STASHED" = "true" ] && git stash pop

# Update METRICS.md
DURATION=$(($(date +%s) - START_TIME))
cat >> METRICS.md << EOF
## Iteration #$ITER - $(date '+%Y-%m-%d %H:%M:%S')
- **Mode**: $MODE | **Health**: $HEALTH/100 | **Focus**: $NEXT_FOCUS
- **Result**: $RESULT
- **Stack**: $STACK
- **Tests**: $AFTER_TESTS (Δ$TESTS_DELTA) | **Coverage**: $AFTER_COV% (Δ$COV_DELTA)
- **LOC**: $AFTER_LOC | **TODOs**: $AFTER_TODOS (Δ$TODOS_DELTA)
- **Duration**: ${DURATION}s
- **Unresolved**: $(grep -c "Priority: HIGH" FAILED_ATTEMPTS.md 2>/dev/null || echo 0) issues
EOF

# Pattern analysis every 10 iterations
if [ $((ITER % 10)) -eq 0 ]; then
    echo -e "\n### 📊 Pattern Analysis (Last 10 iterations)" >> METRICS.md
    echo "**Success by focus area:**" >> METRICS.md
    grep -E "Focus:.*Result: SUCCESS" METRICS.md | sed 's/.*Focus: \([^ ]*\).*/\1/' | sort | uniq -c | sort -nr >> METRICS.md
    
    echo -e "\n**Recurring issues:**" >> METRICS.md
    grep "Issue:" FAILED_ATTEMPTS.md 2>/dev/null | sort | uniq -c | sort -nr | head -5 >> METRICS.md
fi

# Clean up
rm -f .apex_state

# Output summary
echo ""
echo "✅ Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Tests: $BEFORE_TESTS → $AFTER_TESTS (Δ$TESTS_DELTA)"
echo "Coverage: $BEFORE_COV% → $AFTER_COV% (Δ$COV_DELTA)"
echo "Result: $RESULT"
echo ""

# Show any high priority issues
HIGH_PRIORITY=$(grep -c "Priority: HIGH" FAILED_ATTEMPTS.md 2>/dev/null || echo 0)
if [ $HIGH_PRIORITY -gt 0 ]; then
    echo "⚠️ Known Issues"
    grep -B2 "Priority: HIGH" FAILED_ATTEMPTS.md | tail -6
fi