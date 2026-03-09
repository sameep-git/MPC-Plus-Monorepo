"""
Geometry Check Extractor - Extracts beam and MLC data from Results.xml.

Reads Varian MPC Results.xml (geometry check), extracts beam profile values,
center shift, and MLC leaf offsets. Output matches Results.csv format.
Values not present in XML are returned as N/A.

=============================================================================
XML STRUCTURE (Results.xml)
=============================================================================

The XML uses namespaces and xsi:type for polymorphism. Key elements:

1. BEAM PROFILE (BeamProfileCheck)
   Location: <d2p1:anyType i:type="BeamProfileCheck">
   Children: <RelativeOutput>, <RelativeUniformity>
   - RelativeOutput: ratio (e.g. 0.999 → -0.1% output change)
   - RelativeUniformity: ratio (e.g. 0.001 → 0.1% uniformity change)

2. CENTER SHIFT (JawEdgeCheck)
   Location: <d2p1:anyType i:type="JawEdgeCheck">
   Children: <IsoCenter>, <BaselineIsoCenter>
   Each has <X>, <Y> sub-elements (normalized coordinates).
   Formula: sqrt((X-X0)² + (Y-Y0)²) × 10 = center shift [mm]

3. MLC LEAF DATA (MLCCheck)
   Two containers in the XML:
   - <LeafPairs>: First measurement (MLC position check)
   - <LeafPairsEx>: Second measurement (used for backlash)
   Each contains <ArrayOfMLCCheck.LeafPair> with <MLCCheck.LeafPair> entries:
     <Index>11</Index>           → leaf number (11-50)
     <LeafOffsetA>0.0099...</LeafOffsetA>  → bank A offset (normalized)
     <LeafOffsetB>-0.0372...</LeafOffsetB> → bank B offset (normalized)

=============================================================================
CALCULATIONS (LeafOffset × 10 = value [mm])
=============================================================================

- MLCLeavesA: LeafPairsEx.LeafOffsetA × 10  (bank A position from 2nd measurement)
- MLCLeavesB: |LeafPairs.LeafOffsetB| × 10  (bank B position from 1st, abs for positive)
- MLCBacklashA: |LeafPairsEx.LeafOffsetA - LeafPairs.LeafOffsetA| × 10
- MLCBacklashB: |LeafPairs.LeafOffsetB - LeafPairsEx.LeafOffsetB| × 10

Summary stats (MLCMaxOffset, MLCMeanOffset, etc.) are max/mean of the leaf values.
"""

import os
import sys
import math
import xml.etree.ElementTree as ET

NA = "N/A"


def _tag(elem):
    """
    Strip XML namespace from element tag.
    Varian XML uses {http://...}namespace:TagName format.
    Returns just the local name (e.g. 'MLCCheck.LeafPair').
    """
    return elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag


def _find_text(elem, child_tag):
    """
    Find direct child element by local tag name, return its text as float.
    Returns None if not found or invalid.
    """
    for child in elem:
        if _tag(child) == child_tag and child.text:
            try:
                return float(child.text.strip())
            except (ValueError, TypeError):
                return None
    return None


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


def _extract_leaf_pairs_from_container(container):
    """
    Extract leaf data from a <LeafPairs> or <LeafPairsEx> XML element.

    XML structure (either format):
      <LeafPairs> or <LeafPairsEx>
        <ArrayOfMLCCheck.LeafPair>   (optional wrapper)
          <MLCCheck.LeafPair>
            <Index>11</Index>
            <LeafOffsetA>0.0099436681463851428</LeafOffsetA>
            <LeafOffsetB>-0.037265466237850653</LeafOffsetB>
          </MLCCheck.LeafPair>
          ...

    Returns: dict {leaf_index: {"LeafOffsetA": float, "LeafOffsetB": float}}
    """
    result = {}
    for child in container:
        tag = _tag(child)
        if tag == "MLCCheck.LeafPair":
            idx = _find_text(child, "Index")
            if idx is not None:
                idx = int(idx)
                off_a = _find_text(child, "LeafOffsetA")
                off_b = _find_text(child, "LeafOffsetB")
                result[idx] = {"LeafOffsetA": off_a, "LeafOffsetB": off_b}
        elif "LeafPair" in tag or "ArrayOf" in tag:
            # Recurse into wrapper (e.g. ArrayOfMLCCheck.LeafPair)
            nested = _extract_leaf_pairs_from_container(child)
            for k, v in nested.items():
                if k not in result:
                    result[k] = v
                else:
                    result[k] = {**result[k], **v}
    return result


