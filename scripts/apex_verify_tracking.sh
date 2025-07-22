#!/bin/bash
# Verify APEX tracking files are properly maintained

echo "🔍 APEX Tracking Files Verification"
echo "==================================="

# Check if files exist
FILES="METRICS.md FAILED_ATTEMPTS.md PROJECT_CONTEXT.md BASELINES.md FIXES.log .iteration"
MISSING=""

for file in $FILES; do
    if [ ! -f "$file" ]; then
        MISSING="$MISSING $file"
    fi
done

if [ -n "$MISSING" ]; then
    echo "⚠️  Missing files:$MISSING"
    echo "Run 'apex.sh' to initialize missing files"
else
    echo "✅ All tracking files present"
fi

echo ""
echo "📊 Current Status:"
echo "-----------------"

# Show current iteration
if [ -f .iteration ]; then
    echo "Iteration: $(cat .iteration)"
fi

# Show baselines
if [ -f BASELINES.md ]; then
    echo ""
    echo "Baselines:"
    cat BASELINES.md | sed 's/^/  /'
fi

# Show last metric entry
if [ -f METRICS.md ]; then
    echo ""
    echo "Last Metric Entry:"
    tail -n 15 METRICS.md | head -n 10 | sed 's/^/  /'
fi

# Count entries
echo ""
echo "📈 Statistics:"
echo "--------------"
if [ -f METRICS.md ]; then
    TOTAL_ITERATIONS=$(grep -c "^## Iteration" METRICS.md)
    SUCCESS_COUNT=$(grep -c "Result: SUCCESS" METRICS.md)
    FAILED_COUNT=$(grep -c "Result: FAILED" METRICS.md)
    echo "Total Iterations: $TOTAL_ITERATIONS"
    echo "Successful: $SUCCESS_COUNT"
    echo "Failed: $FAILED_COUNT"
fi

if [ -f FAILED_ATTEMPTS.md ]; then
    HIGH_PRIORITY=$(grep -c "Priority: HIGH" FAILED_ATTEMPTS.md)
    echo "High Priority Issues: $HIGH_PRIORITY"
fi

if [ -f FIXES.log ]; then
    TOTAL_FIXES=$(grep -c "^\[Iteration" FIXES.log)
    echo "Total Fixes Logged: $TOTAL_FIXES"
fi

echo ""
echo "✨ Tracking system is ready for use!"