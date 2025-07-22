#!/bin/bash
# APEX v4.2 - Autonomous Code Evolution System
# Complete integrated script for evolution iterations

# Initialize tracking files
[ ! -f .iteration ] && echo "0" > .iteration && touch METRICS.md FAILED_ATTEMPTS.md PROJECT_CONTEXT.md BASELINES.md FIXES.log
ITER=$(cat .iteration)
START_TIME=$(date +%s)

# Verify tracking files are in good state
TRACKING_ISSUES=""
[ ! -s METRICS.md ] && TRACKING_ISSUES="$TRACKING_ISSUES METRICS.md(empty)"
[ ! -s BASELINES.md ] && TRACKING_ISSUES="$TRACKING_ISSUES BASELINES.md(empty)"
[ ! -s FIXES.log ] && TRACKING_ISSUES="$TRACKING_ISSUES FIXES.log(empty)"

if [ -n "$TRACKING_ISSUES" ]; then
    echo "⚠️  Tracking files need initialization:$TRACKING_ISSUES"
    # Initialize empty files with headers
    [ ! -s METRICS.md ] && echo "# APEX Metrics Log" > METRICS.md
    [ ! -s BASELINES.md ] && echo "COV=0" > BASELINES.md && echo "PERF=999" >> BASELINES.md && echo "TESTS=0" >> BASELINES.md && echo "LOC=0" >> BASELINES.md
    [ ! -s FIXES.log ] && echo "# APEX Fixes Log" > FIXES.log && echo "Track all fixes applied during iterations" >> FIXES.log && echo "" >> FIXES.log && echo "Format: [Iteration #] - [Date] - [Fix Description]" >> FIXES.log && echo "==========================================" >> FIXES.log
    [ ! -s FAILED_ATTEMPTS.md ] && echo "# APEX Failed Attempts Log" > FAILED_ATTEMPTS.md && echo "*Document failed iterations for analysis and learning*" >> FAILED_ATTEMPTS.md
fi

echo "=== APEX Iteration: $ITER | $(date '+%Y-%m-%d %H:%M:%S') ==="

# First run: Detect stack and commands
if [ ! -s PROJECT_CONTEXT.md ] || ! grep -q "TEST_CMD" PROJECT_CONTEXT.md; then
    echo "🔍 First run - analyzing project stack..."
    # For Python Flask project (already detected)
    cat > PROJECT_CONTEXT.md << 'EOF'
