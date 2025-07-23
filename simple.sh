#!/bin/bash

# APEX Simple - One command, consistent results

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

case "$1" in
    "complete")
        if [ -z "$2" ]; then
            echo "Usage: $0 complete <iteration_number>"
            exit 1
        fi
        python apex_simple.py complete $2
        ;;
        
    "history")
        python apex_simple.py history
        ;;
        
    "help"|"--help"|"-h")
        echo -e "${BLUE}APEX Simple - Lean Iteration System${NC}"
        echo
        echo "Usage:"
        echo "  $0              # Run new iteration (default)"
        echo "  $0 complete N   # Complete iteration N"  
        echo "  $0 history      # Show iteration history"
        echo
        echo "One command, consistent results, real progress."
        ;;
        
    *)
        # Default - run iteration
        echo -e "${GREEN}Starting APEX Simple iteration...${NC}\n"
        python apex_simple.py
        ;;
esac