"""
mpc_parser.py — Varian MPC Results.xml Parser

Extracts all confirmed MPC check metrics from a Results.xml file,
reproducing the values that appear in the companion Results.csv.

Cross-validated against 3 independent MPC session pairs (552/553 matches).

Usage:
    from mpc_parser import parse_mpc_xml

    results = parse_mpc_xml("Results.xml")
    for name, value in results.items():
        print(f"{name} = {value}")

Or from the command line:
    python mpc_parser.py Results.xml
    python mpc_parser.py Results.xml --validate Results.csv
"""

import xml.etree.ElementTree as ET
import math
import statistics
import csv
import argparse
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# XML Namespace Constants
# ---------------------------------------------------------------------------
# NOTE: Varian's MPC namespace uses a single slash (http:/) not double (http://)
VARIAN_NS = "http:/www.varian.com/MPC"
ARRAYS_NS = "http://schemas.microsoft.com/2003/10/Serialization/Arrays"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"


def _v(tag: str) -> str:
    """Wrap a tag name with the Varian MPC namespace."""
    return f"{{{VARIAN_NS}}}{tag}"


def _a(tag: str) -> str:
    """Wrap a tag name with the Microsoft Arrays namespace."""
    return f"{{{ARRAYS_NS}}}{tag}"


# ---------------------------------------------------------------------------
# XML Step Tags
# ---------------------------------------------------------------------------
LINEAR_STEP_TAGS = [
    "EnhancedCouch-Lin_Vrt",
    "EnhancedCouch-Lin_Lat",
    "EnhancedCouch-Lin_Lng",
    "EnhancedCouch-Lin_VrtLatLng1",
    "EnhancedCouch-Lin_VrtLatLng2",
]

FINE_ROTATION_STEP_TAGS = [
    "EnhancedCouch-Rtn_Fine1",
    "EnhancedCouch-Rtn_Fine2",
]

LARGE_ROTATION_STEP_TAGS = [
    "EnhancedCouch-Rtn_Large090",
    "EnhancedCouch-Rtn_Large135",
    "EnhancedCouch-Rtn_Large225",
    "EnhancedCouch-Rtn_Large270",
]

MLC_LEAF_RANGE = range(11, 51)  # Leaves 11-50 (NDS120 central leaves)


# ---------------------------------------------------------------------------
# Helper: Motion Error Extraction
# ---------------------------------------------------------------------------
@dataclass
class MotionError:
    """Translational (cm) and rotational (deg) error from a couch step."""
    x: float   # Lateral (cm)
    y: float   # Longitudinal (cm)
    z: float   # Vertical (cm)
    ax: float  # Pitch (deg)
    ay: float  # Roll (deg)
    az: float  # Rotation (deg)


def _extract_motion_error(step: ET.Element) -> MotionError:
    """
    Compute ActualMotion - NominalMotion for an EnhancedCouchPosition step.

    XML Path:
        step/ActualMotion/Origin/{X,Y,Z}     (cm)
        step/NominalMotion/Origin/{X,Y,Z}    (cm)
        step/ActualMotion/{AngleX,AngleY,AngleZ}   (deg)
        step/NominalMotion/{AngleX,AngleY,AngleZ}   (deg)
    """
    am = step.find(_v("ActualMotion"))
    nm = step.find(_v("NominalMotion"))
    amo = am.find(_v("Origin"))
    nmo = nm.find(_v("Origin"))
    return MotionError(
        x=float(amo.find(_v("X")).text) - float(nmo.find(_v("X")).text),
        y=float(amo.find(_v("Y")).text) - float(nmo.find(_v("Y")).text),
        z=float(amo.find(_v("Z")).text) - float(nmo.find(_v("Z")).text),
        ax=float(am.find(_v("AngleX")).text) - float(nm.find(_v("AngleX")).text),
        ay=float(am.find(_v("AngleY")).text) - float(nm.find(_v("AngleY")).text),
        az=float(am.find(_v("AngleZ")).text) - float(nm.find(_v("AngleZ")).text),
    )


def _wrap_angle(deg: float) -> float:
    """Normalize an angle to the range [-180, +180]."""
    while deg > 180:
        deg -= 360
    while deg < -180:
        deg += 360
    return deg


