"""
Geometry Check Extractor - Extracts beam and MLC data from Results.xml.

Reads Varian MPC Results.xml (geometry check), extracts beam profile values,
center shift, MLC leaf offsets, IsoCenter, Gantry, and EnhancedCouch metrics.
Output matches Results.csv format. Values not present in XML are returned as N/A.

All calculations use the same formulas as mpc_parser.py (XML/mpc_parser.py)
to ensure consistency with the validated MPC parser. No mpc_parser import.
"""

import os
import sys
import math
import statistics
import xml.etree.ElementTree as ET
from pathlib import Path
from dataclasses import dataclass

NA = "N/A"

# Step tags for EnhancedCouch (from mpc_parser)
LINEAR_STEP_TAGS = [
    "EnhancedCouch-Lin_Vrt",
    "EnhancedCouch-Lin_Lat",
    "EnhancedCouch-Lin_Lng",
    "EnhancedCouch-Lin_VrtLatLng1",
    "EnhancedCouch-Lin_VrtLatLng2",
]
FINE_ROTATION_STEP_TAGS = ["EnhancedCouch-Rtn_Fine1", "EnhancedCouch-Rtn_Fine2"]
LARGE_ROTATION_STEP_TAGS = [
    "EnhancedCouch-Rtn_Large090",
    "EnhancedCouch-Rtn_Large135",
    "EnhancedCouch-Rtn_Large225",
    "EnhancedCouch-Rtn_Large270",
]

XSI_TYPE = "{http://www.w3.org/2001/XMLSchema-instance}type"


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


def _find_child(elem, local_tag):
    """Find direct child by local tag name. Returns None if not found."""
    for child in elem:
        if _tag(child) == local_tag:
            return child
    return None


def _find_all_children(elem, local_tag):
    """Find all direct children with given local tag."""
    return [c for c in elem if _tag(c) == local_tag]


def _get_workspace_root():
    """
    Get MPC-Plus workspace root (parent of MPC-Plus-Monorepo).
    geometry_extractor is at: .../MPC-Plus-Monorepo/backend/.../extractors/xml/
    """
    return Path(__file__).resolve().parents[7]


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
    workspace_root = _get_workspace_root()
    for alt in [
        str(workspace_root / folder_path),
        str(workspace_root / "data" / "csv_data" / folder_path),
        str(workspace_root / "MPC-Plus-Monorepo" / "backend" / "data" / "xml_only" / folder_path),
    ]:
        if os.path.exists(alt):
            return alt
    return None


def _build_step_index(root):
    """
    Index all CompletedSteps by their xsi:type attribute.
    Returns dict mapping step type (e.g. 'BeamProfileCheck') to list of (tag, element).
    """
    steps = {}
    completed = _find_child(root, "CompletedSteps")
    if completed is None:
        return steps
    for child in completed:
        stype = child.get(XSI_TYPE, "")
        tag_el = _find_child(child, "Tag")
        tag = tag_el.text.strip() if tag_el is not None and tag_el.text else ""
        steps.setdefault(stype, []).append((tag, child))
    return steps


def _wrap_angle(deg):
    """Normalize angle to [-180, +180]."""
    while deg > 180:
        deg -= 360
    while deg < -180:
        deg += 360
    return deg


@dataclass
class MotionError:
    """Translational (cm) and rotational (deg) error from couch step."""

    x: float
    y: float
    z: float
    ax: float
    ay: float
    az: float


