"""
Geometry Check Extractor - Extracts beam and MLC data from Results.xml.

Uses the same calculation methods and value-derivation logic as mpc_parser.py
(XML/mpc_parser.py) to ensure consistency with the validated MPC parser.
Values not present in XML are returned as N/A.

Integrates cleanly with the existing ETL pipeline via extract_geometry_values().
"""

import os
import sys
import importlib.util
from pathlib import Path

NA = "N/A"


def _load_mpc_parser():
    """
    Load mpc_parser module from XML/mpc_parser.py (workspace root).
    Uses importlib to avoid package structure dependencies.
    """
    # Workspace root: MPC-Plus (contains XML folder and MPC-Plus-Monorepo)
    # geometry_extractor is at: MPC-Plus-Monorepo/backend/src/data_manipulation/ETL/extractors/xml/
    workspace_root = Path(__file__).resolve().parents[7]
    mpc_parser_path = workspace_root / "XML" / "mpc_parser.py"

    if not mpc_parser_path.exists():
        raise FileNotFoundError(
            f"mpc_parser.py not found at {mpc_parser_path}. "
            "Ensure XML/mpc_parser.py exists in the workspace."
        )

    spec = importlib.util.spec_from_file_location(
        "mpc_parser", str(mpc_parser_path)
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def _mpc_result_to_extractor_dict(mpc_results):
    """
    Map mpc_parser output keys to geometry_extractor dict format.
    mpc_parser returns keys like "BeamGroup/BeamOutputChange [%]".
    Returns None for numeric keys not present (so model setters are skipped).
    Returns NA for fields mpc_parser never extracts (jaws, collimation).
    """
    def get(key, default=None):
        val = mpc_results.get(key)
        return val if val is not None else default

    # Build mlc_leaves_a, mlc_leaves_b, mlc_backlash_a, mlc_backlash_b from
    # mpc_parser's per-leaf keys
    mlc_leaves_a = {}
    mlc_leaves_b = {}
    mlc_backlash_a = {}
    mlc_backlash_b = {}

    for key, val in mpc_results.items():
        if val is None:
            continue
        if key.startswith("CollimationGroup/MLCGroup/MLCLeavesA/MLCLeaf") and key.endswith(" [mm]"):
            idx_str = key.replace("CollimationGroup/MLCGroup/MLCLeavesA/MLCLeaf", "").replace(" [mm]", "")
            try:
                mlc_leaves_a[int(idx_str)] = round(val, 2)
            except ValueError:
                pass
        elif key.startswith("CollimationGroup/MLCGroup/MLCLeavesB/MLCLeaf") and key.endswith(" [mm]"):
            idx_str = key.replace("CollimationGroup/MLCGroup/MLCLeavesB/MLCLeaf", "").replace(" [mm]", "")
            try:
                mlc_leaves_b[int(idx_str)] = round(val, 2)
            except ValueError:
                pass
        elif key.startswith("CollimationGroup/MLCBacklashGroup/MLCBacklashLeavesA/MLCBacklashLeaf") and key.endswith(" [mm]"):
            idx_str = key.replace("CollimationGroup/MLCBacklashGroup/MLCBacklashLeavesA/MLCBacklashLeaf", "").replace(" [mm]", "")
            try:
                mlc_backlash_a[int(idx_str)] = round(val, 2)
            except ValueError:
                pass
        elif key.startswith("CollimationGroup/MLCBacklashGroup/MLCBacklashLeavesB/MLCBacklashLeaf") and key.endswith(" [mm]"):
            idx_str = key.replace("CollimationGroup/MLCBacklashGroup/MLCBacklashLeavesB/MLCBacklashLeaf", "").replace(" [mm]", "")
            try:
                mlc_backlash_b[int(idx_str)] = round(val, 2)
            except ValueError:
                pass

    return {
        # BeamGroup
        "beam_output_change": get("BeamGroup/BeamOutputChange [%]"),
        "beam_uniformity_change": get("BeamGroup/BeamUniformityChange [%]"),
        "beam_center_shift": get("BeamGroup/BeamCenterShift [mm]"),
        # IsoCenterGroup
        "iso_center_size": get("IsoCenterGroup/IsoCenterSize [mm]"),
        "iso_center_mv_offset": get("IsoCenterGroup/IsoCenterMVOffset [mm]"),
        "iso_center_kv_offset": get("IsoCenterGroup/IsoCenterKVOffset [mm]"),
        # MLC leaves
        "mlc_leaves_a": dict(sorted(mlc_leaves_a.items())),
        "mlc_leaves_b": dict(sorted(mlc_leaves_b.items())),
        "mlc_backlash_a": dict(sorted(mlc_backlash_a.items())),
        "mlc_backlash_b": dict(sorted(mlc_backlash_b.items())),
        # MLC summary stats
        "mlc_max_offset_a": get("CollimationGroup/MLCGroup/MLCMaxOffsetA [mm]"),
        "mlc_max_offset_b": get("CollimationGroup/MLCGroup/MLCMaxOffsetB [mm]"),
        "mlc_mean_offset_a": get("CollimationGroup/MLCGroup/MLCMeanOffsetA [mm]"),
        "mlc_mean_offset_b": get("CollimationGroup/MLCGroup/MLCMeanOffsetB [mm]"),
        "mlc_backlash_max_a": get("CollimationGroup/MLCBacklashGroup/MLCBacklashMaxA [mm]"),
        "mlc_backlash_max_b": get("CollimationGroup/MLCBacklashGroup/MLCBacklashMaxB [mm]"),
        "mlc_backlash_mean_a": get("CollimationGroup/MLCBacklashGroup/MLCBacklashMeanA [mm]"),
        "mlc_backlash_mean_b": get("CollimationGroup/MLCBacklashGroup/MLCBacklashMeanB [mm]"),
        # GantryGroup
        "gantry_absolute": get("GantryGroup/GantryAbsolute [°]"),
        "gantry_relative": get("GantryGroup/GantryRelative [°]"),
        # EnhancedCouchGroup
        "couch_max_position_error": get("EnhancedCouchGroup/CouchMaxPositionError [mm]"),
        "couch_lat": get("EnhancedCouchGroup/CouchLat [mm]"),
        "couch_lng": get("EnhancedCouchGroup/CouchLng [mm]"),
        "couch_vrt": get("EnhancedCouchGroup/CouchVrt [mm]"),
        "couch_rtn_fine": get("EnhancedCouchGroup/CouchRtnFine [°]"),
        "couch_rtn_large": get("EnhancedCouchGroup/CouchRtnLarge [°]"),
        "rotation_induced_couch_shift_full_range": get(
            "EnhancedCouchGroup/RotationInducedCouchShiftFullRange [mm]"
        ),
        # Not extracted by mpc_parser (no XML source in geometry check)
        "collimation_rotation_offset": NA,
        "jaw_x1": NA,
        "jaw_x2": NA,
        "jaw_y1": NA,
        "jaw_y2": NA,
        "jaw_parallelism_x1": NA,
        "jaw_parallelism_x2": NA,
        "jaw_parallelism_y1": NA,
        "jaw_parallelism_y2": NA,
    }


def extract_geometry_values(folder_path):
    """
    Extract beam values and MLC leaf data from geometry check Results.xml.

    Uses mpc_parser.py for all calculations and value derivation, ensuring
    consistency with the validated MPC parser.
    Values not present in XML are returned as N/A.

    Args:
        folder_path: Path to the folder containing Results.xml

    Returns:
        dict with keys:
            - beam_output_change: float (%) or N/A
            - beam_uniformity_change: float (%) or N/A
            - beam_center_shift: float (mm) or N/A
            - iso_center_size, iso_center_mv_offset, iso_center_kv_offset
            - mlc_leaves_a, mlc_leaves_b, mlc_backlash_a, mlc_backlash_b
            - mlc_max_offset_a/b, mlc_mean_offset_a/b
            - mlc_backlash_max_a/b, mlc_backlash_mean_a/b
            - gantry_absolute, gantry_relative
            - couch_max_position_error, couch_lat, couch_lng, couch_vrt
            - couch_rtn_fine, couch_rtn_large
            - rotation_induced_couch_shift_full_range
            - etc.
        Returns None if extraction fails.
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
        mpc_parser = _load_mpc_parser()
        mpc_results = mpc_parser.parse_mpc_xml(results_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None
    except Exception as e:
        print(f"Error parsing XML with mpc_parser: {e}")
        return None

    return _mpc_result_to_extractor_dict(mpc_results)


if __name__ == "__main__":
    """CLI: python geometry_extractor.py <folder_path>"""
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
        ("mlc_max_offset_a", "MLCMaxOffsetA [mm]"),
        ("mlc_max_offset_b", "MLCMaxOffsetB [mm]"),
        ("mlc_mean_offset_a", "MLCMeanOffsetA [mm]"),
        ("mlc_mean_offset_b", "MLCMeanOffsetB [mm]"),
        ("mlc_backlash_max_a", "MLCBacklashMaxA [mm]"),
        ("mlc_backlash_max_b", "MLCBacklashMaxB [mm]"),
        ("mlc_backlash_mean_a", "MLCBacklashMeanA [mm]"),
        ("mlc_backlash_mean_b", "MLCBacklashMeanB [mm]"),
        ("gantry_absolute", "GantryAbsolute [°]"),
        ("gantry_relative", "GantryRelative [°]"),
        ("couch_max_position_error", "CouchMaxPositionError [mm]"),
        ("couch_lat", "CouchLat [mm]"),
        ("couch_lng", "CouchLng [mm]"),
        ("couch_vrt", "CouchVrt [mm]"),
        ("couch_rtn_fine", "CouchRtnFine [°]"),
        ("couch_rtn_large", "CouchRtnLarge [°]"),
        ("rotation_induced_couch_shift_full_range", "RotationInducedCouchShiftFullRange [mm]"),
        ("jaw_x1", "JawX1 [mm]"),
        ("jaw_x2", "JawX2 [mm]"),
        ("jaw_y1", "JawY1 [mm]"),
        ("jaw_y2", "JawY2 [mm]"),
        ("jaw_parallelism_x1", "JawParallelismX1 [°]"),
        ("jaw_parallelism_x2", "JawParallelismX2 [°]"),
        ("jaw_parallelism_y1", "JawParallelismY1 [°]"),
        ("jaw_parallelism_y2", "JawParallelismY2 [°]"),
        ("collimation_rotation_offset", "CollimationRotationOffset [°]"),
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
