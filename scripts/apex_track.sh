#!/bin/bash
# APEX Tracking Helper - Ensures all metrics are properly recorded

# Function to append to METRICS.md with proper formatting
update_metrics() {
    local ITER=$1
    local MODE=$2
    local HEALTH=$3
    local FOCUS=$4
    local RESULT=$5
    local TESTS_BEFORE=$6
    local TESTS_AFTER=$7
    local COV_BEFORE=$8
    local COV_AFTER=$9
    local LOC=${10}
    local TODOS=${11}
    local DURATION=${12}
    
    cat >> METRICS.md << EOF
## Iteration #$ITER - $(date '+%Y-%m-%d %H:%M:%S')
- **Mode**: $MODE | **Health**: $HEALTH/100 | **Focus**: $FOCUS
- **Result**: $RESULT
- **Stack**: Python/Flask
- **Tests**: $TESTS_BEFORE → $TESTS_AFTER (Δ$((TESTS_AFTER - TESTS_BEFORE))) | **Coverage**: $COV_BEFORE% → $COV_AFTER% (Δ$(echo "$COV_AFTER - $COV_BEFORE" | bc)%)
- **LOC**: $LOC | **TODOs**: $TODOS
- **Duration**: ${DURATION}s
- **Changes**: See FIXES.log for details
EOF
}

# Function to record failed attempts
record_failure() {
    local ITER=$1
    local ISSUE=$2
    local PRIORITY=${3:-MEDIUM}
    
    cat >> FAILED_ATTEMPTS.md << EOF

## Iteration #$ITER - $(date '+%a, %b %d, %Y %I:%M:%S %p')
**Issue**: $ISSUE
**Priority**: $PRIORITY
---
EOF
}

# Function to update baselines if improved
update_baselines() {
    local NEW_COV=$1
    local NEW_TESTS=$2
    local NEW_LOC=$3
    
    source BASELINES.md
    
    # Update coverage if improved
    if (( $(echo "$NEW_COV > $COV" | bc -l) )); then
        sed -i "s/COV=.*/COV=$NEW_COV/" BASELINES.md
        echo "📈 Coverage baseline updated: $COV → $NEW_COV"
    fi
    
    # Update tests if improved
    if [ $NEW_TESTS -gt $TESTS ]; then
        sed -i "s/TESTS=.*/TESTS=$NEW_TESTS/" BASELINES.md
        echo "📈 Test baseline updated: $TESTS → $NEW_TESTS"
    fi
    
    # Update LOC
    sed -i "s/LOC=.*/LOC=$NEW_LOC/" BASELINES.md
}

# Function to add to FIXES.log
record_fix() {
    local ITER=$1
    local MODE=$2
    local DESCRIPTION=$3
    
    cat >> FIXES.log << EOF

[Iteration $ITER] - $(date '+%Y-%m-%d') - $MODE: $DESCRIPTION
EOF
}

# Main tracking function
track_iteration() {
    echo "📊 Updating APEX tracking files..."
    
    # Load current state
    source .apex_state 2>/dev/null || echo "Warning: .apex_state not found"
    
    # Example usage (would be called from apex_complete.sh)
    # update_metrics $ITER $MODE $HEALTH $FOCUS $RESULT ...
    # update_baselines $AFTER_COV $AFTER_TESTS $AFTER_LOC
    
    echo "✅ Tracking files updated"
}

# Export functions for use in other scripts
export -f update_metrics
export -f record_failure
export -f update_baselines
export -f record_fix

# If called directly, show usage
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    echo "APEX Tracking Helper Functions"
    echo "=============================="
    echo "Source this file to use tracking functions:"
    echo "  source scripts/apex_track.sh"
    echo ""
    echo "Available functions:"
    echo "  update_metrics ITER MODE HEALTH FOCUS RESULT ..."
    echo "  record_failure ITER ISSUE [PRIORITY]"
    echo "  update_baselines NEW_COV NEW_TESTS NEW_LOC"
    echo "  record_fix ITER MODE DESCRIPTION"
fi