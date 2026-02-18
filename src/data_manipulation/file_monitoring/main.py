#!/usr/bin/env python3
"""
MPC-Plus Main Entry Point

This is the main entry point for the MPC-Plus system. It provides a simple
command-line interface to start the folder monitoring service and other
system components.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the Python path
# This file is at: MPC-Plus/src/data_manipulation/file_monitoring/main.py
# We want to add: MPC-Plus/ to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_manipulation.file_monitoring.folder_monitor import FolderMonitor
from src.data_manipulation.file_monitoring.run_monitor_service import MonitorService, install_dependencies

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_banner():
    """Print the MPC-Plus banner"""
    print("=" * 50)
    print("    MPC-Plus - Medical Physics Console Plus")
    print("    Automated Data Processing System")
    print("=" * 50)
    print()

def start_monitor(idrive_path="iDrive", background=False, lexar=False):
    """
    Start the folder monitor
    
    Args:
        idrive_path (str): Path to monitor (or 'lexar' for Lexar drive)
        background (bool): Whether to run in background
        lexar (bool): Whether to monitor Lexar drive locations
    """
    try:
        # Handle Lexar drive monitoring
        if lexar or idrive_path.lower() == 'lexar':
            lexar_base = "/Volumes/Lexar/MPC Data"
            paths = [
                os.path.join(lexar_base, "Arlington"),
                os.path.join(lexar_base, "Weatherford")
            ]
            
            # Check if paths exist
            existing_paths = [p for p in paths if os.path.exists(p)]
            if not existing_paths:
                logger.error(f"Lexar drive paths not found. Expected: {paths}")
                logger.error("Please ensure the Lexar drive is mounted and contains 'MPC Data/Arlington' and 'MPC Data/Weatherford' folders")
                sys.exit(1)
            
            print(f"Starting folder monitor for Lexar drive locations:")
            for path in existing_paths:
                print(f"  - {path}")
            
            if background:
                logger.warning("Background mode with multiple paths not fully supported. Using direct mode.")
            
            # Direct monitoring mode for multiple paths
            monitor = FolderMonitor(existing_paths)
            monitor.scan_existing_folders()
            monitor.start_monitoring()
        else:
            # Single path monitoring
            print(f"Starting folder monitor for: {os.path.abspath(idrive_path)}")
            
            # Load PostgreSQL credentials from environment
            postgres_host = os.getenv('POSTGRES_HOST')
            postgres_database = os.getenv('POSTGRES_DATABASE')
            postgres_user = os.getenv('POSTGRES_USER')
            
            if postgres_host and postgres_database and postgres_user:
                print("✓ PostgreSQL credentials loaded - uploads enabled")
            else:
                print("⚠ No PostgreSQL credentials - uploads disabled")
                print("  Set POSTGRES_HOST, POSTGRES_DATABASE, POSTGRES_USER, and POSTGRES_PASSWORD in .env to enable uploads")
            
            if background:
                # Use the service runner for background mode
                service = MonitorService()
                service.start_background()
            else:
                # Direct monitoring mode
                monitor = FolderMonitor(idrive_path)
                monitor.scan_existing_folders()
                monitor.start_monitoring()
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        logger.error(f"Error starting monitor: {str(e)}")
        sys.exit(1)

def setup_system():
    """
    Set up the MPC-Plus system
    """
    print("Setting up MPC-Plus system...")
    
    # Install dependencies
    if not install_dependencies():
        print("ERROR: Failed to install dependencies")
        return False
    
    # Create default iDrive folder if it doesn't exist
    idrive_path = "iDrive"
    if not os.path.exists(idrive_path):
        print(f"Creating iDrive folder: {os.path.abspath(idrive_path)}")
        os.makedirs(idrive_path, exist_ok=True)
    
    # Create logs directory
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        print(f"Creating logs directory: {os.path.abspath(logs_dir)}")
        os.makedirs(logs_dir, exist_ok=True)
    
    print("System setup completed successfully!")
    print()
    print("You can now start the monitor with:")
    print("  python -m src.data_manipulation.file_monitoring.main start")
    return True

def main():
    """
    Main entry point
    """
    parser = argparse.ArgumentParser(
        description='MPC-Plus - Medical Physics Console Plus',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/main.py setup           # Set up the system
  python src/main.py start           # Start folder monitoring
  python src/main.py start --path custom_folder  # Monitor custom folder
  python src/main.py start --lexar   # Monitor Lexar drive (Arlington & Weatherford)
  python src/main.py start --background          # Run in background
  python -m src.data_manipulation.file_monitoring.main start --lexar
        """
    )
    
    parser.add_argument('command', choices=['setup', 'start', 'status'], 
                       help='Command to execute')
    parser.add_argument('--path', '-p', default='iDrive',
                       help='Path to monitor (default: iDrive, or use "lexar" for Lexar drive)')
    parser.add_argument('--lexar', '-l', action='store_true',
                       help='Monitor Lexar drive locations (Arlington and Weatherford)')
    parser.add_argument('--background', '-b', action='store_true',
                       help='Run in background mode')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print_banner()
    
    if args.command == 'setup':
        setup_system()
    elif args.command == 'start':
        start_monitor(args.path, args.background, args.lexar)
    elif args.command == 'status':
        service = MonitorService()
        service.status()

if __name__ == "__main__":
    main()
