"""
Unified extractor for MPC beam Results.xml files.

Given a path (either directly to a Results.xml file or to its containing
folder), this module:
- Detects the beam type from XML content (check types present in Results.xml)
- Calls the appropriate extractor
- Returns only the fields requested for that beam type:
  - e‑beam: relative output, relative uniformity
  - x‑beam: relative output, relative uniformity, center shift
"""

import os
import sys
import xml.etree.ElementTree as ET

try:
    # Package import (used when called from DataProcessor or any other module)
    from src.data_manipulation.ETL.xml_data_extractor.ebeam_extractor import extract_ebeam_values
    from src.data_manipulation.ETL.xml_data_extractor.xbeam_extractor import extract_xbeam_values
except ImportError:
    # Fallback for running the file directly as a script
    from ebeam_extractor import extract_ebeam_values
    from xbeam_extractor import extract_xbeam_values


def _normalize_paths(path: str):
    """
    Normalize an input path to both (folder_path, xml_path).

    The caller can pass either:
    - a folder containing Results.xml
    - a direct path to Results.xml
    
    Handles relative paths by trying to resolve them relative to MPC-Plus directory.
    """
    # Get MPC-Plus directory (common parent directory)
    # Navigate up from current script: ETL -> data_manipulation -> src -> MPC-Plus
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mpc_plus_dir = os.path.abspath(os.path.join(script_dir, '../../..'))
    
    # Normalize path separators
    path = path.replace('\\', os.sep).replace('/', os.sep)
    
    # Try to resolve the path
    resolved_path = None
    
    # First, try as-is (if it's already absolute and exists)
    if os.path.isabs(path) and os.path.exists(path):
        resolved_path = path
    # If relative path, try multiple possible locations relative to MPC-Plus
    elif not os.path.isabs(path):
        possible_paths = [
            os.path.join(mpc_plus_dir, path),  # Relative to MPC-Plus root
            os.path.join(os.getcwd(), path),  # Relative to current working directory
        ]
        
        # Also try if path starts with 'data/' - resolve relative to MPC-Plus
        if path.startswith('data' + os.sep) or path.startswith('data/'):
            possible_paths.insert(0, os.path.join(mpc_plus_dir, path))
        
        for alt_path in possible_paths:
            if os.path.exists(alt_path):
                resolved_path = os.path.abspath(alt_path)
                break
        
        # If still not found, try resolving as absolute from current directory
        if not resolved_path:
            resolved_path = os.path.abspath(path)
    else:
        # Absolute path that doesn't exist - use as-is (will fail later)
        resolved_path = path

    # Determine if resolved_path is a directory or file
    if os.path.isdir(resolved_path):
        folder_path = resolved_path
        xml_path = os.path.join(folder_path, "Results.xml")
    else:
        xml_path = resolved_path
        folder_path = os.path.dirname(xml_path)

    return folder_path, xml_path


def detect_beam_type(path: str) -> str:
    """
    Detect beam type **only from the folder path**.
    
    Folder-name based rules:
    - Geometry: folder contains "geometry" or "geom"
    - X-beam: folder contains "6x", "15x", or "xbeam"
    - E-beam: folder contains "6e", "16e", or "beamchecktemplate"
    
    Returns:
        str: 'ebeam', 'xbeam', 'geometry', or 'unknown'
    """
    folder_path, _ = _normalize_paths(path)
    folder_name = os.path.basename(folder_path).lower()
    
    if any(token in folder_name for token in ["geometry", "geom"]):
        return "geometry"
    if any(token in folder_name for token in ["6x", "15x", "xbeam"]):
        return "xbeam"
    if any(token in folder_name for token in ["6e", "16e", "beamchecktemplate"]):
        return "ebeam"
    
    return "unknown"


def extract_beam_values(path: str):
    """
    Unified entrypoint to extract beam QA values.

    Args:
        path: Folder containing Results.xml OR direct path to Results.xml.

    Returns:
        dict | None:
            For e‑beam:
                {
                    "beam_type": "ebeam",
                    "relative_output_percent": float,
                    "relative_uniformity_percent": float,
                }

            For x‑beam (and geometry):
                {
                "beam_type": "xbeam" | "geometry",
                    "relative_output_percent": float,
                    "relative_uniformity_percent": float,
                    "center_shift_mm": float | None,
                }

            For unsupported / unknown beam types: None
    """
    beam_type = detect_beam_type(path)
    folder_path, xml_path = _normalize_paths(path)

    # e‑beam: use existing extractor and only expose output + uniformity
    if beam_type == "ebeam":
        output, uniformity = extract_ebeam_values(xml_path)
        if output is None or uniformity is None:
            return None

        return {
            "beam_type": "ebeam",
            "relative_output_percent": output,
            "relative_uniformity_percent": uniformity,
        }

    # x‑beam and geometry checks: same output fields (output + uniformity + center shift)
    if beam_type in ("xbeam", "geometry"):
        output, uniformity, center_shift = extract_xbeam_values(folder_path)
        if output is None or uniformity is None:
            return None

        return {
            "beam_type": beam_type,
            "relative_output_percent": output,
            "relative_uniformity_percent": uniformity,
            "center_shift_mm": center_shift,
        }

    # Unknown / unsupported beam type
    return None


if __name__ == "__main__":
    # Command-line interface for quick testing
    if len(sys.argv) < 2:
        print("Usage: beam_extractor.py <folder_or_results_xml_path>")
        sys.exit(1)

    input_path = sys.argv[1]
    result = extract_beam_values(input_path)

    if not result:
        print("Failed to detect beam type or extract values.")
        sys.exit(1)

    beam_type = result.get("beam_type")
    print(f"Beam type (from folder): {beam_type}")

    # Print only the fields relevant to the detected type
    if beam_type == "ebeam":
        print(f"Relative Output: {result['relative_output_percent']:.2f}%")
        print(f"Relative Uniformity: {result['relative_uniformity_percent']:.2f}%")
    elif beam_type in ("xbeam", "geometry"):
        print(f"Relative Output: {result['relative_output_percent']:.2f}%")
        print(f"Relative Uniformity: {result['relative_uniformity_percent']:.2f}%")
        center_shift = result.get("center_shift_mm")
        if center_shift is not None:
            print(f"Center Shift: {center_shift:.6f} mm")
        else:
            print("Center Shift: Not found")
    else:
        print("Unknown beam type.")
