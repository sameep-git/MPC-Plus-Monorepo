#!/usr/bin/env python3
"""
Service Runner for MPC-Plus Folder Monitor

This script helps run the folder monitor as a background service on Windows.
It provides options for running as a regular background process or installing 
as a Windows service.
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

class MonitorService:
    """
    Service wrapper for the folder monitor
    """
    
    def __init__(self):
        self.process = None
        self.is_running = False
    
    def start_background(self):
        """
        Start the monitor in background mode
        """
        try:
            # Get the path to the monitor script
            script_dir = Path(__file__).parent
            monitor_script = script_dir / "folder_monitor.py"
            
            print(f"Starting MPC-Plus Folder Monitor...")
            print(f"Monitor script: {monitor_script}")
            print(f"Working directory: {script_dir.parent}")
            
            # Change to the project root directory
            os.chdir(script_dir.parent)
            
            # Start the monitor process
            self.process = subprocess.Popen(
                [sys.executable, str(monitor_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.is_running = True
            print(f"Folder Monitor started with PID: {self.process.pid}")
            print("Monitor is running in background...")
            print("Press Ctrl+C to stop the service")
            
            # Monitor the process and output logs
            self._monitor_process()
            
        except Exception as e:
            print(f"Error starting monitor service: {str(e)}")
            sys.exit(1)
    
    def _monitor_process(self):
        """
        Monitor the running process and handle output
        """
        try:
            while self.is_running and self.process.poll() is None:
                # Read output line by line
                output = self.process.stdout.readline()
                if output:
                    print(f"[MONITOR] {output.strip()}")
                time.sleep(0.1)
            
            # Process has ended
            if self.process.poll() is not None:
                print(f"Monitor process ended with return code: {self.process.poll()}")
                self.is_running = False
                
        except KeyboardInterrupt:
            print("\nReceived interrupt signal...")
            self.stop()
        except Exception as e:
            print(f"Error monitoring process: {str(e)}")
            self.stop()
    
    def stop(self):
        """
        Stop the monitor service
        """
        if self.process and self.is_running:
            print("Stopping Folder Monitor...")
            try:
                # Try graceful shutdown first
                self.process.terminate()
                
                # Wait a bit for graceful shutdown
                try:
                    self.process.wait(timeout=5)
                    print("Monitor stopped gracefully")
                except subprocess.TimeoutExpired:
                    print("Force killing monitor process...")
                    self.process.kill()
                    self.process.wait()
                    print("Monitor force stopped")
                    
            except Exception as e:
                print(f"Error stopping monitor: {str(e)}")
            
            self.is_running = False
    
    def status(self):
        """
        Check the status of the monitor service
        """
        if self.process and self.process.poll() is None:
            print(f"Monitor is running (PID: {self.process.pid})")
            return True
        else:
            print("Monitor is not running")
            return False

def install_dependencies():
    """
    Install required Python dependencies
    """
    try:
        print("Installing dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {str(e)}")
        return False

def main():
    """
    Main entry point for the service runner
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='MPC-Plus Folder Monitor Service')
    parser.add_argument('command', choices=['start', 'stop', 'status', 'install-deps'], 
                       help='Service command')
    parser.add_argument('--background', '-b', action='store_true',
                       help='Run in background mode (default)')
    
    args = parser.parse_args()
    
    service = MonitorService()
    
    if args.command == 'install-deps':
        install_dependencies()
    elif args.command == 'start':
        print("=== MPC-Plus Folder Monitor Service ===")
        service.start_background()
    elif args.command == 'stop':
        service.stop()
    elif args.command == 'status':
        service.status()

if __name__ == "__main__":
    main()