# Project Context - Cibozer
STACK="Python/Flask"
TEST_CMD="python -m pytest"
BUILD_CMD="pip install -r requirements.txt"
COVERAGE_CMD="python -m pytest --cov=. --cov-report=term-missing"
AUDIT_CMD="pip-audit"
FILE_PATTERN="*.py"
TEST_FAIL_PATTERN="FAILED|AssertionError|Exception|ERROR"
TEST_PASS_PATTERN="passed|PASSED"
COVERAGE_PATTERN="[0-9]+%"
LINT_CMD="python -m flake8 . --max-line-length=120 --exclude=venv,.git,__pycache__"
EOF
elif grep -q "<<<<<<< Updated upstream" PROJECT_CONTEXT.md 2>/dev/null; then
    echo "⚠️  Merge conflicts detected in PROJECT_CONTEXT.md - preserving v4.1 version"
    # Extract and preserve the v4.1 content if it exists
    if grep -q "Project Context - Cibozer v4.1" PROJECT_CONTEXT.md; then
        # Keep a backup
        cp PROJECT_CONTEXT.md PROJECT_CONTEXT.md.conflict
        # Extract the v4.1 content between conflict markers
        sed -n '/<<<<<<< Updated upstream/,/=======/{/<<<<<<< Updated upstream/!{/=======/!p}}' PROJECT_CONTEXT.md > PROJECT_CONTEXT.md.tmp
        # Add the test commands at the top
        echo "# Project Context - Cibozer v4.1" > PROJECT_CONTEXT.md.new
        echo "STACK=\"Python/Flask\"" >> PROJECT_CONTEXT.md.new
        echo "TEST_CMD=\"python -m pytest\"" >> PROJECT_CONTEXT.md.new
        echo "BUILD_CMD=\"pip install -r requirements.txt\"" >> PROJECT_CONTEXT.md.new
        echo "COVERAGE_CMD=\"python -m pytest --cov=. --cov-report=term-missing\"" >> PROJECT_CONTEXT.md.new
        echo "AUDIT_CMD=\"pip-audit\"" >> PROJECT_CONTEXT.md.new
        echo "FILE_PATTERN=\"*.py\"" >> PROJECT_CONTEXT.md.new
        echo "TEST_FAIL_PATTERN=\"FAILED|AssertionError|Exception|ERROR\"" >> PROJECT_CONTEXT.md.new
        echo "TEST_PASS_PATTERN=\"passed|PASSED\"" >> PROJECT_CONTEXT.md.new
        echo "COVERAGE_PATTERN=\"[0-9]+%\"" >> PROJECT_CONTEXT.md.new
        echo "LINT_CMD=\"python -m flake8 . --max-line-length=120 --exclude=venv,.git,__pycache__\"" >> PROJECT_CONTEXT.md.new
        echo "" >> PROJECT_CONTEXT.md.new
        # Append the architectural content
        grep -v "^STACK=\|^TEST_CMD=\|^BUILD_CMD=\|^COVERAGE_CMD=\|^AUDIT_CMD=\|^FILE_PATTERN=\|^TEST_FAIL_PATTERN=\|^TEST_PASS_PATTERN=\|^COVERAGE_PATTERN=\|^LINT_CMD=" PROJECT_CONTEXT.md.tmp >> PROJECT_CONTEXT.md.new
        mv PROJECT_CONTEXT.md.new PROJECT_CONTEXT.md
        rm -f PROJECT_CONTEXT.md.tmp
        echo "✅ PROJECT_CONTEXT.md conflicts resolved"
    fi
fi

# Load configuration
source PROJECT_CONTEXT.md
source BASELINES.md 2>/dev/null || echo "COV=0;PERF=999;TESTS=0;LOC=0" > BASELINES.md && source BASELINES.md

# Health check
echo "🏥 Running health check..."
TEST_OUTPUT=$($TEST_CMD 2>&1 || true)
FAILS=$(echo "$TEST_OUTPUT" | grep -ciE "${TEST_FAIL_PATTERN:-fail|error|FAIL|ERROR}" || echo 0)
PASSES=$(echo "$TEST_OUTPUT" | grep -ciE "${TEST_PASS_PATTERN:-pass|ok|SUCCESS|✓}" || echo 0)
SECURITY=$($AUDIT_CMD 2>&1 | grep -ciE "high|critical|vulnerable" 2>/dev/null || echo 0)
HEALTH=$((100 - FAILS*5 - SECURITY*10))
[ $HEALTH -lt 0 ] && HEALTH=0
LAST_RESULT=$(tail -1 METRICS.md 2>/dev/null | grep -oE "Result: [A-Z]*" | cut -d' ' -f2)

# Mode selection
MODE="STANDARD"
[ $HEALTH -lt 60 ] && MODE="RECOVERY"
[ "$LAST_RESULT" = "FAILED" ] && MODE="RECOVERY"
[ $((ITER % 5)) -eq 0 ] && [ $ITER -ne 0 ] && [ $HEALTH -gt 80 ] && MODE="FEATURE"
[ $((ITER % 10)) -eq 0 ] && [ $ITER -ne 0 ] && MODE="ARCHITECTURE"
echo "📊 Mode: $MODE | Health: $HEALTH/100 | Tests: $PASSES passing, $FAILS failing"

# Pre-Work Setup
# Ensure git is initialized and configured
[ ! -d .git ] && git init && git add . && git commit -m "Initial commit"
git config user.name >/dev/null || git config user.name "APEX Bot"
git config user.email >/dev/null || git config user.email "apex@evolution.local"

# Clean up old iteration branches (keep last 5)
git branch | grep -E "iteration-[0-9]+-" | sort -V | head -n -5 | xargs -r git branch -D 2>/dev/null || true

# Ensure we're on main/master
MAIN_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
git checkout $MAIN_BRANCH 2>/dev/null || git checkout -b main

