#!/bin/bash
# APEX v4.2 - Initialize project for first run or reset

echo "🚀 Initializing APEX for Cibozer project..."

# Create required files if they don't exist
touch METRICS.md FAILED_ATTEMPTS.md PROJECT_CONTEXT.md BASELINES.md FIXES.log

# Initialize iteration counter
echo "0" > .iteration

# Set up PROJECT_CONTEXT.md with detected values
cat > PROJECT_CONTEXT.md << 'EOF'
# Project Context - Cibozer
# AI-powered meal planning SaaS platform

## Stack Details
STACK="Python/Flask"
FRAMEWORK="Flask 2.3.3"
DATABASE="SQLAlchemy with SQLite"
TESTING="pytest with coverage"
DEPLOYMENT="Gunicorn, Heroku/Render/Railway/Vercel ready"

## Commands
TEST_CMD="python -m pytest"
BUILD_CMD="pip install -r requirements.txt"
COVERAGE_CMD="python -m pytest --cov=. --cov-report=term-missing"
AUDIT_CMD="pip-audit"
FILE_PATTERN="*.py"
TEST_FAIL_PATTERN="FAILED|AssertionError|Exception|ERROR"
TEST_PASS_PATTERN="passed|PASSED"
COVERAGE_PATTERN="[0-9]+%"
LINT_CMD="python -m flake8 . --max-line-length=120 --exclude=venv,.git,__pycache__"

## Key Features
- AI Meal Planning with calorie targets
- Video generation for social media
- PDF export functionality
- Stripe payment integration
- Credit-based usage system
- Admin dashboard

## Architecture Notes
- Modular blueprint-based Flask app
- Security-focused with CSRF protection
- Centralized logging with custom loggers
- Web-safe meal optimizer wrapper
- Async video generation (needs improvement)
EOF

# Initialize baselines with current metrics
echo "🔍 Detecting current baselines..."
TEST_OUTPUT=$(python -m pytest --collect-only -q 2>&1 || true)
CURRENT_TESTS=$(echo "$TEST_OUTPUT" | grep -oE "[0-9]+ test" | grep -oE "[0-9]+" || echo 0)
CURRENT_COV=$(python -m pytest --cov=. --cov-report=term-missing 2>&1 | grep -oE "TOTAL.*[0-9]+%" | grep -oE "[0-9]+" | tail -1 || echo 30)
CURRENT_LOC=$(find . -name "*.py" -not -path "./venv/*" -not -path "./.git/*" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)

cat > BASELINES.md << EOF
# Baselines - Best achieved metrics
COV=$CURRENT_COV
PERF=5
TESTS=$CURRENT_TESTS
LOC=$CURRENT_LOC
EOF

# Initialize METRICS.md header
cat > METRICS.md << 'EOF'
# APEX Metrics History

Track evolution progress across iterations.

Format:
- **Mode**: RECOVERY | STANDARD | FEATURE | ARCHITECTURE
- **Health**: 0-100 (based on test failures and security issues)
- **Focus**: Current aspect (frontend/backend/database/testing/docs/security/devops/a11y/logging/refactor)
- **Result**: SUCCESS | PARTIAL | FAILED

---

EOF

# Initialize FAILED_ATTEMPTS.md
cat > FAILED_ATTEMPTS.md << 'EOF'
# Failed Attempts Log

Document issues that couldn't be resolved in a single iteration.

Format:
```
## Iteration #N - Date
**Issue**: Brief description
**Tried**: What solutions were attempted
**Blocked by**: Root cause
**Priority**: HIGH | ARCHITECTURAL
**Occurrences**: Number of times encountered
---
```

## Known Issues

### bcrypt import error in tests
**Issue**: ImportError: PyO3 modules compiled for CPython 3.8 or older
**Blocked by**: Environment-specific bcrypt compilation issue
**Priority**: MEDIUM
**Workaround**: Run tests in fresh environment or use bcrypt-cffi

---

EOF

# Initialize FIXES.log with header
echo "# Successful Fixes Log" > FIXES.log
echo "# Format: DATE|STACK|ERROR_TYPE|FILES_CHANGED|IMPROVEMENT" >> FIXES.log
echo "#" >> FIXES.log

# Set git config if needed
git config user.name >/dev/null || git config user.name "APEX Bot"
git config user.email >/dev/null || git config user.email "apex@evolution.local"

# Make scripts executable
chmod +x apex.sh apex_complete.sh apex_init.sh 2>/dev/null || true

echo ""
echo "✅ APEX initialization complete!"
echo ""
echo "📊 Current baselines:"
echo "   Tests: $CURRENT_TESTS"
echo "   Coverage: $CURRENT_COV%"
echo "   LOC: $CURRENT_LOC"
echo ""
echo "🎯 Next steps:"
echo "   1. Run: ./apex.sh"
echo "   2. Implement based on mode and focus"
echo "   3. Run: ./apex_complete.sh"
echo ""
echo "📚 Files created/updated:"
echo "   - PROJECT_CONTEXT.md (project configuration)"
echo "   - BASELINES.md (best metrics)"
echo "   - METRICS.md (iteration history)"
echo "   - FAILED_ATTEMPTS.md (known issues)"
echo "   - FIXES.log (successful patterns)"
echo "   - .iteration (counter at 0)"