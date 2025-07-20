#!/bin/bash
# Universal Codebase Evolution Engine - ANY STACK
# Run with: ./evolution_engine.sh

# Initialize/Load Context
[ ! -f .iteration ] && echo "0" > .iteration && touch METRICS.md FAILED_ATTEMPTS.md PROJECT_CONTEXT.md BASELINES.md FIXES.log
ITER=$(cat .iteration)
echo "Iteration: $ITER | $(date '+%Y-%m-%d %H:%M:%S')"

# First run: Detect stack and commands
if [ ! -s PROJECT_CONTEXT.md ] || ! grep -q "TEST_CMD" PROJECT_CONTEXT.md; then
    echo "First run - analyzing project stack..."
    # For Python Flask project (already detected)
    cat >> PROJECT_CONTEXT.md << 'EOF'
# Commands (auto-detected for Python/Flask)
TEST_CMD="python -m pytest"
BUILD_CMD="pip install -r requirements.txt"
COVERAGE_CMD="python -m pytest --cov=. --cov-report=term-missing"
AUDIT_CMD="pip-audit"
FILE_PATTERN="*.py"
TEST_FAIL_PATTERN="FAILED|AssertionError|Exception|ERROR"
TEST_PASS_PATTERN="passed|PASSED"
COVERAGE_PATTERN="[0-9]+%"
EOF
fi

# Load detected commands
eval "$(grep "^[A-Z_]*=" PROJECT_CONTEXT.md)"

# Load baselines
if [ -f BASELINES.md ]; then
    eval "$(cat BASELINES.md)"
else
    echo "COV=0;PERF=999;TESTS=0;LOC=0" > BASELINES.md
    eval "$(cat BASELINES.md)"
fi

# Universal health check (works for any stack)
echo "Running health check..."
FAILS=$($TEST_CMD 2>&1 | grep -ciE "${TEST_FAIL_PATTERN:-fail|error|FAIL|ERROR}" || echo 0)
PASSES=$($TEST_CMD 2>&1 | grep -ciE "${TEST_PASS_PATTERN:-pass|ok|SUCCESS}" || echo 0)
SECURITY=$($AUDIT_CMD 2>&1 | grep -ciE "high|critical|vulnerable" 2>/dev/null || echo 0)
HEALTH=$((100 - FAILS*5 - SECURITY*10))
LAST_RESULT=$(tail -1 METRICS.md | grep -oE "Result: [A-Z]*" | cut -d' ' -f2)

MODE="STANDARD"
[ $HEALTH -lt 60 ] && MODE="RECOVERY"
[ "$LAST_RESULT" = "FAILED" ] && MODE="RECOVERY"
[ $((ITER % 5)) -eq 0 ] && [ $ITER -ne 0 ] && [ $HEALTH -gt 80 ] && MODE="FEATURE"
[ $((ITER % 10)) -eq 0 ] && [ $ITER -ne 0 ] && MODE="ARCHITECTURE"
echo "Mode: $MODE (Health: $HEALTH/100)"

# Pre-Work Setup
# Git health
[ ! -d .git ] && git init && git add . && git commit -m "Initial commit"
git checkout main 2>/dev/null || git checkout -b main
[ -n "$(git status --porcelain)" ] && git add -A && git commit -m "WIP: Pre-iteration $((ITER+1))"

# Create branch & checkpoint
git checkout -b "iteration-$((ITER+1))-$MODE"
git tag -a "checkpoint-$ITER" -m "Checkpoint $(date)" 2>/dev/null

# Capture before metrics (universal)
echo "=== Metrics ==="
BEFORE_LOC=$(find . -type f -name "${FILE_PATTERN:-*.py}" -not -path "./.git/*" -not -path "./venv/*" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
BEFORE_TODOS=$(grep -r 'TODO\|FIXME' . --include="${FILE_PATTERN}" --exclude-dir={node_modules,.git,target,dist,build,venv} 2>/dev/null | wc -l)
BEFORE_COV=$($COVERAGE_CMD 2>&1 | grep -oE "${COVERAGE_PATTERN:-[0-9]+%}" | head -1 | tr -d '%' || echo 0)
BEFORE_TESTS=$(python -m pytest --collect-only -q 2>&1 | grep -oE "[0-9]+ test" | grep -oE "[0-9]+" || echo 0)
BEFORE_PERF=$(date +%s)

# For suspicious file detection
ERROR_TYPE=$($TEST_CMD 2>&1 | grep -E "${TEST_FAIL_PATTERN:-Error|Failed|FAIL}" | head -1 | cut -d: -f1)
TROUBLE_FILES=$(git log --format="" --name-only --grep="fix\|bug" 2>/dev/null | sort | uniq -c | sort -nr | head -5 | awk '{print $2}')

# Intelligent Aspect Rotation
LAST_FOCUS=$(git log --oneline -3 | grep -oE '\(frontend\)|\(backend\)|\(database\)|\(testing\)|\(docs\)|\(security\)|\(devops\)|\(a11y\)|\(logging\)|\(refactor\)' | tr -d '()' | head -1)
ASPECTS="frontend backend database testing docs security devops a11y logging refactor"
# If high-priority issue exists, override rotation
[ $FAILS -gt 5 ] && NEXT_FOCUS="testing"
[ $SECURITY -gt 0 ] && NEXT_FOCUS="security"
# Otherwise rotate
[ -z "$NEXT_FOCUS" ] && {
    if [ -n "$LAST_FOCUS" ]; then
        NEXT_FOCUS=$(echo $ASPECTS | tr ' ' '\n' | grep -v "$LAST_FOCUS" | head -1)
    else
        NEXT_FOCUS="backend"
    fi
}

echo "Next focus area: $NEXT_FOCUS"
echo "Error type: $ERROR_TYPE"
echo "Trouble files: $TROUBLE_FILES"

# Save state for AI to use
cat > .evolution_state << EOF
ITER=$((ITER+1))
MODE=$MODE
HEALTH=$HEALTH
NEXT_FOCUS=$NEXT_FOCUS
ERROR_TYPE=$ERROR_TYPE
TROUBLE_FILES=$TROUBLE_FILES
BEFORE_LOC=$BEFORE_LOC
BEFORE_TODOS=$BEFORE_TODOS
BEFORE_COV=$BEFORE_COV
BEFORE_TESTS=$BEFORE_TESTS
BEFORE_PERF=$BEFORE_PERF
EOF

echo ""
echo "=== Evolution Engine Ready ==="
echo "AI should now execute based on MODE=$MODE and FOCUS=$NEXT_FOCUS"
echo "State saved to .evolution_state"
echo ""
echo "After implementation, run: ./evolution_complete.sh"