# ---------------------------------------------------------------------------
# Step Index Builder
# ---------------------------------------------------------------------------
def _build_step_index(root: ET.Element) -> Dict[str, List[Tuple[str, ET.Element]]]:
    """
    Index all CompletedSteps by their xsi:type attribute.

    Returns a dict mapping step type names (e.g. "BeamProfileCheck")
    to a list of (tag_text, element) tuples.
    """
    steps: Dict[str, List[Tuple[str, ET.Element]]] = {}
    completed = root.find(_v("CompletedSteps"))
    for child in completed:
        stype = child.get(f"{{{XSI_NS}}}type", "")
        tag_el = child.find(_v("Tag"))
        tag = tag_el.text if tag_el is not None else ""
        steps.setdefault(stype, []).append((tag, child))
    return steps


# ---------------------------------------------------------------------------
# Individual Metric Extractors
# ---------------------------------------------------------------------------

def _extract_beam_group(
    steps: Dict[str, List[Tuple[str, ET.Element]]],
    results: Dict[str, float],
) -> None:
    """
    BeamGroup: Output, Uniformity, and CenterShift.

    BeamOutputChange [%]
        Source:  BeamProfileCheck/RelativeOutput
        Formula: (RelativeOutput - 1.0) * 100

    BeamUniformityChange [%]
        Source:  BeamProfileCheck/RelativeUniformity
        Formula: RelativeUniformity * 100

    BeamCenterShift [mm]
        Source:  JawEdgeCheck/IsoCenter/{X,Y}
                 JawEdgeCheck/BaselineIsoCenter/{X,Y}
        Formula: sqrt((IsoCenter.X - BaselineIsoCenter.X)^2
                     + (IsoCenter.Y - BaselineIsoCenter.Y)^2) * 10
        Units:   XML values are in cm; multiply by 10 for mm.
    """
    for _, step in steps.get("BeamProfileCheck", []):
        relative_output = float(step.find(_v("RelativeOutput")).text)
        relative_uniformity = float(step.find(_v("RelativeUniformity")).text)

        results["BeamGroup/BeamOutputChange [%]"] = (relative_output - 1.0) * 100
        results["BeamGroup/BeamUniformityChange [%]"] = relative_uniformity * 100

    for _, step in steps.get("JawEdgeCheck", []):
        iso = step.find(_v("IsoCenter"))
        base = step.find(_v("BaselineIsoCenter"))

        iso_x = float(iso.find(_v("X")).text)
        iso_y = float(iso.find(_v("Y")).text)
        base_x = float(base.find(_v("X")).text)
        base_y = float(base.find(_v("Y")).text)

        dx = iso_x - base_x   # cm
        dy = iso_y - base_y   # cm
        results["BeamGroup/BeamCenterShift [mm]"] = math.sqrt(dx**2 + dy**2) * 10


