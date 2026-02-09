"""
Overview: 
    This script processes all folders within a given directory location,
    invoking DataProcessor on each folder to reingest data into the database.
    It is designed for batch processing of multiple beam test result directories.
    
Usage:
    python -m src.data_manipulation.ETL.Reingest <folder_path>
    
    Examples:
        python -m src.data_manipulation.ETL.Reingest data/csv_data
        python -m src.data_manipulation.ETL.Reingest /path/to/beam/data
        python -m src.data_manipulation.ETL.Reingest data/csv_data --test
    
Options:
    -h, --help      Show this help message and exit
    --test          Run in test mode (RunTest()) instead of upload mode (Run())
"""

from src.data_manipulation.ETL.DataProcessor import DataProcessor
import os
import argparse
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv


def main():
    # Configure logging to console
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(
        description="Batch process all folders in a directory using DataProcessor.",
        usage="python -m src.data_manipulation.ETL.Reingest <folder_path> [options]"
    )
    
    parser.add_argument(
        'folder_path',
        type=str,
        help="Path to the directory containing beam test result folders"
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help="Run in test mode (RunTest()) instead of upload mode (Run())"
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Validate and resolve the folder path
    folder_path = Path(args.folder_path).resolve()
    
    if not folder_path.exists():
        logger.error(f"Error: The specified path does not exist: {folder_path}")
        sys.exit(1)
    
    if not folder_path.is_dir():
        logger.error(f"Error: The specified path is not a directory: {folder_path}")
        sys.exit(1)
    
    logger.info(f"Processing all folders in: {folder_path}")
    logger.info(f"Mode: {'TEST' if args.test else 'UPLOAD'}")
    
    # Get all subdirectories
    subfolders = [d for d in folder_path.iterdir() if d.is_dir()]
    
    if not subfolders:
        logger.warning(f"No subdirectories found in: {folder_path}")
        sys.exit(0)
    
    total_folders = len(subfolders)
    logger.info(f"Found {total_folders} folder(s) to process")
    
    # Process each subfolder
    successful = 0
    failed = 0
    skipped = 0
    
    
    sorted_folders = sorted(subfolders)
    start_processing = False
    
    RESUME_FROM_FOLDER = Path(r"E:\MPC Data\Weatherford\NDS-WKS-SN6543-2025-10-07-07-14-25-0008-GeometryCheckTemplate6xMVkVEnhancedCouch").resolve()
    for idx, subfolder in enumerate(sorted_folders, start=121):
        subfolder_path = str(subfolder)
        if subfolder.resolve() == RESUME_FROM_FOLDER:
            start_processing = True
            logger.info(f"Resuming from folder: {subfolder.name}")
        if not start_processing:
            continue
    # for idx, subfolder in enumerate(sorted(subfolders), start=486):
    #     subfolder_path = str(subfolder)
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing folder {idx} out of {total_folders}: {subfolder.name}")
        print(f"Processing folder {idx} out of {total_folders}: {subfolder.name}")
        logger.info(f"Full path: {subfolder_path}")
        logger.info(f"{'='*80}")
        
        # Check if the folder contains required files
        results_csv = subfolder / "Results.csv"
        beam_profile = subfolder / "BeamProfileCheck.xim"
        
        if not results_csv.exists():
            logger.warning(f"Skipping {subfolder.name}: Results.csv not found")
            skipped += 1
            continue
        
        if not beam_profile.exists():
            logger.warning(f"Skipping {subfolder.name}: BeamProfileCheck.xim not found")
            skipped += 1
            continue
        
        try:
            dp = DataProcessor(subfolder_path)
            
            if args.test:
                logger.info("Running in TEST mode...")
                dp.RunTest()
            else:
                logger.info("Running in UPLOAD mode...")
                dp.Run()
            
            logger.info(f"✓ Successfully processed: {subfolder.name}")
            successful += 1
            
        except Exception as e:
            logger.error(f"✗ ERROR processing {subfolder.name}: {e}", exc_info=True)
            failed += 1
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("PROCESSING SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Total folders: {len(subfolders)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Skipped: {skipped}")
    logger.info(f"{'='*80}")


if __name__ == "__main__":
    main()