def _extract_motion_error(step):
    """
    Compute ActualMotion - NominalMotion for EnhancedCouchPosition step.
    Returns MotionError with x,y,z (cm) and ax,ay,az (deg).
    """
    am = _find_child(step, "ActualMotion")
    nm = _find_child(step, "NominalMotion")
    if am is None or nm is None:
        return None
    amo = _find_child(am, "Origin")
    nmo = _find_child(nm, "Origin")
    if amo is None or nmo is None:
        return None
    x1 = _find_text(amo, "X")
    y1 = _find_text(amo, "Y")
    z1 = _find_text(amo, "Z")
    x2 = _find_text(nmo, "X")
    y2 = _find_text(nmo, "Y")
    z2 = _find_text(nmo, "Z")
    ax1 = _find_text(am, "AngleX")
    ay1 = _find_text(am, "AngleY")
    az1 = _find_text(am, "AngleZ")
    ax2 = _find_text(nm, "AngleX")
    ay2 = _find_text(nm, "AngleY")
    az2 = _find_text(nm, "AngleZ")
    if any(v is None for v in (x1, y1, z1, x2, y2, z2, ax1, ay1, az1, ax2, ay2, az2)):
        return None
    return MotionError(
        x=x1 - x2,
        y=y1 - y2,
        z=z1 - z2,
        ax=ax1 - ax2,
        ay=ay1 - ay2,
        az=az1 - az2,
    )


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


def _extract_iso_center(steps):
    """Extract IsoCenterSize, IsoCenterMVOffset, IsoCenterKVOffset from IsoCal steps."""
    iso_size = iso_mv = iso_kv = None
    for _, step in steps.get("IsoCal", []):
        all_mv = _find_child(step, "AllMVResults")
        if all_mv is None:
            continue
        # KeyValueOfstringIsoCalResultsAsoNrQnM / Value / MaxCentralBeamError
        kv_pair = _find_child(all_mv, "KeyValueOfstringIsoCalResultsAsoNrQnM")
        if kv_pair is not None:
            mv_val = _find_child(kv_pair, "Value")
            if mv_val is not None:
                mce = _find_child(mv_val, "MaxCentralBeamError")
                if mce is not None and mce.text:
                    iso_size = round(float(mce.text.strip()), 2)
                # MV frames for IsoCenterMVOffset
                frames_el = _find_child(mv_val, "Frames")
                if frames_el is not None:
                    frames = _find_all_children(frames_el, "IsoCalResults.Frame")
                    if frames:
                        radii = []
                        for f in frames:
                            px = _find_text(f, "IsocenterProjectionX")
                            py = _find_text(f, "IsocenterProjectionY")
                            if px is not None and py is not None:
                                radii.append(math.sqrt(px**2 + py**2))
                        if radii:
                            iso_mv = round(max(radii), 2)
        # KV frames for IsoCenterKVOffset
        kv_res = _find_child(step, "KVResults")
        if kv_res is not None:
            frames_el = _find_child(kv_res, "Frames")
            if frames_el is not None:
                frames = _find_all_children(frames_el, "IsoCalResults.Frame")
                if frames:
                    radii = []
                    for f in frames:
                        px = _find_text(f, "IsocenterProjectionX")
                        py = _find_text(f, "IsocenterProjectionY")
                        if px is not None and py is not None:
                            radii.append(math.sqrt(px**2 + py**2))
                    if radii:
                        iso_kv = round(max(radii), 2)
        break
    return iso_size, iso_mv, iso_kv


def _extract_gantry(steps):
    """Extract GantryAbsolute and GantryRelative."""
    gantry_abs = gantry_rel = None
    for _, step in steps.get("EnhancedCouchPositionGantryAbsCorrection", []):
        err_el = _find_child(step, "GantryAbsoluteError")
        if err_el is not None and err_el.text:
            gantry_abs = round(-float(err_el.text.strip()), 2)
        break
    for _, step in steps.get("IsoCal", []):
        all_mv = _find_child(step, "AllMVResults")
        if all_mv is None:
            continue
        kv_pair = _find_child(all_mv, "KeyValueOfstringIsoCalResultsAsoNrQnM")
        if kv_pair is None:
            continue
        mv_val = _find_child(kv_pair, "Value")
        if mv_val is None:
            continue
        frames_el = _find_child(mv_val, "Frames")
        if frames_el is None:
            continue
        frames = _find_all_children(frames_el, "IsoCalResults.Frame")
        deviations = []
        for f in frames:
            found = _find_text(f, "FoundSourceAngle")
            nominal = _find_text(f, "NominalSourceAngle")
            if found is not None and nominal is not None:
                deviations.append(_wrap_angle(found - nominal))
        if deviations:
            mean_dev = statistics.mean(deviations)
            residuals = [d - mean_dev for d in deviations]
            max_res = max(residuals, key=abs)
            gantry_rel = round(-max_res, 2)
        break
    return gantry_abs, gantry_rel