def _collect_leaf_data(root):
    """
    Traverse entire XML tree and collect all LeafPairs and LeafPairsEx data.

    There may be multiple MLCCheck elements (e.g. position check + backlash check).
    - LeafPairs: first measurement (position)
    - LeafPairsEx: second measurement (used for backlash calc)

    Returns: (leaf_pairs, leaf_pairs_ex) - each dict maps index -> {LeafOffsetA, LeafOffsetB}
    """
    leaf_pairs = {}
    leaf_pairs_ex = {}

    for elem in root.iter():
        tag = _tag(elem)
        if tag == "LeafPairs":
            data = _extract_leaf_pairs_from_container(elem)
            for idx, vals in data.items():
                if idx not in leaf_pairs:
                    leaf_pairs[idx] = vals
                else:
                    leaf_pairs[idx] = {**leaf_pairs[idx], **vals}
        elif tag == "LeafPairsEx":
            data = _extract_leaf_pairs_from_container(elem)
            for idx, vals in data.items():
                if idx not in leaf_pairs_ex:
                    leaf_pairs_ex[idx] = vals
                else:
                    leaf_pairs_ex[idx] = {**leaf_pairs_ex[idx], **vals}

    return leaf_pairs, leaf_pairs_ex


def extract_geometry_values(folder_path):
    """
    Extract beam values and MLC leaf data from geometry check Results.xml.

    Flow: resolve path → parse XML → extract BeamProfileCheck, JawEdgeCheck,
    LeafPairs/LeafPairsEx → compute leaf values and backlash → return dict.

    Args:
        folder_path: Path to the folder containing Results.xml

    Returns:
        dict with keys:
            - beam_output_change: float (%)
            - beam_uniformity_change: float (%)
            - beam_center_shift: float (mm) or None
            - mlc_leaves_a: dict {leaf_index: value_mm}
            - mlc_leaves_b: dict {leaf_index: value_mm}
            - mlc_backlash_a: dict {leaf_index: value_mm}
            - mlc_backlash_b: dict {leaf_index: value_mm}
            - mlc_max_offset_a/b, mlc_mean_offset_a/b: max/mean of leaf offsets
            - mlc_backlash_max_a/b, mlc_backlash_mean_a/b: max/mean of backlash
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
        tree = ET.parse(results_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return None

    # ========================================================================
    # BEAM PROFILE - XML: <d2p1:anyType i:type="BeamProfileCheck">
    # ========================================================================
    # Children: <RelativeOutput>, <RelativeUniformity>
    # Conversion: (RelativeOutput - 1) * 100 = BeamOutputChange [%]
    #             RelativeUniformity * 100 = BeamUniformityChange [%]
    beam_output_change = None
    beam_uniformity_change = None
    beam_center_shift = None

    xsi_type = "{http://www.w3.org/2001/XMLSchema-instance}type"
    for elem in root.iter():
        if elem.get(xsi_type) == "BeamProfileCheck":
            for child in elem:
                tag = _tag(child)
                if tag == "RelativeOutput" and child.text:
                    try:
                        beam_output_change = (float(child.text.strip()) - 1) * 100
                    except (ValueError, TypeError):
                        pass
                elif tag == "RelativeUniformity" and child.text:
                    try:
                        beam_uniformity_change = float(child.text.strip()) * 100
                    except (ValueError, TypeError):
                        pass
            break

    # ========================================================================
    # CENTER SHIFT - XML: <d2p1:anyType i:type="JawEdgeCheck">
    # ========================================================================
    # Children: <IsoCenter> and <BaselineIsoCenter>, each with <X>, <Y> sub-elements
    # Formula: Euclidean distance × 10 = BeamCenterShift [mm]
    #          sqrt((X - X0)² + (Y - Y0)²) × 10
    iso_x = iso_y = baseline_iso_x = baseline_iso_y = None
    for elem in root.iter():
        if elem.get(xsi_type) == "JawEdgeCheck":
            for child in elem:
                tag = _tag(child)
                if tag == "IsoCenter":
                    for coord in child:
                        ct = _tag(coord)
                        if ct == "X" and coord.text:
                            iso_x = float(coord.text.strip())
                        elif ct == "Y" and coord.text:
                            iso_y = float(coord.text.strip())
                elif tag == "BaselineIsoCenter":
                    for coord in child:
                        ct = _tag(coord)
                        if ct == "X" and coord.text:
                            baseline_iso_x = float(coord.text.strip())
                        elif ct == "Y" and coord.text:
                            baseline_iso_y = float(coord.text.strip())
            break

    if all(v is not None for v in (iso_x, iso_y, baseline_iso_x, baseline_iso_y)):
        dx = iso_x - baseline_iso_x
        dy = iso_y - baseline_iso_y
        beam_center_shift = math.sqrt(dx * dx + dy * dy) * 10

    # ========================================================================
    # MLC LEAF DATA - XML: <LeafPairs> and <LeafPairsEx> (under MLCCheck)
    # ========================================================================
    leaf_pairs, leaf_pairs_ex = _collect_leaf_data(root)

    # MLCLeavesA: CollimationGroup/MLCGroup/MLCLeavesA/MLCLeafN [mm]
    # Source: LeafPairsEx → LeafOffsetA × 10 (second measurement, bank A)
    mlc_leaves_a = {}
    for idx, vals in leaf_pairs_ex.items():
        off_a = vals.get("LeafOffsetA")
        if off_a is not None:
            mlc_leaves_a[idx] = round(off_a * 10, 2)

    # MLCLeavesB: CollimationGroup/MLCGroup/MLCLeavesB/MLCLeafN [mm]
    # Source: LeafPairs → LeafOffsetB × 10 (first measurement, bank B; abs for positive)
    mlc_leaves_b = {}
    for idx, vals in leaf_pairs.items():
        off_b = vals.get("LeafOffsetB")
        if off_b is not None:
            mlc_leaves_b[idx] = round(abs(off_b) * 10, 2)

    # MLCBacklashLeavesA: CollimationGroup/MLCBacklashGroup/MLCBacklashLeavesA/MLCBacklashLeafN [mm]
    # Source: |LeafPairsEx.LeafOffsetA - LeafPairs.LeafOffsetA| × 10 (absolute diff × 10)
    mlc_backlash_a = {}
    # MLCBacklashLeavesB: CollimationGroup/MLCBacklashGroup/MLCBacklashLeavesB/MLCBacklashLeafN [mm]
    # Source: |LeafPairs.LeafOffsetB - LeafPairsEx.LeafOffsetB| × 10 (absolute diff × 10)
    mlc_backlash_b = {}
    all_indices = set(leaf_pairs.keys()) | set(leaf_pairs_ex.keys())
    for idx in all_indices:
        off_a_pairs = leaf_pairs.get(idx, {}).get("LeafOffsetA")
        off_a_ex = leaf_pairs_ex.get(idx, {}).get("LeafOffsetA")
        if off_a_pairs is not None and off_a_ex is not None:
            diff = abs(off_a_ex - off_a_pairs)
            mlc_backlash_a[idx] = round(diff * 10, 2)

        off_b_pairs = leaf_pairs.get(idx, {}).get("LeafOffsetB")
        off_b_ex = leaf_pairs_ex.get(idx, {}).get("LeafOffsetB")
        if off_b_pairs is not None and off_b_ex is not None:
            diff = abs(off_b_pairs - off_b_ex)
            mlc_backlash_b[idx] = round(diff * 10, 2)

    # ========================================================================
    # SUMMARY STATS - Derived from leaf dicts (not direct XML)
    # ========================================================================
    # MLCMaxOffsetA/B, MLCMeanOffsetA/B: max/mean of MLCLeavesA/B values
    # MLCBacklashMaxA/B, MLCBacklashMeanA/B: max/mean of MLCBacklashLeavesA/B values
    def _max_or_none(d):
        return round(max(abs(v) for v in d.values()), 2) if d else None

    def _mean_or_none(d):
        return round(sum(abs(v) for v in d.values()) / len(d), 2) if d else None

    mlc_max_offset_a = _max_or_none(mlc_leaves_a)
    mlc_max_offset_b = _max_or_none(mlc_leaves_b)
    mlc_mean_offset_a = _mean_or_none(mlc_leaves_a)
    mlc_mean_offset_b = _mean_or_none(mlc_leaves_b)
    mlc_backlash_max_a = _max_or_none(mlc_backlash_a)
    mlc_backlash_max_b = _max_or_none(mlc_backlash_b)
    mlc_backlash_mean_a = _mean_or_none(mlc_backlash_a)
    mlc_backlash_mean_b = _mean_or_none(mlc_backlash_b)

    return {
        # From XML
        "beam_output_change": beam_output_change,
        "beam_uniformity_change": beam_uniformity_change,
        "beam_center_shift": beam_center_shift,
        "mlc_leaves_a": dict(sorted(mlc_leaves_a.items())),
        "mlc_leaves_b": dict(sorted(mlc_leaves_b.items())),
        "mlc_backlash_a": dict(sorted(mlc_backlash_a.items())),
        "mlc_backlash_b": dict(sorted(mlc_backlash_b.items())),
        "mlc_max_offset_a": mlc_max_offset_a,
        "mlc_max_offset_b": mlc_max_offset_b,
        "mlc_mean_offset_a": mlc_mean_offset_a,
        "mlc_mean_offset_b": mlc_mean_offset_b,
        "mlc_backlash_max_a": mlc_backlash_max_a,
        "mlc_backlash_max_b": mlc_backlash_max_b,
        "mlc_backlash_mean_a": mlc_backlash_mean_a,
        "mlc_backlash_mean_b": mlc_backlash_mean_b,
        # --------------------------------------------------------------------
        # NOT IN XML - These Results.csv fields have no XML source in geometry
        # check; return N/A (IsoCenter, Jaws, Gantry, Couch, etc.)
        # --------------------------------------------------------------------
        "iso_center_size": NA,
        "iso_center_mv_offset": NA,
        "iso_center_kv_offset": NA,
        "jaw_x1": NA,
        "jaw_x2": NA,
        "jaw_y1": NA,
        "jaw_y2": NA,
        "jaw_parallelism_x1": NA,
        "jaw_parallelism_x2": NA,
        "jaw_parallelism_y1": NA,
        "jaw_parallelism_y2": NA,
        "collimation_rotation_offset": NA,
        "gantry_absolute": NA,
        "gantry_relative": NA,
        "couch_max_position_error": NA,
        "couch_lat": NA,
        "couch_lng": NA,
        "couch_vrt": NA,
        "couch_rtn_fine": NA,
        "couch_rtn_large": NA,
        "rotation_induced_couch_shift_full_range": NA,
    }


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
        ("jaw_x1", "JawX1 [mm]"),
        ("jaw_x2", "JawX2 [mm]"),
        ("jaw_y1", "JawY1 [mm]"),
        ("jaw_y2", "JawY2 [mm]"),
        ("jaw_parallelism_x1", "JawParallelismX1 [°]"),
        ("jaw_parallelism_x2", "JawParallelismX2 [°]"),
        ("jaw_parallelism_y1", "JawParallelismY1 [°]"),
        ("jaw_parallelism_y2", "JawParallelismY2 [°]"),
        ("collimation_rotation_offset", "CollimationRotationOffset [°]"),
        ("gantry_absolute", "GantryAbsolute [°]"),
        ("gantry_relative", "GantryRelative [°]"),
        ("couch_max_position_error", "CouchMaxPositionError [mm]"),
        ("couch_lat", "CouchLat [mm]"),
        ("couch_lng", "CouchLng [mm]"),
        ("couch_vrt", "CouchVrt [mm]"),
        ("couch_rtn_fine", "CouchRtnFine [°]"),
        ("couch_rtn_large", "CouchRtnLarge [°]"),
        ("rotation_induced_couch_shift_full_range", "RotationInducedCouchShiftFullRange [mm]"),
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
        leaves = data[key]
        if leaves:
            print(f"\n{label}: {len(leaves)} leaves")
            for idx, val in leaves.items():
                print(f"  {leaf_name}{idx} [mm] = {val}")
        else:
            print(f"\n{label}: No leaves found")
