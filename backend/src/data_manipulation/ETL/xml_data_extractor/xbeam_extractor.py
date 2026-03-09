"""
Extract relative uniformity, relative output, and center shift from x-beam Results.xml
"""

import os
import sys
import xml.etree.ElementTree as ET
import math


def is_xbeam_folder(folder_path):
    """
    Check if folder is an x-beam folder
    
    Args:
        folder_path: Path to the folder to check
        
    Returns:
        bool: True if folder name contains x-beam indicators ('15x', '6x', or 'BeamCheckTemplate')
    """
    folder_name = os.path.basename(folder_path)
    # Check for x-beam indicators in folder name
    return '15x' in folder_name or '6x' in folder_name or 'BeamCheckTemplate' in folder_name


def extract_xbeam_values(folder_path):
    """
    Extract relative output, relative uniformity, and center shift from x-beam Results.xml
    
    Args:
        folder_path: Path to the folder containing Results.xml
        
    Returns:
        tuple: (output_percentage, uniformity_percentage, center_shift_mm) or (None, None, None) if extraction fails
    """
    # Try to resolve path - if relative path doesn't exist, try relative to MPC-Plus
    if not os.path.exists(folder_path):
        # Try relative to MPC-Plus folder (common parent directory)
        # Navigate up from current script: ETL -> data_manipulation -> src -> MPC-Plus
        script_dir = os.path.dirname(os.path.abspath(__file__))
        mpc_plus_dir = os.path.abspath(os.path.join(script_dir, '../../..'))
        
        # Try multiple possible locations
        possible_paths = [
            os.path.join(mpc_plus_dir, folder_path),  # Directly in MPC-Plus
            os.path.join(mpc_plus_dir, 'data', 'csv_data', folder_path)  # In data/csv_data subdirectory
        ]
        
        found_path = None
        for alt_path in possible_paths:
            if os.path.exists(alt_path):
                found_path = alt_path
                break
        
        if found_path:
            folder_path = found_path
        else:
            print(f"Error: Folder not found: {folder_path}")
            return None, None, None
    
    # Construct path to Results.xml file
    results_path = os.path.join(folder_path, "Results.xml")
    
    # Validate that Results.xml exists
    if not os.path.exists(results_path):
        print(f"Error: Results.xml not found in {folder_path}")
        return None, None, None
    
    # Validate that this is an x-beam folder
    if not is_xbeam_folder(folder_path):
        print(f"Error: Not an x-beam folder")
        return None, None, None
    
    # Parse the XML file
    tree = ET.parse(results_path)
    root = tree.getroot()
    
    # Initialize variables to store extracted values
    relative_output = None
    relative_uniformity = None
    center_shift = None
    
    # Find BeamProfileCheck element for relative output and relative uniformity
    # XML namespaces are handled by checking the xsi:type attribute
    for elem in root.iter():
        # Check if this element is a BeamProfileCheck type
        if elem.get('{http://www.w3.org/2001/XMLSchema-instance}type') == 'BeamProfileCheck':
            # Iterate through child elements to find RelativeOutput and RelativeUniformity
            for child in elem:
                # Extract tag name by removing namespace prefix (everything before '}')
                tag = child.tag.split('}')[-1]
                if tag == 'RelativeOutput' and child.text:
                    relative_output = float(child.text.strip())
                elif tag == 'RelativeUniformity' and child.text:
                    relative_uniformity = float(child.text.strip())
            # Found the element, no need to continue searching
            break
    
    # Find JawEdgeCheck element for IsoCenter and BaselineIsoCenter coordinates
    # These are needed to calculate the center shift
    iso_x = None
    iso_y = None
    baseline_iso_x = None
    baseline_iso_y = None
    
    for elem in root.iter():
        # Check if this element is a JawEdgeCheck type
        if elem.get('{http://www.w3.org/2001/XMLSchema-instance}type') == 'JawEdgeCheck':
            # Iterate through child elements to find IsoCenter and BaselineIsoCenter
            for child in elem:
                tag = child.tag.split('}')[-1]
                if tag == 'IsoCenter':
                    # Extract X and Y coordinates from IsoCenter element
                    for coord in child:
                        coord_tag = coord.tag.split('}')[-1]
                        if coord_tag == 'X' and coord.text:
                            iso_x = float(coord.text.strip())
                        elif coord_tag == 'Y' and coord.text:
                            iso_y = float(coord.text.strip())
                elif tag == 'BaselineIsoCenter':
                    # Extract X and Y coordinates from BaselineIsoCenter element
                    for coord in child:
                        coord_tag = coord.tag.split('}')[-1]
                        if coord_tag == 'X' and coord.text:
                            baseline_iso_x = float(coord.text.strip())
                        elif coord_tag == 'Y' and coord.text:
                            baseline_iso_y = float(coord.text.strip())
            # Found the element, no need to continue searching
            break
    
    # Calculate center shift using Euclidean distance formula:
    # √[(X – X₀)² + (Y – Y₀)²] × 10
    # Where (X, Y) is IsoCenter and (X₀, Y₀) is BaselineIsoCenter
    # The result is multiplied by 10 to convert to millimeters
    if iso_x is not None and iso_y is not None and baseline_iso_x is not None and baseline_iso_y is not None:
        dx = iso_x - baseline_iso_x  # Difference in X coordinates
        dy = iso_y - baseline_iso_y  # Difference in Y coordinates
        center_shift = math.sqrt(dx * dx + dy * dy) * 10
    
    # Validate that required values were found
    if relative_output is None or relative_uniformity is None:
        return None, None, None
    
    # Convert relative values to percentages:
    # - RelativeOutput: subtract 1 and multiply by 100 (e.g., 1.02 -> 2.0%)
    # - RelativeUniformity: multiply by 100 (e.g., 0.015 -> 1.5%)
    output = (relative_output - 1) * 100
    uniformity = relative_uniformity * 100
    
    return output, uniformity, center_shift


if __name__ == "__main__":
    # Command-line interface for testing the extractor
    if len(sys.argv) < 2:
        print("Usage: xbeam_extractor.py <folder_path>")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    output, uniformity, center_shift = extract_xbeam_values(folder_path)
    
    # Display results if extraction was successful
    if output is not None and uniformity is not None:
        print(f"Relative Output: {output:.2f}%")
        print(f"Relative Uniformity: {uniformity:.2f}%")
        # Center shift is optional - may not be present in all XML files
        if center_shift is not None:
            print(f"Center Shift: {center_shift:.6f} mm")
        else:
            print("Center Shift: Not found")
    else:
        print("Failed to extract values")
        sys.exit(1)