def _extract_enhanced_couch(steps):
    """Extract CouchLat, CouchLng, CouchVrt, CouchMaxPositionError, CouchRtnFine, CouchRtnLarge, RotationInducedCouchShiftFullRange."""
    couch_steps = {tag: step for tag, step in steps.get("EnhancedCouchPosition", [])}
    result = {
        "couch_lat": None,
        "couch_lng": None,
        "couch_vrt": None,
        "couch_max_position_error": None,
        "couch_rtn_fine": None,
        "couch_rtn_large": None,
        "rotation_induced_couch_shift_full_range": None,
    }
    lin_errors = []
    for t in LINEAR_STEP_TAGS:
        if t in couch_steps:
            err = _extract_motion_error(couch_steps[t])
            if err is not None:
                lin_errors.append(err)
    if lin_errors:
        result["couch_lat"] = round(max(abs(e.x) for e in lin_errors) * 10, 2)
        result["couch_lng"] = round(max(abs(e.y) for e in lin_errors) * 10, 2)
        result["couch_vrt"] = round(max(abs(e.z) for e in lin_errors) * 10, 2)
        result["couch_max_position_error"] = round(
            max(math.sqrt(e.x**2 + e.y**2 + e.z**2) for e in lin_errors) * 10, 2
        )
    fine_errors = []
    for t in FINE_ROTATION_STEP_TAGS:
        if t in couch_steps:
            err = _extract_motion_error(couch_steps[t])
            if err is not None:
                fine_errors.append(err)
    if fine_errors:
        result["couch_rtn_fine"] = round(max(abs(e.az) for e in fine_errors), 2)
    large_errors = []
    for t in LARGE_ROTATION_STEP_TAGS:
        if t in couch_steps:
            err = _extract_motion_error(couch_steps[t])
            if err is not None:
                large_errors.append(err)
    if large_errors:
        result["couch_rtn_large"] = round(max(abs(e.az) for e in large_errors), 2)
        result["rotation_induced_couch_shift_full_range"] = round(
            max(math.sqrt(e.x**2 + e.y**2) for e in large_errors) * 10, 2
        )
    return result


