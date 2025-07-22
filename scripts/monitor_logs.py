#!/usr/bin/env python3
"""Real-time log monitor"""

import time
import os
from datetime import datetime

log_file = "logs/cibozer_20250718.log"

# Get initial file size
last_position = os.path.getsize(log_file)
print(f"Starting log monitor at {datetime.now()}")
print(f"Monitoring: {log_file}")
print(f"Initial position: {last_position}")
print("-" * 80)

while True:
    try:
        # Check current file size
        current_size = os.path.getsize(log_file)
        
        if current_size > last_position:
            # New data available
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(last_position)
                new_lines = f.read()
                if new_lines:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] New log entries:")
                    print(new_lines, end='')
                last_position = current_size
        elif current_size < last_position:
            # File was truncated/rotated
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Log file rotated/truncated")
            last_position = 0
            
    except FileNotFoundError:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Log file not found")
    except KeyboardInterrupt:
        print("\nStopping log monitor")
        break
    except Exception as e:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
    
    time.sleep(0.5)  # Check every 500ms