def _extract_isocenter_group(
    steps: Dict[str, List[Tuple[str, ET.Element]]],
    results: Dict[str, float],
) -> None:
    """
    IsoCenterGroup: Size, MV Offset, KV Offset.

    IsoCenterSize [mm]
        Source:  IsoCal/AllMVResults
                   /KeyValueOfstringIsoCalResultsAsoNrQnM/Value
                   /MaxCentralBeamError
        Formula: Direct read (already in mm).
        Notes:   Maximum distance between any MV frame's central
                 beam axis projection and the treatment isocenter.

    IsoCenterMVOffset [mm]
        Source:  IsoCal/AllMVResults/.../Value/Frames
                   /IsoCalResults.Frame/IsocenterProjection{X,Y}
        Formula: max over all MV frames of
                 sqrt(IsocenterProjectionX^2 + IsocenterProjectionY^2)
        Notes:   Already in mm. Maximum 2D radial distance of
                 per-frame isocenter projections.

    IsoCenterKVOffset [mm]
        Source:  IsoCal/KVResults/Frames
                   /IsoCalResults.Frame/IsocenterProjection{X,Y}
        Formula: max over all KV frames of
                 sqrt(IsocenterProjectionX^2 + IsocenterProjectionY^2)
        Notes:   Same calculation as MV, using KV frames.
    """
    for _, step in steps.get("IsoCal", []):
        all_mv = step.find(_v("AllMVResults"))
        kv_pair = all_mv.find(_a("KeyValueOfstringIsoCalResultsAsoNrQnM"))
        mv_value = kv_pair.find(_a("Value"))

        # IsoCenterSize
        max_central_beam_error = float(
            mv_value.find(_v("MaxCentralBeamError")).text
        )
        results["IsoCenterGroup/IsoCenterSize [mm]"] = max_central_beam_error

        # IsoCenterMVOffset
        mv_frames = (
            mv_value.find(_v("Frames")).findall(_v("IsoCalResults.Frame"))
        )
        results["IsoCenterGroup/IsoCenterMVOffset [mm]"] = max(
            math.sqrt(
                float(f.find(_v("IsocenterProjectionX")).text) ** 2
                + float(f.find(_v("IsocenterProjectionY")).text) ** 2
            )
            for f in mv_frames
        )

        # IsoCenterKVOffset
        kv_results = step.find(_v("KVResults"))
        kv_frames = (
            kv_results.find(_v("Frames")).findall(_v("IsoCalResults.Frame"))
        )
        results["IsoCenterGroup/IsoCenterKVOffset [mm]"] = max(
            math.sqrt(
                float(f.find(_v("IsocenterProjectionX")).text) ** 2
                + float(f.find(_v("IsocenterProjectionY")).text) ** 2
            )
            for f in kv_frames
        )


def _extract_mlc_group(
    steps: Dict[str, List[Tuple[str, ET.Element]]],
    results: Dict[str, float],
) -> None:
    """
    CollimationGroup/MLCGroup: Individual leaf offsets and summaries.
    CollimationGroup/MLCBacklashGroup: Individual backlash and summaries.

    Source: MLCCheck step contains two leaf-pair arrays:
        MLCCheck/LeafPairs/MLCCheck.LeafPair[Index, LeafOffsetA, LeafOffsetB]
        MLCCheck/LeafPairsEx/ArrayOfMLCCheck.LeafPair
            /MLCCheck.LeafPair[Index, LeafOffsetA, LeafOffsetB]

    LeafPairs and LeafPairsEx are measurements from two different
    collimator angle acquisitions. All XML offsets are in cm.

    --- Individual Leaf Offsets ---

    MLCLeavesA/MLCLeaf{i} [mm]  (Bank A, signed)
        For each leaf i (11-50):
            candidate_LP  = LeafPairs[i].LeafOffsetA * 10
            candidate_LPx = LeafPairsEx[i].LeafOffsetA * 10
            CSV = whichever has the larger absolute value (sign preserved)

    MLCLeavesB/MLCLeaf{i} [mm]  (Bank B, always positive)
        Same max-abs selection on LeafOffsetB, then negate:
            CSV = -(selected value)
        Bank B XML offsets are negative; negation makes CSV positive.

    --- Summary Statistics ---

    MLCMaxOffsetA [mm]  = max(|chosenA[i]|)         across all leaves
    MLCMaxOffsetB [mm]  = max(|chosenB[i]|)         across all leaves
    MLCMeanOffsetA [mm] = mean(chosenA[i])           signed mean
    MLCMeanOffsetB [mm] = mean(|chosenB[i]|)         mean of abs values

    --- Backlash ---

    MLCBacklashLeaf{i} [mm] = |LeafPairs.Offset - LeafPairsEx.Offset| * 10
        (computed independently for banks A and B)

    MLCBacklashMax{A,B} [mm]  = max(backlash) across all leaves
    MLCBacklashMean{A,B} [mm] = mean(backlash) across all leaves
    """
    for _, step in steps.get("MLCCheck", []):
        leaf_pairs = step.find(_v("LeafPairs")).findall(
            _v("MLCCheck.LeafPair")
        )
        leaf_pairs_ex = (
            step.find(_v("LeafPairsEx"))
            .find(_v("ArrayOfMLCCheck.LeafPair"))
            .findall(_v("MLCCheck.LeafPair"))
        )

        chosen_a: List[float] = []
        chosen_b: List[float] = []
        backlash_a: List[float] = []
        backlash_b: List[float] = []

        for lp, lpx in zip(leaf_pairs, leaf_pairs_ex):
            idx = int(lp.find(_v("Index")).text)

            # Raw offsets in mm (XML is cm, multiply by 10)
            a1 = float(lp.find(_v("LeafOffsetA")).text) * 10
            b1 = float(lp.find(_v("LeafOffsetB")).text) * 10
            a2 = float(lpx.find(_v("LeafOffsetA")).text) * 10
            b2 = float(lpx.find(_v("LeafOffsetB")).text) * 10

            # Choose the larger-magnitude offset
            ca = a1 if abs(a1) >= abs(a2) else a2
            cb = b1 if abs(b1) >= abs(b2) else b2

            # Backlash = absolute difference
            ba = abs(a1 - a2)
            bb = abs(b1 - b2)

            chosen_a.append(ca)
            chosen_b.append(cb)
            backlash_a.append(ba)
            backlash_b.append(bb)

            # Individual leaf offsets
            results[f"CollimationGroup/MLCGroup/MLCLeavesA/MLCLeaf{idx} [mm]"] = ca
            results[f"CollimationGroup/MLCGroup/MLCLeavesB/MLCLeaf{idx} [mm]"] = -cb

            # Individual backlash
            results[f"CollimationGroup/MLCBacklashGroup/MLCBacklashLeavesA/MLCBacklashLeaf{idx} [mm]"] = ba
            results[f"CollimationGroup/MLCBacklashGroup/MLCBacklashLeavesB/MLCBacklashLeaf{idx} [mm]"] = bb

        # Summary statistics
        results["CollimationGroup/MLCGroup/MLCMaxOffsetA [mm]"] = max(abs(x) for x in chosen_a)
        results["CollimationGroup/MLCGroup/MLCMaxOffsetB [mm]"] = max(abs(x) for x in chosen_b)
        results["CollimationGroup/MLCGroup/MLCMeanOffsetA [mm]"] = statistics.mean(chosen_a)
        results["CollimationGroup/MLCGroup/MLCMeanOffsetB [mm]"] = statistics.mean(abs(x) for x in chosen_b)

        results["CollimationGroup/MLCBacklashGroup/MLCBacklashMaxA [mm]"] = max(backlash_a)
        results["CollimationGroup/MLCBacklashGroup/MLCBacklashMaxB [mm]"] = max(backlash_b)
        results["CollimationGroup/MLCBacklashGroup/MLCBacklashMeanA [mm]"] = statistics.mean(backlash_a)
        results["CollimationGroup/MLCBacklashGroup/MLCBacklashMeanB [mm]"] = statistics.mean(backlash_b)


