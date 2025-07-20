#!/bin/bash

# Document failure script for iteration tracking
# Usage: ./document_failure.sh <ERROR_TYPE> <PRIORITY>

ERROR_TYPE="${1:-Unknown Error}"
PRIORITY="${2:-MEDIUM}"
ITER=$(cat .iteration 2>/dev/null || echo 0)

# Count similar failures
SIMILAR=$(grep -c "$ERROR_TYPE" FAILED_ATTEMPTS.md 2>/dev/null || echo 0)

# Get current branch and mode
BRANCH=$(git branch --show-current)
MODE=$(echo $BRANCH | grep -oE "(STANDARD|AGGRESSIVE|FEATURE)" || echo "STANDARD")

# Document the failure
cat >> FAILED_ATTEMPTS.md << EOF
## Iteration #$((ITER+1)) - $(date '+%Y-%m-%d %H:%M:%S')
**Issue**: $ERROR_TYPE
**Mode**: $MODE
**Branch**: $BRANCH
**Tried**: 
  - [List specific solutions attempted]
  - [Include commands/approaches used]
**Blocked by**: 
  - [Root cause analysis]
  - [Missing dependencies/permissions/etc]
**Priority**: $PRIORITY
**Occurrences**: $((SIMILAR+1))
**Impact**: 
  - Tests affected: $(grep -c "FAIL" test_results.log 2>/dev/null || echo "N/A")
  - Build status: $([ -f build.log ] && tail -1 build.log || echo "Unknown")
---
EOF

# Add TODO in relevant files based on error type
if [[ "$ERROR_TYPE" == *"test"* ]]; then
    TROUBLE_FILE=$(grep -l "FAIL" tests/*.py 2>/dev/null | head -1)
elif [[ "$ERROR_TYPE" == *"build"* ]]; then
    TROUBLE_FILE=$(find . -name "*.js" -o -name "*.py" | head -1)
else
    TROUBLE_FILE=$(git diff --name-only 2>/dev/null | head -1)
fi

if [ -n "$TROUBLE_FILE" ]; then
    # Add TODO comment to the file
    echo -e "\n// TODO(Iter $((ITER+1))): $ERROR_TYPE - Priority: $PRIORITY - see FAILED_ATTEMPTS.md" >> "$TROUBLE_FILE"
    echo "Added TODO to: $TROUBLE_FILE"
fi

# Create failure summary for quick reference
echo "$((ITER+1))|$(date +%Y%m%d)|$ERROR_TYPE|$PRIORITY|$((SIMILAR+1))" >> .failure_summary.csv

# Trigger web search if conditions met
if [ $((SIMILAR+1)) -ge 2 ] || [ "$PRIORITY" = "HIGH" ]; then
    echo "⚠️  Web search recommended: $ERROR_TYPE has occurred $((SIMILAR+1)) times"
    echo "SEARCH_NEEDED: $ERROR_TYPE" >> .search_queue
fi

echo "✅ Failure documented in FAILED_ATTEMPTS.md"
echo "📊 This is occurrence #$((SIMILAR+1)) of '$ERROR_TYPE'"
echo "🔍 Priority set to: $PRIORITY"