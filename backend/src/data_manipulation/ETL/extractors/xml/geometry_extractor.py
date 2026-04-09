"""
Geometry Check Extractor - Extracts beam, IsoCenter, Gantry, Couch, and MLC
data from a Varian MPC Results.xml file.

Delegates all XML parsing to mpc_parser.parse_mpc_xml() and maps the flat
CSV-style keys into the structured dict that the rest of the ETL pipeline
(xml_beam_extractor_entry.py) expects.
"""

import os
import sys
import re

try:
    from src.data_manipulation.ETL.extractors.xml.mpc_parser import parse_mpc_xml
except ImportError:
    from mpc_parser import parse_mpc_xml

NA = "N/A"


def is_geometry_folder(folder_path):
    """
    Check if folder is a geometry check folder.

    Args:
        folder_path: Path to the folder to check

    Returns:
        bool: True if folder name contains geometry check indicators
    """
    folder_name = os.path.basename(folder_path)
    return (
        "GeometryCheckTemplate" in folder_name
        or "6xMVkVEnhancedCouch" in folder_name
        or "GeometryCheck" in folder_name
    )


def _resolve_folder_path(folder_path):
    """
    Resolve folder path. Tries MPC-Plus root and data/csv_data/ if not found.
    Matches xbeam_extractor path resolution behavior.
    """
    if os.path.exists(folder_path):
        return folder_path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mpc_plus_dir = os.path.abspath(os.path.join(script_dir, "../../.."))
    for alt in [
        os.path.join(mpc_plus_dir, folder_path),
        os.path.join(mpc_plus_dir, "data", "csv_data", folder_path),
    ]:
        if os.path.exists(alt):
            return alt
    return None


# ---------------------------------------------------------------------------
# Key mapping: mpc_parser CSV-style keys -> pipeline dict keys
# ---------------------------------------------------------------------------
_SCALAR_MAP = {
    "BeamGroup/BeamOutputChange [%]": "beam_output_change",
    "BeamGroup/BeamUniformityChange [%]": "beam_uniformity_change",
    "BeamGroup/BeamCenterShift [mm]": "beam_center_shift",
    "IsoCenterGroup/IsoCenterSize [mm]": "iso_center_size",
    "IsoCenterGroup/IsoCenterMVOffset [mm]": "iso_center_mv_offset",
    "IsoCenterGroup/IsoCenterKVOffset [mm]": "iso_center_kv_offset",
    "GantryGroup/GantryAbsolute [°]": "gantry_absolute",
    "GantryGroup/GantryRelative [°]": "gantry_relative",
    "EnhancedCouchGroup/CouchLat [mm]": "couch_lat",
    "EnhancedCouchGroup/CouchLng [mm]": "couch_lng",
    "EnhancedCouchGroup/CouchVrt [mm]": "couch_vrt",
    "EnhancedCouchGroup/CouchMaxPositionError [mm]": "couch_max_position_error",
    "EnhancedCouchGroup/CouchRtnFine [°]": "couch_rtn_fine",
    "EnhancedCouchGroup/CouchRtnLarge [°]": "couch_rtn_large",
    "EnhancedCouchGroup/RotationInducedCouchShiftFullRange [mm]": "rotation_induced_couch_shift_full_range",
    "CollimationGroup/MLCGroup/MLCMaxOffsetA [mm]": "mlc_max_offset_a",
    "CollimationGroup/MLCGroup/MLCMaxOffsetB [mm]": "mlc_max_offset_b",
    "CollimationGroup/MLCGroup/MLCMeanOffsetA [mm]": "mlc_mean_offset_a",
    "CollimationGroup/MLCGroup/MLCMeanOffsetB [mm]": "mlc_mean_offset_b",
    "CollimationGroup/MLCBacklashGroup/MLCBacklashMaxA [mm]": "mlc_backlash_max_a",
    "CollimationGroup/MLCBacklashGroup/MLCBacklashMaxB [mm]": "mlc_backlash_max_b",
    "CollimationGroup/MLCBacklashGroup/MLCBacklashMeanA [mm]": "mlc_backlash_mean_a",
    "CollimationGroup/MLCBacklashGroup/MLCBacklashMeanB [mm]": "mlc_backlash_mean_b",
}

_LEAF_A_RE = re.compile(r"CollimationGroup/MLCGroup/MLCLeavesA/MLCLeaf(\d+) \[mm\]")
_LEAF_B_RE = re.compile(r"CollimationGroup/MLCGroup/MLCLeavesB/MLCLeaf(\d+) \[mm\]")
_BACKLASH_A_RE = re.compile(r"CollimationGroup/MLCBacklashGroup/MLCBacklashLeavesA/MLCBacklashLeaf(\d+) \[mm\]")
_BACKLASH_B_RE = re.compile(r"CollimationGroup/MLCBacklashGroup/MLCBacklashLeavesB/MLCBacklashLeaf(\d+) \[mm\]")


