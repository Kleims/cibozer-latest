#!/usr/bin/env python
"""
THE ONLY COMMAND YOU NEED
Just tell it what you want, it figures out everything else
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from autonomous_agent import do

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # You gave it a task
        task = " ".join(sys.argv[1:])
        print(f"\nProcessing: {task}\n")
        result = do(task)
    else:
        # No task given - it checks for pending work automatically
        print("\nChecking for pending work...\n")
        result = do()
        
        if not result:
            print("\nNo pending work. Give me a task!")
            print("\nUsage:")
            print('  /run python agents/do.py "what you want done"')
            print("\nExamples:")
            print('  /run python agents/do.py "fix the login bug"')
            print('  /run python agents/do.py "add dark mode"')
            print('  /run python agents/do.py "deploy to production"')
            print('  /run python agents/do.py "optimize database queries"')