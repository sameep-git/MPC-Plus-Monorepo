"""
Unified extractor for MPC beam Results.xml files.

Given a path (either directly to a Results.xml file or to its containing
folder) and an already-initialised beam model, this module:
- Detects the beam type from the folder name
- Calls the appropriate low-level extractor
- Populates the model object via its setters
- Returns the populated model

Supported model types:
    - EBeamModel  → relative output, relative uniformity
    - XBeamModel  → relative output, relative uniformity, center shift
    - GeoModel    → all geometry/MLC fields extracted from XML
"""

import os
import sys

try:
    from src.data_manipulation.ETL.extractors.xml.ebeam_extractor import extract_ebeam_values
    from src.data_manipulation.ETL.extractors.xml.xbeam_extractor import extract_xbeam_values
    from src.data_manipulation.ETL.extractors.xml.geometry_extractor import extract_geometry_values, is_geometry_folder
    from src.data_manipulation.models.EBeamModel import EBeamModel
    from src.data_manipulation.models.XBeamModel import XBeamModel
    from src.data_manipulation.models.GeoModel import GeoModel
except ImportError:
    from ebeam_extractor import extract_ebeam_values
    from xbeam_extractor import extract_xbeam_values
    from geometry_extractor import extract_geometry_values, is_geometry_folder
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))
    from src.data_manipulation.models.EBeamModel import EBeamModel
    from src.data_manipulation.models.XBeamModel import XBeamModel
    from src.data_manipulation.models.GeoModel import GeoModel


def detect_beam_type(path: str) -> str:
    """
    Detect beam type from folder or file path.
    Returns 'ebeam', 'xbeam', 'geometry', or 'unknown'.
    """
    folder_path, _ = _normalize_paths(path)
    check_path = folder_path if os.path.isdir(folder_path) else os.path.dirname(folder_path)
    if is_geometry_folder(check_path):
        return "geometry"
    folder_name = os.path.basename(check_path)
    if "BeamCheckTemplate" in folder_name:
        for indicator in ("6e", "9e", "12e", "16e", "20e"):
            if indicator in folder_name:
                return "ebeam"
        return "xbeam"
    return "unknown"