def extract_geometry_values(folder_path):
    """
    Extract all geometry check metrics from Results.xml via mpc_parser.

    Args:
        folder_path: Path to the folder containing Results.xml

    Returns:
        dict with beam, isocenter, gantry, couch, and MLC fields,
        or None if extraction fails.
    """
    folder_path = _resolve_folder_path(folder_path)
    if not folder_path:
        print(f"Error: Folder not found: {folder_path}")
        return None

    results_path = os.path.join(folder_path, "Results.xml")
    if not os.path.exists(results_path):
        print(f"Error: Results.xml not found in {folder_path}")
        return None

    if not is_geometry_folder(folder_path):
        print("Error: Not a geometry check folder")
        return None

    try:
        raw = parse_mpc_xml(results_path)
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return None

    # Map scalar values
    result = {}
    for csv_key, pipeline_key in _SCALAR_MAP.items():
        result[pipeline_key] = raw.get(csv_key)

    # Map per-leaf MLC values
    mlc_leaves_a = {}
    mlc_leaves_b = {}
    mlc_backlash_a = {}
    mlc_backlash_b = {}

    for csv_key, value in raw.items():
        m = _LEAF_A_RE.match(csv_key)
        if m:
            mlc_leaves_a[int(m.group(1))] = value
            continue
        m = _LEAF_B_RE.match(csv_key)
        if m:
            mlc_leaves_b[int(m.group(1))] = value
            continue
        m = _BACKLASH_A_RE.match(csv_key)
        if m:
            mlc_backlash_a[int(m.group(1))] = value
            continue
        m = _BACKLASH_B_RE.match(csv_key)
        if m:
            mlc_backlash_b[int(m.group(1))] = value
            continue

    result["mlc_leaves_a"] = dict(sorted(mlc_leaves_a.items()))
    result["mlc_leaves_b"] = dict(sorted(mlc_leaves_b.items()))
    result["mlc_backlash_a"] = dict(sorted(mlc_backlash_a.items()))
    result["mlc_backlash_b"] = dict(sorted(mlc_backlash_b.items()))

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: geometry_extractor.py <folder_path>")
        sys.exit(1)

    folder_path = sys.argv[1]
    data = extract_geometry_values(folder_path)

    if data is None:
        print("Failed to extract geometry values")
        sys.exit(1)

    print("--- Fields ---")
    for key, label in [
        ("iso_center_size", "IsoCenterSize [mm]"),
        ("iso_center_mv_offset", "IsoCenterMVOffset [mm]"),
        ("iso_center_kv_offset", "IsoCenterKVOffset [mm]"),
        ("beam_output_change", "BeamOutputChange [%]"),
        ("beam_uniformity_change", "BeamUniformityChange [%]"),
        ("beam_center_shift", "BeamCenterShift [mm]"),
        ("gantry_absolute", "GantryAbsolute [°]"),
        ("gantry_relative", "GantryRelative [°]"),
        ("couch_lat", "CouchLat [mm]"),
        ("couch_lng", "CouchLng [mm]"),
        ("couch_vrt", "CouchVrt [mm]"),
        ("couch_max_position_error", "CouchMaxPositionError [mm]"),
        ("couch_rtn_fine", "CouchRtnFine [°]"),
        ("couch_rtn_large", "CouchRtnLarge [°]"),
        ("rotation_induced_couch_shift_full_range", "RotationInducedCouchShiftFullRange [mm]"),
        ("mlc_max_offset_a", "MLCMaxOffsetA [mm]"),
        ("mlc_max_offset_b", "MLCMaxOffsetB [mm]"),
        ("mlc_mean_offset_a", "MLCMeanOffsetA [mm]"),
        ("mlc_mean_offset_b", "MLCMeanOffsetB [mm]"),
        ("mlc_backlash_max_a", "MLCBacklashMaxA [mm]"),
        ("mlc_backlash_max_b", "MLCBacklashMaxB [mm]"),
        ("mlc_backlash_mean_a", "MLCBacklashMeanA [mm]"),
        ("mlc_backlash_mean_b", "MLCBacklashMeanB [mm]"),
    ]:
        val = data.get(key)
        if val is None:
            val = NA
        elif isinstance(val, (int, float)) and not isinstance(val, bool):
            val = f"{val:.2f}" if isinstance(val, float) else val
        print(f"  {label}: {val}")

    for key, label, leaf_name in [
        ("mlc_leaves_a", "MLCLeavesA", "MLCLeaf"),
        ("mlc_leaves_b", "MLCLeavesB", "MLCLeaf"),
        ("mlc_backlash_a", "MLCBacklashLeavesA", "MLCBacklashLeaf"),
        ("mlc_backlash_b", "MLCBacklashLeavesB", "MLCBacklashLeaf"),
    ]:
        leaves = data.get(key, {})
        if leaves:
            print(f"\n{label}: {len(leaves)} leaves")
            for idx, val in leaves.items():
                print(f"  {leaf_name}{idx} [mm] = {val}")
        else:
            print(f"\n{label}: No leaves found")
