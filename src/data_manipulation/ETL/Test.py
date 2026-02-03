"""
Overview: 
    This script serves as a simple driver to invoke the DataProcessor on 
    a single dataset directory. It is primarily intended for local testing, 
    validation, or debugging of the data extraction pipeline.
    This script serves as a driver to invoke the DataProcessor on 
    dataset directories using command line arguments.
    
Usage:
    1) Update the `path` variable below to point to a directory containing 
       beam test results (a Results.csv file is expected inside).
    2) Run this script directly to process that dataset.
    python -m src.data_manipulation.ETL.Test [options]
    
    Examples:
        python -m src.data_manipulation.ETL.Test -csv -6e
        python -m src.data_manipulation.ETL.Test -csv -xbeams -upload
        python -m src.data_manipulation.ETL.Test -csv (tests all beams defined in paths)
Command:
    python -m src.data_manipulation.ETL.Test
Options:
    -h, --help      Show this help message and exit
    -csv            Use CSV data source (data/csv_data)
    -xml            Use XML data source (data/xml_data) [Not implemented yet, placeholder]
    -upload         Upload to database (uses Run() instead of RunTest())
    
    Beam Selection Groups:
    -xbeams         Test all X-Ray beams (2_5x, 10x, 15x, 6xFFF)
    -ebeams         Test all Electron beams (6e, 9e, 12e, 16e)
    -geo            Test the Geometry Check beam (6x/6xMVkVEnhancedCouch)
    
    Individual Beams:
    -6e, -9e, -12e, -16e
    -2_5x, -10x, -15x
    -6xFFF
""" 
from src.data_manipulation.ETL.DataProcessor import DataProcessor
import os
import argparse
import logging
import sys
from dotenv import load_dotenv
from src.data_manipulation.ETL.DataProcessor import DataProcessor
# =============================================================================
# DATA PATH CONFIGURATION
# Update these paths to point to your specific data folders.
# =============================================================================
# --- CSV DATA PATHS ---
CSV_PATH_6E = r"data/csv_data/NDS-WKS-SN6543-2025-09-19-07-41-49-0004-BeamCheckTemplate6e"
CSV_PATH_9E = r"data/csv_data/Placeholder_9e"
CSV_PATH_12E = r"data/csv_data/NDS-WKS-SN6543-2025-09-19-07-41-49-0006-BeamCheckTemplate12e"
CSV_PATH_16E = r"data/csv_data/NDS-WKS-SN6543-2025-09-19-07-41-49-0007-BeamCheckTemplate16e"
CSV_PATH_2_5X = r"data/csv_data/NDS-WKS-SN6543-2015-09-18-08-06-01-0000-BeamCheckTemplate2_5x"
CSV_PATH_10X = r"data/csv_data/Placeholder_10x"
CSV_PATH_15X = r"data/csv_data/NDS-WKS-SN6543-2025-09-19-07-41-49-0003-BeamCheckTemplate15x"
CSV_PATH_6xFFF = r"data/csv_data/NDS-WKS-SN6543-2025-09-19-07-41-49-0001-BeamCheckTemplate6xFFF"
CSV_PATH_GEO = r"data/csv_data/NDS-WKS-SN6543-2025-09-19-07-41-49-0008-GeometryCheckTemplate6xMVkVEnhancedCouch"
# --- XML DATA PATHS ---
XML_PATH_6E = r"data/xml_data/Placeholder_6e"
XML_PATH_9E = r"data/xml_data/Placeholder_9e"
XML_PATH_12E = r"data/xml_data/Placeholder_12e"
XML_PATH_16E = r"data/xml_data/Placeholder_16e"
XML_PATH_2_5X = r"data/xml_data/Placeholder_2_5x"
XML_PATH_10X = r"data/xml_data/Placeholder_10x"
XML_PATH_15X = r"data/xml_data/Placeholder_15x"
XML_PATH_6xFFF = r"data/xml_data/Placeholder_6xFFF"
XML_PATH_GEO = r"data/xml_data/Placeholder_Geo"
def get_beam_paths(use_csv=True):
    """Returns a dictionary mapping beam keys to their configured paths."""
    if use_csv:
        return {
            '6e': CSV_PATH_6E,
            '9e': CSV_PATH_9E,
            '12e': CSV_PATH_12E,
            '16e': CSV_PATH_16E,
            '2_5x': CSV_PATH_2_5X,
            '10x': CSV_PATH_10X,
            '15x': CSV_PATH_15X,
            '6xFFF': CSV_PATH_6xFFF,
            'geo': CSV_PATH_GEO
        }
    else:
        return {
            '6e': XML_PATH_6E,
            '9e': XML_PATH_9E,
            '12e': XML_PATH_12E,
            '16e': XML_PATH_16E,
            '2_5x': XML_PATH_2_5X,
            '10x': XML_PATH_10X,
            '15x': XML_PATH_15X,
            '6xFFF': XML_PATH_6xFFF,
            'geo': XML_PATH_GEO
        }