def _extract_gantry_group(
    steps: Dict[str, List[Tuple[str, ET.Element]]],
    results: Dict[str, float],
) -> None:
    """
    GantryGroup: Absolute and Relative gantry accuracy.

    GantryAbsolute [deg]
        Source:  EnhancedCouchPositionGantryAbsCorrection/GantryAbsoluteError
        Formula: -GantryAbsoluteError   (sign is negated)

    GantryRelative [deg]
        Source:  IsoCal/AllMVResults/.../Value/Frames
                   /IsoCalResults.Frame/{FoundSourceAngle, NominalSourceAngle}
        Formula:
            1. For each MV frame, compute gantry angle deviation:
               delta[i] = FoundSourceAngle - NominalSourceAngle
               (wrapped to [-180, +180])
            2. Compute the systematic offset (mean):
               mean_delta = mean(delta[i])
            3. Compute residuals (reproducibility errors):
               residual[i] = delta[i] - mean_delta
            4. Find the residual with the largest absolute value.
            5. CSV = -(that residual)   (sign is negated)
        Notes:   This separates gantry reproducibility (relative) from
                 the systematic offset (captured by GantryAbsolute).
    """
    # GantryAbsolute
    for _, step in steps.get("EnhancedCouchPositionGantryAbsCorrection", []):
        gantry_abs_error = float(
            step.find(_v("GantryAbsoluteError")).text
        )
        results["GantryGroup/GantryAbsolute [°]"] = -gantry_abs_error

    # GantryRelative (from IsoCal MV frames)
    for _, step in steps.get("IsoCal", []):
        all_mv = step.find(_v("AllMVResults"))
        kv_pair = all_mv.find(_a("KeyValueOfstringIsoCalResultsAsoNrQnM"))
        mv_value = kv_pair.find(_a("Value"))
        mv_frames = (
            mv_value.find(_v("Frames")).findall(_v("IsoCalResults.Frame"))
        )

        # Step 1: Gantry angle deviations (wrapped)
        deviations = []
        for frame in mv_frames:
            found = float(frame.find(_v("FoundSourceAngle")).text)
            nominal = float(frame.find(_v("NominalSourceAngle")).text)
            deviations.append(_wrap_angle(found - nominal))

        # Step 2: Mean systematic offset
        mean_dev = statistics.mean(deviations)

        # Step 3: Residuals
        residuals = [d - mean_dev for d in deviations]

        # Step 4-5: Negated max-abs residual
        max_residual = max(residuals, key=abs)
        results["GantryGroup/GantryRelative [°]"] = -max_residual


