#!/usr/bin/env python3
"""Check if environment files are properly set up"""

from pathlib import Path

# Check if environment files exist
env_files = ['.env', '.env.development', '.env.production']
any_exists = any(Path(f).exists() for f in env_files)

if any_exists:
    print("OK")
else:
    print("FAIL")