def main():
    # Configure logging to console if not already configured
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
    
    parser = argparse.ArgumentParser(
        description="Run DataProcessor extraction tests.",
        usage="python -m src.data_manipulation.ETL.Test [options]"
    )
    
    # Data Source Options
    source_group = parser.add_argument_group('Data Source (One required)')
    source_group.add_argument('-csv', action='store_true', help="Use Configured CSV Paths")
    source_group.add_argument('-xml', action='store_true', help="Use Configured XML Paths")
    # Mode Options
    parser.add_argument('-upload', action='store_true', help="Upload results to DB (Run()) instead of Test mode (RunTest())")
    # Beam Selection Options
    beam_group = parser.add_argument_group('Beam Selection')
    beam_group.add_argument('-xbeams', action='store_true', help="Test all X-Ray beams")
    beam_group.add_argument('-ebeams', action='store_true', help="Test all Electron beams")
    beam_group.add_argument('-geo', action='store_true', help="Test Geometry Check")
    
    individual_beams = ['6e', '9e', '12e', '16e', '2_5x', '10x', '15x', '6xFFF']
    for beam in individual_beams:
        beam_group.add_argument(f'-{beam}', action='store_true', help=f"Test {beam} beam")
    # If no arguments provided, print help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args()
    # Validate Data Source
    if not args.csv and not args.xml:
        print("Error: You must specify either -csv or -xml.")
        parser.print_help()
        sys.exit(1)
        
    load_dotenv()
    # Determine which beams to run
    beam_flags_set = (
        args.xbeams or args.ebeams or args.geo or 
        #any(getattr(args, f.replace('.', '_')) for f in ["2_5x"]) or 
        any(getattr(args, b) for b in individual_beams)
    )
    
    target_beam_keys = set()
    
    if not beam_flags_set:
        print("No specific beams selected. Testing ALL configured beams.")
        target_beam_keys.update(individual_beams)
        target_beam_keys.add('geo')
    else:
        # Groups
        if args.xbeams:
            target_beam_keys.update(['2_5x', '10x', '15x', '6xFFF'])
        if args.ebeams:
            target_beam_keys.update(['6e', '9e', '12e', '16e'])
        if args.geo:
            target_beam_keys.add('geo')
            
        # Individuals
        args_dict = vars(args)
        if args_dict.get('6e'): target_beam_keys.add('6e')
        if args_dict.get('9e'): target_beam_keys.add('9e')
        if args_dict.get('12e'): target_beam_keys.add('12e')
        if args_dict.get('16e'): target_beam_keys.add('16e')
        if args_dict.get('10x'): target_beam_keys.add('10x')
        if args_dict.get('15x'): target_beam_keys.add('15x')
        if args_dict.get('6xFFF'): target_beam_keys.add('6xFFF')
        if args_dict.get('2_5x') or args_dict.get('2_5x'): target_beam_keys.add('2_5x')
    print(f"Target Beams: {target_beam_keys}")
    
    # Get configured paths
    Available_Paths = get_beam_paths(use_csv=args.csv)
    
    # Process selected beams
    for key in target_beam_keys:
        path = Available_Paths.get(key)
        
        if not path or "Placeholder" in path:
            print(f"\nSkipping {key}: Path not configured or is placeholder ({path})")
            continue
            
        if not os.path.exists(path):
            print(f"\nSkipping {key}: Path does not exist: {path}")
            continue
        print(f"\nProcessing {key}: {path}")
        try:
            dp = DataProcessor(path)
            if args.upload:
                print("Running in UPLOAD mode...")
                dp.Run()
            else:
                print("Running in TEST mode...")
                dp.RunTest()
        except Exception as e:
            print(f"ERROR processing {key}: {e}")
if __name__ == "__main__":
    main()