# Handle uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo "📦 Stashing uncommitted changes..."
    git stash push -m "Pre-iteration-$((ITER+1)) WIP"
    STASHED=true
fi

# Create iteration branch
BRANCH="iteration-$((ITER+1))-$MODE"
git checkout -b "$BRANCH"
git tag -a "checkpoint-$ITER" -m "Checkpoint before iteration $((ITER+1))" 2>/dev/null || true

# Capture BEFORE metrics
echo "📏 Capturing metrics..."
BEFORE_LOC=$(find . -type f -name "${FILE_PATTERN:-*.*}" -not -path "./.git/*" -not -path "*/node_modules/*" -not -path "*/venv/*" -not -path "*/dist/*" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)
BEFORE_TODOS=$(grep -r "TODO\|FIXME" . --include="${FILE_PATTERN:-*.*}" --exclude-dir={.git,node_modules,dist,build,target,venv} 2>/dev/null | wc -l)
BEFORE_COV=$($COVERAGE_CMD 2>&1 | grep -oE "${COVERAGE_PATTERN:-[0-9]+\.?[0-9]*}" | head -1 | tr -d '%' || echo 0)
BEFORE_TESTS=$PASSES

# Identify problem areas
ERROR_TYPE=$(echo "$TEST_OUTPUT" | grep -E "${TEST_FAIL_PATTERN:-Error|Failed|FAIL}" | head -1 | cut -d: -f1)
TROUBLE_FILES=$(git log --format="" --name-only --grep="fix\|bug" 2>/dev/null | grep -E "${FILE_PATTERN:-.*}" | sort | uniq -c | sort -nr | head -5 | awk '{print $2}')

# Intelligent rotation based on health and history
LAST_FOCUS=$(git log --oneline -3 --grep="Focus:" | grep -oE 'frontend|backend|database|testing|docs|security|devops|a11y|logging|refactor' | head -1)
ASPECTS="frontend backend database testing docs security devops a11y logging refactor"

# Priority overrides
NEXT_FOCUS=""
[ $FAILS -gt 5 ] && NEXT_FOCUS="testing"
[ $SECURITY -gt 0 ] && NEXT_FOCUS="security"
[ -z "$NEXT_FOCUS" ] && NEXT_FOCUS=$(echo $ASPECTS | tr ' ' '\n' | grep -v "$LAST_FOCUS" | head -1)
[ -z "$NEXT_FOCUS" ] && NEXT_FOCUS="backend"

echo ""
echo "🔍 Analysis"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Iteration: #$((ITER+1)) | Mode: $MODE | Branch: $BRANCH"
echo "Health: $HEALTH/100 | Focus: $NEXT_FOCUS"
echo "Critical Issues: $FAILS failing tests, $SECURITY security issues"
echo ""
echo "🎯 Priorities"
case $MODE in
    RECOVERY)
        echo "1. Fix critical failures only"
        echo "2. No new features or refactoring"
        echo "3. Web search all persistent/unknown errors"
        ;;
    STANDARD)
        echo "1. Fix 1-2 critical issues (80% time)"
        echo "2. Add 1 small improvement (20% time)"
        [ -n "$ERROR_TYPE" ] && echo "3. Focus on: $ERROR_TYPE"
        ;;
    FEATURE)
        echo "1. Add NEW feature with tests (80% time)"
        echo "2. Critical fixes only (20% time)"
        echo "3. Web search: competitors, trends, user needs"
        ;;
    ARCHITECTURE)
        echo "1. Review and update PROJECT_CONTEXT.md"
        echo "2. Analyze patterns in FAILED_ATTEMPTS.md"
        echo "3. Refactor repeated code (3+ occurrences)"
        echo "4. Major structural improvements"
        ;;
esac

# Save state for AI
cat > .apex_state << EOF
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
BRANCH=$BRANCH
MAIN_BRANCH=$MAIN_BRANCH
START_TIME=$START_TIME
STASHED=${STASHED:-false}
EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "State saved to .apex_state"
echo "AI should now implement based on MODE=$MODE and FOCUS=$NEXT_FOCUS"
echo "After implementation, run: ./apex_complete.sh"