def _normalize_paths(path: str):
    """
    Normalize an input path to both (folder_path, xml_path).

    The caller can pass either:
    - a folder containing Results.xml
    - a direct path to Results.xml

    Handles relative paths by trying to resolve them relative to MPC-Plus directory.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mpc_plus_dir = os.path.abspath(os.path.join(script_dir, '../../../..'))

    path = path.replace('\\', os.sep).replace('/', os.sep)

    resolved_path = None

    if os.path.isabs(path) and os.path.exists(path):
        resolved_path = path
    elif not os.path.isabs(path):
        possible_paths = [
            os.path.join(mpc_plus_dir, path),
            os.path.join(os.getcwd(), path),
        ]

        if path.startswith('data' + os.sep) or path.startswith('data/'):
            possible_paths.insert(0, os.path.join(mpc_plus_dir, path))

        for alt_path in possible_paths:
            if os.path.exists(alt_path):
                resolved_path = os.path.abspath(alt_path)
                break

        if not resolved_path:
            resolved_path = os.path.abspath(path)
    else:
        resolved_path = path

    if os.path.isdir(resolved_path):
        folder_path = resolved_path
        xml_path = os.path.join(folder_path, "Results.xml")
    else:
        xml_path = resolved_path
        folder_path = os.path.dirname(xml_path)

    return folder_path, xml_path


def extract_beam_values(path: str, model):
    """
    Unified entrypoint to extract beam QA values into a model object.

    Args:
        path:  Folder containing Results.xml OR direct path to Results.xml.
        model: A pre-initialised beam model instance (EBeamModel, XBeamModel,
               or GeoModel). Its setters will be called with the extracted values.

    Returns:
        The same model object with its fields populated, or None on failure.
    """
    model_type = type(model).__name__.lower()
    folder_path, xml_path = _normalize_paths(path)

    # -------------------------------------------------------------------------
    # E-beam: relative output + relative uniformity
    # -------------------------------------------------------------------------
    if "ebeam" in model_type:
        if not isinstance(model, EBeamModel):
            raise TypeError(
                f"Expected EBeamModel for ebeam path, got {type(model).__name__}"
            )
        output, uniformity = extract_ebeam_values(xml_path)
        if output is None or uniformity is None:
            return None

        from decimal import Decimal
        model.set_relative_output(Decimal(str(output)))
        model.set_relative_uniformity(Decimal(str(uniformity)))
        return model

    # -------------------------------------------------------------------------
    # X-beam: relative output + relative uniformity + center shift
    # -------------------------------------------------------------------------
    if "xbeam" in model_type:
        if not isinstance(model, XBeamModel):
            raise TypeError(
                f"Expected XBeamModel for xbeam path, got {type(model).__name__}"
            )
        output, uniformity, center_shift = extract_xbeam_values(folder_path)
        if output is None or uniformity is None:
            return None

        from decimal import Decimal
        model.set_relative_output(Decimal(str(output)))
        model.set_relative_uniformity(Decimal(str(uniformity)))
        if center_shift is not None:
            model.set_center_shift(Decimal(str(center_shift)))
        return model

    # -------------------------------------------------------------------------
    # Geometry: full MLC + beam profile fields via GeoModel
    # -------------------------------------------------------------------------
    if "geo" in model_type:
        if not isinstance(model, GeoModel):
            raise TypeError(
                f"Expected GeoModel for geometry path, got {type(model).__name__}"
            )
        data = extract_geometry_values(folder_path)
        if data is None:
            return None

        from decimal import Decimal

        # --- Beam profile ---
        if data.get("beam_output_change") is not None:
            model.set_relative_output(Decimal(str(data["beam_output_change"])))
        if data.get("beam_uniformity_change") is not None:
            model.set_relative_uniformity(Decimal(str(data["beam_uniformity_change"])))
        if data.get("beam_center_shift") is not None:
            model.set_center_shift(Decimal(str(data["beam_center_shift"])))

        # --- MLC leaves A & B ---
        for idx, val in data.get("mlc_leaves_a", {}).items():
            model.set_MLCLeafA(idx, val)
        for idx, val in data.get("mlc_leaves_b", {}).items():
            model.set_MLCLeafB(idx, val)

        # --- MLC offsets ---
        if data.get("mlc_max_offset_a") is not None:
            model.set_MaxOffsetA(data["mlc_max_offset_a"])
        if data.get("mlc_max_offset_b") is not None:
            model.set_MaxOffsetB(data["mlc_max_offset_b"])
        if data.get("mlc_mean_offset_a") is not None:
            model.set_MeanOffsetA(data["mlc_mean_offset_a"])
        if data.get("mlc_mean_offset_b") is not None:
            model.set_MeanOffsetB(data["mlc_mean_offset_b"])

        # --- MLC backlash leaves A & B ---
        for idx, val in data.get("mlc_backlash_a", {}).items():
            model.set_MLCBacklashA(idx, val)
        for idx, val in data.get("mlc_backlash_b", {}).items():
            model.set_MLCBacklashB(idx, val)

        # --- MLC backlash summary stats ---
        if data.get("mlc_backlash_max_a") is not None:
            model.set_MLCBacklashMaxA(data["mlc_backlash_max_a"])
        if data.get("mlc_backlash_max_b") is not None:
            model.set_MLCBacklashMaxB(data["mlc_backlash_max_b"])
        if data.get("mlc_backlash_mean_a") is not None:
            model.set_MLCBacklashMeanA(data["mlc_backlash_mean_a"])
        if data.get("mlc_backlash_mean_b") is not None:
            model.set_MLCBacklashMeanB(data["mlc_backlash_mean_b"])

        # --- IsoCenter ---
        if data.get("iso_center_size") is not None:
            model.set_IsoCenterSize(Decimal(str(data["iso_center_size"])))
        if data.get("iso_center_mv_offset") is not None:
            model.set_IsoCenterMVOffset(Decimal(str(data["iso_center_mv_offset"])))
        if data.get("iso_center_kv_offset") is not None:
            model.set_IsoCenterKVOffset(Decimal(str(data["iso_center_kv_offset"])))

        # --- Gantry ---
        if data.get("gantry_absolute") is not None:
            model.set_GantryAbsolute(Decimal(str(data["gantry_absolute"])))
        if data.get("gantry_relative") is not None:
            model.set_GantryRelative(Decimal(str(data["gantry_relative"])))

        # --- Couch ---
        if data.get("couch_lat") is not None:
            model.set_CouchLat(Decimal(str(data["couch_lat"])))
        if data.get("couch_lng") is not None:
            model.set_CouchLng(Decimal(str(data["couch_lng"])))
        if data.get("couch_vrt") is not None:
            model.set_CouchVrt(Decimal(str(data["couch_vrt"])))
        if data.get("couch_max_position_error") is not None:
            model.set_CouchMaxPositionError(Decimal(str(data["couch_max_position_error"])))
        if data.get("couch_rtn_fine") is not None:
            model.set_CouchRtnFine(Decimal(str(data["couch_rtn_fine"])))
        if data.get("couch_rtn_large") is not None:
            model.set_CouchRtnLarge(Decimal(str(data["couch_rtn_large"])))
        if data.get("rotation_induced_couch_shift_full_range") is not None:
            model.set_RotationInducedCouchShiftFullRange(Decimal(str(data["rotation_induced_couch_shift_full_range"])))

        return model

    # Unknown / unsupported beam type
    return None


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: xml_beam_extractor_entry.py <ebeam|xbeam|geo> <folder_or_results_xml_path>")
        sys.exit(1)

    beam_arg = sys.argv[1].lower()
    input_path = sys.argv[2]

    if beam_arg == "ebeam":
        test_model = EBeamModel()
    elif beam_arg == "xbeam":
        test_model = XBeamModel()
    elif beam_arg == "geo":
        test_model = GeoModel()
    else:
        print(f"Unknown beam type: {beam_arg}. Use ebeam, xbeam, or geo.")
        sys.exit(1)

    result = extract_beam_values(input_path, test_model)
    if not result:
        print("Failed to extract values.")
        sys.exit(1)

    print(f"Relative Output    : {result.get_relative_output()}")
    print(f"Relative Uniformity: {result.get_relative_uniformity()}")
    if hasattr(result, "get_center_shift"):
        print(f"Center Shift       : {result.get_center_shift()}")