def extract_geometry_values(folder_path):
    """
    Extract beam values, MLC leaf data, IsoCenter, Gantry, and EnhancedCouch from Results.xml.

    All calculations match mpc_parser.py formulas. No mpc_parser import.

    Args:
        folder_path: Path to the folder containing Results.xml

    Returns:
        dict with beam, MLC, IsoCenter, Gantry, Couch fields. None if extraction fails.
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

    steps = _build_step_index(root)

    # ========================================================================
    # BEAM PROFILE - (RelativeOutput - 1) * 100, RelativeUniformity * 100
    # ========================================================================
    beam_output_change = beam_uniformity_change = beam_center_shift = None
    for _, step in steps.get("BeamProfileCheck", []):
        ro = _find_text(step, "RelativeOutput")
        ru = _find_text(step, "RelativeUniformity")
        if ro is not None:
            beam_output_change = round((ro - 1.0) * 100, 2)
        if ru is not None:
            beam_uniformity_change = round(ru * 100, 2)
        break

    # ========================================================================
    # CENTER SHIFT - sqrt((IsoCenter - BaselineIsoCenter)²) × 10 [mm]
    # ========================================================================
    for _, step in steps.get("JawEdgeCheck", []):
        iso = _find_child(step, "IsoCenter")
        base = _find_child(step, "BaselineIsoCenter")
        if iso and base:
            iso_x = _find_text(iso, "X")
            iso_y = _find_text(iso, "Y")
            base_x = _find_text(base, "X")
            base_y = _find_text(base, "Y")
            if all(v is not None for v in (iso_x, iso_y, base_x, base_y)):
                dx = iso_x - base_x
                dy = iso_y - base_y
                beam_center_shift = round(math.sqrt(dx**2 + dy**2) * 10, 2)
        break

    # ========================================================================
    # MLC LEAF DATA - mpc_parser formulas (max-abs selection, negate B)
    # ========================================================================
    leaf_pairs, leaf_pairs_ex = _collect_leaf_data(root)
    all_indices = sorted(set(leaf_pairs.keys()) & set(leaf_pairs_ex.keys()))
    chosen_a, chosen_b, backlash_a, backlash_b = [], [], [], []
    mlc_leaves_a, mlc_leaves_b = {}, {}
    mlc_backlash_a, mlc_backlash_b = {}, {}

    for idx in all_indices:
        lp, lpx = leaf_pairs.get(idx, {}), leaf_pairs_ex.get(idx, {})
        off_a1, off_b1 = lp.get("LeafOffsetA"), lp.get("LeafOffsetB")
        off_a2, off_b2 = lpx.get("LeafOffsetA"), lpx.get("LeafOffsetB")
        if any(v is None for v in (off_a1, off_b1, off_a2, off_b2)):
            continue
        a1, b1, a2, b2 = off_a1 * 10, off_b1 * 10, off_a2 * 10, off_b2 * 10
        ca = a1 if abs(a1) >= abs(a2) else a2
        cb = b1 if abs(b1) >= abs(b2) else b2
        ba, bb = abs(a1 - a2), abs(b1 - b2)
        chosen_a.append(ca)
        chosen_b.append(cb)
        backlash_a.append(ba)
        backlash_b.append(bb)
        mlc_leaves_a[idx] = round(ca, 2)
        mlc_leaves_b[idx] = round(-cb, 2)
        mlc_backlash_a[idx] = round(ba, 2)
        mlc_backlash_b[idx] = round(bb, 2)

    mlc_max_offset_a = round(max(abs(x) for x in chosen_a), 2) if chosen_a else None
    mlc_max_offset_b = round(max(abs(x) for x in chosen_b), 2) if chosen_b else None
    mlc_mean_offset_a = round(statistics.mean(chosen_a), 2) if chosen_a else None
    mlc_mean_offset_b = round(statistics.mean(abs(x) for x in chosen_b), 2) if chosen_b else None
    mlc_backlash_max_a = round(max(backlash_a), 2) if backlash_a else None
    mlc_backlash_max_b = round(max(backlash_b), 2) if backlash_b else None
    mlc_backlash_mean_a = round(statistics.mean(backlash_a), 2) if backlash_a else None
    mlc_backlash_mean_b = round(statistics.mean(backlash_b), 2) if backlash_b else None

    # ========================================================================
    # IsoCenter, Gantry, EnhancedCouch (from mpc_parser formulas)
    # ========================================================================
    iso_size, iso_mv, iso_kv = _extract_iso_center(steps)
    gantry_abs, gantry_rel = _extract_gantry(steps)
    couch = _extract_enhanced_couch(steps)

    return {
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
        "iso_center_size": iso_size,
        "iso_center_mv_offset": iso_mv,
        "iso_center_kv_offset": iso_kv,
        "gantry_absolute": gantry_abs,
        "gantry_relative": gantry_rel,
        "couch_max_position_error": couch["couch_max_position_error"],
        "couch_lat": couch["couch_lat"],
        "couch_lng": couch["couch_lng"],
        "couch_vrt": couch["couch_vrt"],
        "couch_rtn_fine": couch["couch_rtn_fine"],
        "couch_rtn_large": couch["couch_rtn_large"],
        "rotation_induced_couch_shift_full_range": couch["rotation_induced_couch_shift_full_range"],
        "jaw_x1": NA,
        "jaw_x2": NA,
        "jaw_y1": NA,
        "jaw_y2": NA,
        "jaw_parallelism_x1": NA,
        "jaw_parallelism_x2": NA,
        "jaw_parallelism_y1": NA,
        "jaw_parallelism_y2": NA,
        "collimation_rotation_offset": NA,
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
        leaves = data.get(key, {})
        if leaves:
            print(f"\n{label}: {len(leaves)} leaves")
            for idx, val in leaves.items():
                print(f"  {leaf_name}{idx} [mm] = {val}")
        else:
            print(f"\n{label}: No leaves found")
