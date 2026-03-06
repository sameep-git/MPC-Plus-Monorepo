"""
Overview: 
    This script processes all folders within a given directory location,
    invoking DataProcessor on each folder to reingest data into the database.
    It is designed for batch processing of multiple beam test result directories.
    Optionally, ingestion can be restricted to specific beam type(s) by passing
    one or more beam variant names via --beam-types.
    
Usage:
<<<<<<< HEAD:backend/src/data_manipulation/ETL/scripts/Reingest.py
    python -m src.data_manipulation.ETL.scripts.Reingest <folder_path>
    
    Examples:
        python -m src.data_manipulation.ETL.scripts.Reingest data/csv_data
        python -m src.data_manipulation.ETL.scripts.Reingest /path/to/beam/data
        python -m src.data_manipulation.ETL.scripts.Reingest data/csv_data --test
=======
    python -m src.data_manipulation.ETL.Reingest <folder_path> [options]
    
    Examples:
        python -m src.data_manipulation.ETL.Reingest data/csv_data
        python -m src.data_manipulation.ETL.Reingest /path/to/beam/data
        python -m src.data_manipulation.ETL.Reingest data/csv_data --test
        python -m src.data_manipulation.ETL.Reingest data/csv_data --beam-types 6xFFF 10x
        python -m src.data_manipulation.ETL.Reingest data/csv_data --beam-types 2.5x --test
>>>>>>> 5951320 (reingest changed to have type argument):backend/src/data_manipulation/ETL/Reingest.py
    
Options:
    -h, --help                  Show this help message and exit
    --test                      Run in test mode (RunTest()) instead of upload mode (Run())
    --beam-types <type> [...]   Only ingest folders whose name contains one of the
                                specified beam type strings. If omitted, all folders
                                are ingested regardless of beam type.

Valid beam variants:
    10x, 16e, 6xMVkVEnhancedCouch, 12e, 15x, 9e, 2.5x, 6e, 6xFFF
"""

from src.data_manipulation.ETL.DataProcessor import DataProcessor
import os
import argparse
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv, find_dotenv


def main():
    # Configure logging to console
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(
        description="Batch process all folders in a directory using DataProcessor.",
        usage="python -m src.data_manipulation.ETL.scripts.Reingest <folder_path> [options]"
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
    
    # Valid beam variants that can be specified for filtering.
    VALID_BEAM_TYPES = [
        "10x", "16e", "6xMVkVEnhancedCouch", "12e",
        "15x", "9e", "2.5x", "6e", "6xFFF"
    ]
    
    parser.add_argument(
        '--beam-types',
        nargs='+',
        metavar='BEAM_TYPE',
        default=None,
        help=(
            "Only ingest folders whose name contains one of the given beam type strings. "
            "Multiple types may be space-separated (e.g. --beam-types 6xFFF 10x). "
            f"Valid variants: {', '.join(VALID_BEAM_TYPES)}. "
            "If omitted, all folders are ingested."
        )
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv(find_dotenv())
    
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
    if args.beam_types:
        logger.info(f"Beam type filter active — only ingesting: {', '.join(args.beam_types)}")
    else:
        logger.info("Beam type filter: none (all beam types will be ingested)")
    
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
    
    # When --beam-types is provided, filter to only folders whose name contains
    # at least one of the requested beam type strings (case-sensitive match).
    # If --beam-types is omitted (None), all subfolders are processed.
    if args.beam_types:
        sorted_folders = [
            f for f in sorted_folders
            if any(bt in f.name for bt in args.beam_types)
        ]
        logger.info(
            f"After beam-type filtering: {len(sorted_folders)} / {total_folders} "
            f"folder(s) match the requested beam type(s)"
        )
        # Update total count to reflect the filtered set
        total_folders = len(sorted_folders)
    start_processing = False
    
    # RESUME_FROM_FOLDER = Path(r"E:\MPC Data\Weatherford\NDS-WKS-SN6543-2025-10-07-07-14-25-0008-GeometryCheckTemplate6xMVkVEnhancedCouch").resolve()
    # for idx, subfolder in enumerate(sorted_folders, start=121):
    #     if subfolder.resolve() == RESUME_FROM_FOLDER:
    #         start_processing = True
    #         logger.info(f"Resuming from folder: {subfolder.name}")
    #     if not start_processing:
    #         continue
    for idx, subfolder in enumerate(sorted(subfolders), start=1):
        subfolder_path = str(subfolder)
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

