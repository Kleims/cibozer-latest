#!/usr/bin/env python
"""
ZERO INPUT COMMAND - Just run it, agents figure out everything
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from self_directed_system import work, work_all_day

if __name__ == "__main__":
    print("\n" + "="*60)
    print("AUTONOMOUS AGENT SYSTEM")
    print("No input needed - I'll figure out what to do")
    print("="*60)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "all":
            # Work on multiple tasks
            print("\nMode: CONTINUOUS (will work on multiple tasks)")
            work_all_day()
        else:
            # Single task mode
            print("\nMode: SINGLE TASK")
            work()
    else:
        # Default - work on one task
        print("\nMode: SINGLE TASK")
        work()