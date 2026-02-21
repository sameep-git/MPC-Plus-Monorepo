#!/usr/bin/env python3
"""
iDrive Folder Monitor - Entry Point for MPC-Plus Data Processing

This program monitors the 'iDrive' folder for new directory uploads and 
automatically processes them using the DataProcessor.

Author: MPC-Plus System
"""

import os
import sys
import time
import logging
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.data_manipulation.ETL.DataProcessor import DataProcessor

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Configure logging
# Ensure logs directory exists
logs_dir = Path(__file__).parent.parent.parent.parent / 'logs'
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / 'folder_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class iDriveFolderHandler(FileSystemEventHandler):
    """
    Event handler for monitoring iDrive folder changes
    """
    
    def __init__(self):
        """
        Initialize the handler
        """
        self.processed_folders = set()  # Track processed folders to avoid duplicates
        
    def on_created(self, event):
        """
        Handle file/folder creation events
        
        Args:
            event: FileSystemEvent object
        """
        if event.is_directory:
            self._process_new_folder(event.src_path)
    
    def on_moved(self, event):
        """
        Handle file/folder move events (covers uploads that appear as moves)
        
        Args:
            event: FileSystemEvent object
        """
        if event.is_directory:
            self._process_new_folder(event.dest_path)
    
    def _process_new_folder(self, folder_path):
        """
        Process a newly detected folder
        
        Args:
            folder_path (str): Path to the newly created/moved folder
        """
        try:
            # Avoid processing the same folder multiple times
            if folder_path in self.processed_folders:
                return
                
            logger.info(f"New folder detected: {folder_path}")
            
            # Add a small delay to ensure the upload is complete
            time.sleep(2)
            
            # Verify the folder still exists and contains files
            if not self._is_folder_ready(folder_path):
                logger.warning(f"Folder not ready or incomplete: {folder_path}")
                return
            
            # Mark as processed to avoid duplicates
            self.processed_folders.add(folder_path)
            
            # Create DataProcessor instance and run processing
            logger.info(f"Processing folder: {folder_path}")
            processor = DataProcessor(folder_path)
            processor.Run()
            
            logger.info(f"Successfully processed folder: {folder_path}")
            
        except Exception as e:
            logger.error(f"Error processing folder {folder_path}: {str(e)}")
            # Remove from processed set so we can retry later if needed
            self.processed_folders.discard(folder_path)
    
    def _is_folder_ready(self, folder_path):
        """
        Check if a folder is ready for processing (contains expected files)
        
        Args:
            folder_path (str): Path to check
            
        Returns:
            bool: True if folder is ready for processing
        """
        try:
            if not os.path.exists(folder_path):
                return False
                
            # Check if Results.csv exists (required by DataProcessor)
            results_csv = os.path.join(folder_path, "Results.csv")
            if not os.path.exists(results_csv):
                logger.debug(f"Results.csv not found in {folder_path}, waiting...")
                return False
            
            # Check if file is not empty and not being written to
            if os.path.getsize(results_csv) == 0:
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking folder readiness {folder_path}: {str(e)}")
            return False

class FolderMonitor:
    """
    Main folder monitoring service
    """
    
    def __init__(self, idrive_path="iDrive"):
        """
        Initialize the folder monitor
        
        Args:
            idrive_path (str or list): Path(s) to the folder(s) to monitor.
                                      Can be a single path string or a list of paths.
        """
        # Handle both single path and multiple paths
        if isinstance(idrive_path, list):
            self.idrive_paths = [os.path.abspath(p) for p in idrive_path]
        else:
            self.idrive_paths = [os.path.abspath(idrive_path)]
        
        self.observers = []  # List of observers for multiple paths
        self.handler = iDriveFolderHandler()
        self.is_running = False
        
    def start_monitoring(self):
        """
        Start monitoring the folder(s)
        """
        try:
            # Ensure all folders exist
            for path in self.idrive_paths:
                if not os.path.exists(path):
                    logger.warning(f"Folder does not exist: {path}")
                    logger.info(f"Creating folder: {path}")
                    os.makedirs(path, exist_ok=True)
            
            logger.info(f"Starting folder monitoring on {len(self.idrive_paths)} location(s):")
            for path in self.idrive_paths:
                logger.info(f"  - {path}")
            
            logger.info("Monitoring for NEW folders only (existing folders will not be processed)")
            
            # Set up observers for each path
            for path in self.idrive_paths:
                observer = Observer()
                observer.schedule(self.handler, path, recursive=True)
                observer.start()
                self.observers.append(observer)
            
            self.is_running = True
            
            logger.info("Folder monitoring started successfully")
            logger.info("Waiting for new folders to be added...")
            logger.info("Press Ctrl+C to stop monitoring")
            
            # Keep the program running
            try:
                while self.is_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, stopping...")
                self.stop_monitoring()
                
        except Exception as e:
            logger.error(f"Error starting folder monitoring: {str(e)}")
            sys.exit(1)
    
    def stop_monitoring(self):
        """
        Stop monitoring the folder(s)
        """
        if self.is_running:
            logger.info("Stopping folder monitoring...")
            for observer in self.observers:
                observer.stop()
            for observer in self.observers:
                observer.join()
            self.observers = []
            self.is_running = False
            logger.info("Folder monitoring stopped")
    
    def scan_existing_folders(self):
        """
        Scan for existing folders that might need processing.
        This method processes all existing folders in the monitored directories.
        Use the --scan-existing command-line option to invoke this on startup.
        """
        try:
            logger.info(f"Scanning for existing folders in {len(self.idrive_paths)} location(s)...")
            
            for idrive_path in self.idrive_paths:
                if not os.path.exists(idrive_path):
                    logger.info(f"Folder does not exist yet: {idrive_path}")
                    continue
                
                logger.info(f"Scanning: {idrive_path}")
                for item in os.listdir(idrive_path):
                    item_path = os.path.join(idrive_path, item)
                    if os.path.isdir(item_path):
                        logger.info(f"Found existing folder: {item_path}")
                        # Process existing folder if it hasn't been processed
                        self.handler._process_new_folder(item_path)
                    
        except Exception as e:
            logger.error(f"Error scanning existing folders: {str(e)}")

def main():
    """
    Main entry point for the folder monitor
    """
    logger.info("=== MPC-Plus iDrive Folder Monitor Starting ===")
    
    # Load PostgreSQL credentials from environment variables (if available)
    postgres_host = os.getenv('POSTGRES_HOST')
    postgres_database = os.getenv('POSTGRES_DATABASE')
    postgres_user = os.getenv('POSTGRES_USER')
    
    if postgres_host and postgres_database and postgres_user:
        logger.info("✓ PostgreSQL credentials loaded - uploads will be enabled")
    else:
        logger.info("⚠ No PostgreSQL credentials found - uploads will be disabled")
        logger.info("  Set POSTGRES_HOST, POSTGRES_DATABASE, POSTGRES_USER, and POSTGRES_PASSWORD in .env file to enable uploads")
    
    # Create and configure monitor
    monitor = FolderMonitor()
    
    # Start continuous monitoring (only processes NEW folders added while running)
    monitor.start_monitoring()

if __name__ == "__main__":
    main()