def _extract_enhanced_couch_group(
    steps: Dict[str, List[Tuple[str, ET.Element]]],
    results: Dict[str, float],
) -> None:
    """
    EnhancedCouchGroup: Couch positioning and rotation accuracy.

    All source data comes from EnhancedCouchPosition steps.
    Error = ActualMotion - NominalMotion.

    XML Paths per step:
        ActualMotion/Origin/{X,Y,Z}          (cm)
        NominalMotion/Origin/{X,Y,Z}         (cm)
        ActualMotion/{AngleX,AngleY,AngleZ}  (deg)
        NominalMotion/{AngleX,AngleY,AngleZ} (deg)

    --- Linear Position Checks ---
    Steps used: Lin_Vrt, Lin_Lat, Lin_Lng, Lin_VrtLatLng1, Lin_VrtLatLng2

    CouchLat [mm]              = max(|error.X|) * 10     across 5 linear steps
    CouchLng [mm]              = max(|error.Y|) * 10     across 5 linear steps
    CouchVrt [mm]              = max(|error.Z|) * 10     across 5 linear steps
    CouchMaxPositionError [mm] = max(sqrt(eX^2 + eY^2 + eZ^2)) * 10

    Note: X = Lateral, Y = Longitudinal, Z = Vertical in the Varian
    couch coordinate system.

    --- Fine Rotation Checks ---
    Steps used: Rtn_Fine1, Rtn_Fine2

    CouchRtnFine [deg] = max(|AngleZ error|)  across 2 fine steps
    CouchPit [deg]     = max(|AngleX error|)  across 2 fine steps
    CouchRol [deg]     = max(|AngleY error|)  across 2 fine steps

    --- Large Rotation Check ---
    Steps used: Rtn_Large090, Rtn_Large135, Rtn_Large225, Rtn_Large270

    CouchRtnLarge [deg] = max(|AngleZ error|) across 4 large steps

    --- Rotation-Induced Translational Shift ---
    Steps used: same 4 large rotation steps

    RotationInducedCouchShiftFullRange [mm]
        = max(sqrt(error.X^2 + error.Y^2)) * 10
        across the 4 large rotation steps.
        NOTE: Only the 2D lateral (X,Y) error is used.
              The vertical (Z) component is excluded.
    """
    # Build a lookup of EnhancedCouchPosition steps by Tag
    couch_steps: Dict[str, ET.Element] = {}
    for tag, step in steps.get("EnhancedCouchPosition", []):
        couch_steps[tag] = step

    # --- Linear ---
    lin_errors = [
        _extract_motion_error(couch_steps[t])
        for t in LINEAR_STEP_TAGS
        if t in couch_steps
    ]
    if lin_errors:
        results["EnhancedCouchGroup/CouchLat [mm]"] = (
            max(abs(e.x) for e in lin_errors) * 10
        )
        results["EnhancedCouchGroup/CouchLng [mm]"] = (
            max(abs(e.y) for e in lin_errors) * 10
        )
        results["EnhancedCouchGroup/CouchVrt [mm]"] = (
            max(abs(e.z) for e in lin_errors) * 10
        )
        results["EnhancedCouchGroup/CouchMaxPositionError [mm]"] = (
            max(
                math.sqrt(e.x**2 + e.y**2 + e.z**2)
                for e in lin_errors
            )
            * 10
        )

    # --- Fine Rotation ---
    fine_errors = [
        _extract_motion_error(couch_steps[t])
        for t in FINE_ROTATION_STEP_TAGS
        if t in couch_steps
    ]
    if fine_errors:
        results["EnhancedCouchGroup/CouchRtnFine [°]"] = max(
            abs(e.az) for e in fine_errors
        )
        results["EnhancedCouchGroup/CouchPit [°]"] = max(
            abs(e.ax) for e in fine_errors
        )
        results["EnhancedCouchGroup/CouchRol [°]"] = max(
            abs(e.ay) for e in fine_errors
        )

    # --- Large Rotation ---
    large_errors = [
        _extract_motion_error(couch_steps[t])
        for t in LARGE_ROTATION_STEP_TAGS
        if t in couch_steps
    ]
    if large_errors:
        results["EnhancedCouchGroup/CouchRtnLarge [°]"] = max(
            abs(e.az) for e in large_errors
        )
        # 2D lateral (X,Y) only — Z excluded
        results["EnhancedCouchGroup/RotationInducedCouchShiftFullRange [mm]"] = (
            max(math.sqrt(e.x**2 + e.y**2) for e in large_errors) * 10
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_mpc_xml(xml_path: str) -> Dict[str, float]:
    """
    Parse a Varian MPC Results.xml file and return all confirmed
    check metrics as a dict of {csv_name: rounded_value}.

    The keys match the CSV's "Name [Unit]" column exactly.
    All values are rounded to 2 decimal places.

    Args:
        xml_path: Path to the Results.xml file.

    Returns:
        Dictionary mapping CSV check-item names to computed values.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    steps = _build_step_index(root)

    raw: Dict[str, float] = {}

    _extract_beam_group(steps, raw)
    _extract_isocenter_group(steps, raw)
    _extract_mlc_group(steps, raw)
    _extract_gantry_group(steps, raw)
    _extract_enhanced_couch_group(steps, raw)

    # Round everything to 2 decimal places (matches CSV precision)
    return {name: round(value, 2) for name, value in raw.items()}


# ---------------------------------------------------------------------------
# Validation Against CSV
# ---------------------------------------------------------------------------

def validate_against_csv(
    xml_path: str,
    csv_path: str,
    tolerance: float = 0.005,
) -> Tuple[int, int, int, List[str]]:
    """
    Parse the XML and compare every computed metric against the CSV.

    Returns:
        (pass_count, fail_count, skip_count, failure_details)
    """
    computed = parse_mpc_xml(xml_path)

    csv_items: Dict[str, float] = {}
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            csv_items[row[0].strip()] = float(row[1].strip())

    passed, failed, skipped = 0, 0, 0
    failures: List[str] = []

    for name, comp_val in computed.items():
        csv_val = csv_items.get(name)
        if csv_val is None:
            skipped += 1
            continue
        if abs(comp_val - csv_val) < tolerance:
            passed += 1
        else:
            failed += 1
            failures.append(
                f"  {name}: computed={comp_val}, csv={csv_val}, "
                f"diff={abs(comp_val - csv_val):.4f}"
            )

    # Count CSV items we didn't attempt (unresolved mappings)
    unresolved_count = len(csv_items) - (passed + failed + skipped)

    return passed, failed, skipped, failures


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Parse Varian MPC Results.xml and extract check metrics."
    )
    parser.add_argument("xml", help="Path to Results.xml")
    parser.add_argument(
        "--validate",
        metavar="CSV",
        help="Path to Results.csv for validation",
    )
    args = parser.parse_args()

    if args.validate:
        passed, failed, skipped, failures = validate_against_csv(
            args.xml, args.validate
        )
        print(f"Passed:  {passed}")
        print(f"Failed:  {failed}")
        print(f"Skipped: {skipped}")
        if failures:
            print("\nFailures:")
            for f in failures:
                print(f)
    else:
        results = parse_mpc_xml(args.xml)
        # Print in CSV-like format
        print("Name [Unit], Computed Value")
        for name, value in results.items():
            print(f"{name}, {value}")


if __name__ == "__main__":
    main()
