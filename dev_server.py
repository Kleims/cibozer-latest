#!/usr/bin/env python
"""
Development server manager for Cibozer
Handles proper startup/shutdown and log rotation
"""

import os
import sys
import signal
import subprocess
import time
import psutil
from pathlib import Path

class CibozerDevServer:
    def __init__(self):
        self.app_process = None
        self.app_dir = Path(__file__).parent
        self.log_dir = self.app_dir / 'logs'
        
    def cleanup_logs(self):
        """Clean up log files to prevent rotation issues"""
        print("Cleaning up log files...")
        
        # Create logs directory if it doesn't exist
        self.log_dir.mkdir(exist_ok=True)
        
        # Handle the main log file
        main_log = self.log_dir / 'cibozer.log'
        if main_log.exists():
            # Find next available backup number
            i = 1
            while (self.log_dir / f'cibozer.log.backup{i}').exists():
                i += 1
            main_log.rename(self.log_dir / f'cibozer.log.backup{i}')
            print(f"  Moved existing log to cibozer.log.backup{i}")
    
    def check_existing_processes(self):
        """Check if app is already running"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] == 'python.exe' or proc.info['name'] == 'python':
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'app.py' in cmdline and str(self.app_dir) in cmdline:
                        return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return None
    
    def start(self):
        """Start the development server"""
        print("=" * 60)
        print("  Cibozer Development Server Manager")
        print("=" * 60)
        print()
        
        # Check if already running
        existing = self.check_existing_processes()
        if existing:
            print(f"ERROR: Cibozer is already running (PID: {existing.pid})")
            print("Run 'python dev_server.py stop' to stop it first.")
            return False
        
        # Clean up logs
        self.cleanup_logs()
        
        # Set environment variables
        env = os.environ.copy()
        env['FLASK_ENV'] = 'development'
        env['FLASK_DEBUG'] = '1'
        
        print("Starting Cibozer...")
        print()
        print("  Admin Panel: http://localhost:5001/admin")
        print("  Main App:    http://localhost:5001")
        print()
        print("Press Ctrl+C to stop the server")
        print("=" * 60)
        print()
        
        try:
            # Start the app
            self.app_process = subprocess.Popen(
                [sys.executable, 'app.py'],
                env=env,
                cwd=str(self.app_dir)
            )
            
            # Wait for process
            self.app_process.wait()
            
        except KeyboardInterrupt:
            print("\n\nShutting down gracefully...")
            self.stop()
        except Exception as e:
            print(f"\nError: {e}")
            self.stop()
            return False
        
        return True
    
    def stop(self):
        """Stop all Cibozer processes"""
        print("\nStopping Cibozer processes...")
        
        stopped_count = 0
        
        # Stop our subprocess if it exists
        if self.app_process:
            try:
                self.app_process.terminate()
                self.app_process.wait(timeout=5)
                stopped_count += 1
            except:
                self.app_process.kill()
                
        # Find and stop all app.py processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] in ['python.exe', 'python']:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'app.py' in cmdline and str(self.app_dir) in cmdline:
                        print(f"  Stopping PID {proc.info['pid']}...")
                        proc.terminate()
                        proc.wait(timeout=5)
                        stopped_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                try:
                    proc.kill()
                    stopped_count += 1
                except:
                    pass
        
        if stopped_count > 0:
            print(f"\nStopped {stopped_count} process(es).")
        else:
            print("\nNo Cibozer processes found.")
        
        return True
    
    def status(self):
        """Check server status"""
        proc = self.check_existing_processes()
        if proc:
            print(f"Cibozer is running (PID: {proc.pid})")
            print(f"Memory usage: {proc.memory_info().rss / 1024 / 1024:.1f} MB")
        else:
            print("Cibozer is not running.")

def main():
    """Main entry point"""
    server = CibozerDevServer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'start':
            server.start()
        elif command == 'stop':
            server.stop()
        elif command == 'restart':
            server.stop()
            time.sleep(2)
            server.start()
        elif command == 'status':
            server.status()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python dev_server.py [start|stop|restart|status]")
    else:
        # Default to start
        server.start()

if __name__ == '__main__':
    # Check for psutil
    try:
        import psutil
    except ImportError:
        print("ERROR: psutil is required for process management")
        print("Install it with: pip install psutil")
        sys.exit(1)
    
    main()