"""
Tests for AbstractBeamModel, XBeamModel, EBeamModel, GeoModel, and ImageModel.
"""

import os
import sys
import pytest
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Path setup so imports resolve from the backend root
# ---------------------------------------------------------------------------
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from src.data_manipulation.models.XBeamModel import XBeamModel
from src.data_manipulation.models.EBeamModel import EBeamModel
from src.data_manipulation.models.GeoModel import GeoModel
from src.data_manipulation.models.ImageModel import ImageModel


# ===========================================================================
# Helpers
# ===========================================================================

def make_check_xml(directory: str, is_baseline: bool) -> str:
    """Write a minimal Check.xml into *directory* and return its path."""
    xml_content = f"""<?xml version="1.0" encoding="utf-8"?>
<Check xmlns="http://www.varian.com/MPC">
    <IsBaseline>{"true" if is_baseline else "false"}</IsBaseline>
</Check>
"""
    check_path = os.path.join(directory, "Check.xml")
    with open(check_path, "w", encoding="utf-8") as f:
        f.write(xml_content)
    return check_path


# ===========================================================================
# AbstractBeamModel – utility methods (tested via XBeamModel)
# ===========================================================================

class TestGetDateFromPathName:
    """_getDateFromPathName extracts datetime from a folder-style path."""

    def test_valid_path_returns_correct_datetime(self):
        model = XBeamModel()
        path = r"C:\data\NDS-WKS-SN6543-2025-09-19-07-41-49-0008-BeamCheckTemplate10x\Results.csv"
        result = model._getDateFromPathName(path)
        assert result == datetime(2025, 9, 19, 7, 41, 49)

    def test_another_valid_path(self):
        model = XBeamModel()
        path = "/Users/alex/Desktop/MPC Data/NDS-WKS-SN5512-2015-09-17-07-08-59-0002-BeamCheckTemplate10x/Results.csv"
        result = model._getDateFromPathName(path)
        assert result == datetime(2015, 9, 17, 7, 8, 59)

    def test_path_without_date_raises_value_error(self):
        model = XBeamModel()
        with pytest.raises(ValueError, match="Could not extract date from path"):
            model._getDateFromPathName("/no/date/in/this/path/Results.csv")

    def test_returns_datetime_type(self):
        model = XBeamModel()
        path = "NDS-WKS-SN1234-2023-01-15-10-30-00-0001-BeamCheckTemplate6e"
        result = model._getDateFromPathName(path)
        assert isinstance(result, datetime)


class TestGetSNFromPathName:
    """_getSNFromPathName extracts the machine serial number from a path."""

    def test_standard_sn(self):
        model = XBeamModel()
        path = "NDS-WKS-SN6543-2025-09-19-07-41-49-0008-GeometryCheck"
        assert model._getSNFromPathName(path) == "SN6543"

    def test_short_sn(self):
        model = XBeamModel()
        path = "/data/NDS-WKS-SN42-2020-01-01-00-00-00-0001-Check"
        assert model._getSNFromPathName(path) == "SN42"

    def test_path_without_sn_raises_value_error(self):
        model = XBeamModel()
        with pytest.raises(ValueError, match="Could not extract serial number"):
            model._getSNFromPathName("/path/without/sn/Results.csv")

    def test_returns_string_with_sn_prefix(self):
        model = XBeamModel()
        path = "SN9999-rest-of-path"
        result = model._getSNFromPathName(path)
        assert result.startswith("SN")


class TestGetIsBaselineFromPathName:
    """_getIsBaselineFromPathName reads Check.xml for the IsBaseline value."""

    def test_returns_false_when_xml_says_false(self, tmp_path):
        make_check_xml(str(tmp_path), is_baseline=False)
        results_path = str(tmp_path / "Results.csv")
        model = XBeamModel()
        assert model._getIsBaselineFromPathName(results_path) is False

    def test_returns_true_when_xml_says_true(self, tmp_path):
        make_check_xml(str(tmp_path), is_baseline=True)
        results_path = str(tmp_path / "Results.csv")
        model = XBeamModel()
        assert model._getIsBaselineFromPathName(results_path) is True

    def test_raises_file_not_found_when_no_check_xml(self, tmp_path):
        results_path = str(tmp_path / "Results.csv")
        model = XBeamModel()
        with pytest.raises(FileNotFoundError, match="Check.xml not found"):
            model._getIsBaselineFromPathName(results_path)

    def test_raises_value_error_for_malformed_xml(self, tmp_path):
        bad_xml_path = str(tmp_path / "Check.xml")
        with open(bad_xml_path, "w") as f:
            f.write("<<< NOT VALID XML >>>")
        results_path = str(tmp_path / "Results.csv")
        model = XBeamModel()
        with pytest.raises(ValueError):
            model._getIsBaselineFromPathName(results_path)

    def test_raises_value_error_when_is_baseline_tag_missing(self, tmp_path):
        xml_content = '<?xml version="1.0"?><Check xmlns="http://www.varian.com/MPC"></Check>'
        check_path = str(tmp_path / "Check.xml")
        with open(check_path, "w") as f:
            f.write(xml_content)
        results_path = str(tmp_path / "Results.csv")
        model = XBeamModel()
        with pytest.raises(ValueError, match="IsBaseline"):
            model._getIsBaselineFromPathName(results_path)


# ===========================================================================
# AbstractBeamModel – getters / setters (tested via XBeamModel)
# ===========================================================================

class TestAbstractBeamModelGettersSetters:
    def setup_method(self):
        self.model = XBeamModel()

    def test_default_type_is_empty_string(self):
        assert self.model.get_type() == ""

    def test_set_and_get_type(self):
        self.model.set_type("10x")
        assert self.model.get_type() == "10x"

    def test_default_date_is_none(self):
        assert self.model.get_date() is None

    def test_set_and_get_date(self):
        dt = datetime(2025, 1, 1)
        self.model.set_date(dt)
        assert self.model.get_date() == dt

    def test_default_path_is_empty_string(self):
        assert self.model.get_path() == ""

    def test_set_and_get_path(self):
        self.model.set_path("/some/path")
        assert self.model.get_path() == "/some/path"

    def test_default_machine_sn_is_none(self):
        assert self.model.get_machine_SN() is None

    def test_set_and_get_machine_sn(self):
        self.model.set_machine_SN("SN1234")
        assert self.model.get_machine_SN() == "SN1234"

    def test_default_baseline_is_false(self):
        assert self.model.get_baseline() is False

    def test_set_and_get_baseline(self):
        self.model.set_baseline(True)
        assert self.model.get_baseline() is True

    def test_default_image_model_is_none(self):
        assert self.model.get_image_model() is None

    def test_set_and_get_image_model(self):
        mock_image = MagicMock()
        self.model.set_image_model(mock_image)
        assert self.model.get_image_model() is mock_image

    def test_set_and_get_symmetry_horizontal(self):
        self.model.set_symmetry_horizontal(1.23)
        assert self.model.get_symmetry_horizontal() == 1.23

    def test_set_and_get_symmetry_vertical(self):
        self.model.set_symmetry_vertical(0.99)
        assert self.model.get_symmetry_vertical() == 0.99

    def test_set_and_get_flatness_horizontal(self):
        self.model.set_flatness_horizontal(2.5)
        assert self.model.get_flatness_horizontal() == 2.5

    def test_set_and_get_flatness_vertical(self):
        self.model.set_flatness_vertical(3.1)
        assert self.model.get_flatness_vertical() == 3.1

    def test_set_and_get_horizontal_profile_graph(self):
        mock_fig = MagicMock()
        self.model.set_horizontal_profile_graph(mock_fig)
        assert self.model.get_horizontal_profile_graph() is mock_fig

    def test_set_and_get_vertical_profile_graph(self):
        mock_fig = MagicMock()
        self.model.set_vertical_profile_graph(mock_fig)
        assert self.model.get_vertical_profile_graph() is mock_fig


class TestSetFlatAndSymValsFromImage:
    """set_flat_and_sym_vals_from_image copies metrics from the attached ImageModel."""

    def test_copies_flatness_and_symmetry_from_image_model(self):
        beam = XBeamModel()
        mock_image = MagicMock()
        mock_image.get_flatness_horizontal.return_value = 1.1
        mock_image.get_flatness_vertical.return_value = 1.2
        mock_image.get_symmetry_horizontal.return_value = 0.8
        mock_image.get_symmetry_vertical.return_value = 0.9
        mock_image.get_horizontal_profile_graph.return_value = "fig_h"
        mock_image.get_vertical_profile_graph.return_value = "fig_v"

        beam.set_image_model(mock_image)
        beam.set_flat_and_sym_vals_from_image()

        assert beam.get_flatness_horizontal() == 1.1
        assert beam.get_flatness_vertical() == 1.2
        assert beam.get_symmetry_horizontal() == 0.8
        assert beam.get_symmetry_vertical() == 0.9
        assert beam.get_horizontal_profile_graph() == "fig_h"
        assert beam.get_vertical_profile_graph() == "fig_v"


# ===========================================================================
# XBeamModel
# ===========================================================================

class TestXBeamModel:
    def setup_method(self):
        self.model = XBeamModel()

    def test_defaults_relative_uniformity(self):
        assert self.model.get_relative_uniformity() == Decimal("0.0")

    def test_defaults_relative_output(self):
        assert self.model.get_relative_output() == Decimal("0.0")

    def test_defaults_center_shift(self):
        assert self.model.get_center_shift() == Decimal("0.0")

    def test_defaults_type_id_is_none(self):
        assert self.model.get_typeID() is None

    def test_set_and_get_relative_uniformity(self):
        self.model.set_relative_uniformity(Decimal("1.23"))
        assert self.model.get_relative_uniformity() == Decimal("1.23")

    def test_set_and_get_relative_output(self):
        self.model.set_relative_output(Decimal("0.98"))
        assert self.model.get_relative_output() == Decimal("0.98")

    def test_set_and_get_center_shift(self):
        self.model.set_center_shift(Decimal("0.05"))
        assert self.model.get_center_shift() == Decimal("0.05")

    def test_set_and_get_type_id(self):
        uid = "14ddae42-77a5-4e6a-8f27-6c2b98cb9780"
        self.model.set_typeID(uid)
        assert self.model.get_typeID() == uid

    def test_inherits_abstract_setters(self):
        self.model.set_type("10x")
        self.model.set_machine_SN("SN6543")
        assert self.model.get_type() == "10x"
        assert self.model.get_machine_SN() == "SN6543"


# ===========================================================================
# EBeamModel
# ===========================================================================

class TestEBeamModel:
    def setup_method(self):
        self.model = EBeamModel()

    def test_defaults_relative_uniformity(self):
        assert self.model.get_relative_uniformity() == Decimal("0.0")

    def test_defaults_relative_output(self):
        assert self.model.get_relative_output() == Decimal("0.0")

    def test_defaults_type_id_is_none(self):
        assert self.model.get_typeID() is None

    def test_set_and_get_relative_uniformity(self):
        self.model.set_relative_uniformity(Decimal("2.5"))
        assert self.model.get_relative_uniformity() == Decimal("2.5")

    def test_set_and_get_relative_output(self):
        self.model.set_relative_output(Decimal("1.01"))
        assert self.model.get_relative_output() == Decimal("1.01")

    def test_set_and_get_type_id(self):
        uid = "e6763342-a180-444a-a869-ce57d1b086b1"
        self.model.set_typeID(uid)
        assert self.model.get_typeID() == uid

    def test_no_center_shift_attribute(self):
        """EBeamModel does not have center shift – confirm AttributeError."""
        with pytest.raises(AttributeError):
            _ = self.model.get_center_shift()


# ===========================================================================
# GeoModel
# ===========================================================================

class TestGeoModel:
    def setup_method(self):
        self.model = GeoModel()

    # --- Default values ---
    def test_default_iso_center_size(self):
        assert self.model.get_IsoCenterSize() == Decimal("0.0")

    def test_default_gantry_absolute(self):
        assert self.model.get_GantryAbsolute() == Decimal("0.0")

    def test_default_jaw_x1(self):
        assert self.model.get_JawX1() == Decimal("0.0")

    def test_default_mlc_leaves_a_all_zero(self):
        for i in range(1, 61):
            assert self.model.get_MLCLeafA(i) == Decimal("0.0")

    def test_default_mlc_leaves_b_all_zero(self):
        for i in range(1, 61):
            assert self.model.get_MLCLeafB(i) == Decimal("0.0")

    # --- Setters convert to Decimal from various types ---
    def test_set_iso_center_size_from_string(self):
        self.model.set_IsoCenterSize("1.5")
        assert self.model.get_IsoCenterSize() == Decimal("1.5")

    def test_set_iso_center_mv_offset(self):
        self.model.set_IsoCenterMVOffset(0.25)
        assert self.model.get_IsoCenterMVOffset() == Decimal("0.25")

    def test_set_iso_center_kv_offset(self):
        self.model.set_IsoCenterKVOffset(0.1)
        assert self.model.get_IsoCenterKVOffset() == Decimal("0.1")

    def test_set_relative_output(self):
        self.model.set_relative_output("1.02")
        assert self.model.get_relative_output() == Decimal("1.02")

    def test_set_relative_uniformity(self):
        self.model.set_relative_uniformity("0.98")
        assert self.model.get_relative_uniformity() == Decimal("0.98")

    def test_set_center_shift(self):
        self.model.set_center_shift("0.03")
        assert self.model.get_center_shift() == Decimal("0.03")

    def test_set_collimation_rotation_offset(self):
        self.model.set_CollimationRotationOffset(0.5)
        assert self.model.get_CollimationRotationOffset() == Decimal("0.5")

    def test_set_gantry_relative(self):
        self.model.set_GantryRelative(0.3)
        assert self.model.get_GantryRelative() == Decimal("0.3")

    def test_set_couch_lat(self):
        self.model.set_CouchLat(1.1)
        assert self.model.get_CouchLat() == Decimal("1.1")

    def test_set_couch_lng(self):
        self.model.set_CouchLng(2.2)
        assert self.model.get_CouchLng() == Decimal("2.2")

    def test_set_couch_vrt(self):
        self.model.set_CouchVrt(3.3)
        assert self.model.get_CouchVrt() == Decimal("3.3")

    def test_set_couch_rtn_fine(self):
        self.model.set_CouchRtnFine(0.1)
        assert self.model.get_CouchRtnFine() == Decimal("0.1")

    def test_set_couch_rtn_large(self):
        self.model.set_CouchRtnLarge(0.2)
        assert self.model.get_CouchRtnLarge() == Decimal("0.2")

    def test_set_rotation_induced_couch_shift(self):
        self.model.set_RotationInducedCouchShiftFullRange(0.7)
        assert self.model.get_RotationInducedCouchShiftFullRange() == Decimal("0.7")

    def test_set_and_get_mlc_leaf_a(self):
        self.model.set_MLCLeafA(1, "0.12")
        assert self.model.get_MLCLeafA(1) == Decimal("0.12")

    def test_set_and_get_mlc_leaf_b(self):
        self.model.set_MLCLeafB(60, "0.99")
        assert self.model.get_MLCLeafB(60) == Decimal("0.99")

    def test_set_max_offset_a(self):
        self.model.set_MaxOffsetA(0.5)
        assert self.model.get_MaxOffsetA() == Decimal("0.5")

    def test_set_max_offset_b(self):
        self.model.set_MaxOffsetB(0.6)
        assert self.model.get_MaxOffsetB() == Decimal("0.6")

    def test_set_mean_offset_a(self):
        self.model.set_MeanOffsetA(0.3)
        assert self.model.get_MeanOffsetA() == Decimal("0.3")

    def test_set_mean_offset_b(self):
        self.model.set_MeanOffsetB(0.4)
        assert self.model.get_MeanOffsetB() == Decimal("0.4")

    def test_set_mlc_backlash_a(self):
        self.model.set_MLCBacklashA(5, "0.08")
        assert self.model.get_MLCBacklashA(5) == Decimal("0.08")

    def test_set_mlc_backlash_b(self):
        self.model.set_MLCBacklashB(10, "0.07")
        assert self.model.get_MLCBacklashB(10) == Decimal("0.07")

    def test_set_mlc_backlash_max_a(self):
        self.model.set_MLCBacklashMaxA(0.15)
        assert self.model.get_MLCBacklashMaxA() == Decimal("0.15")

    def test_set_mlc_backlash_max_b(self):
        self.model.set_MLCBacklashMaxB(0.16)
        assert self.model.get_MLCBacklashMaxB() == Decimal("0.16")

    def test_set_mlc_backlash_mean_a(self):
        self.model.set_MLCBacklashMeanA(0.06)
        assert self.model.get_MLCBacklashMeanA() == Decimal("0.06")

    def test_set_mlc_backlash_mean_b(self):
        self.model.set_MLCBacklashMeanB(0.07)
        assert self.model.get_MLCBacklashMeanB() == Decimal("0.07")

    def test_set_jaw_x1(self):
        self.model.set_JawX1(0.11)
        assert self.model.get_JawX1() == Decimal("0.11")

    def test_set_jaw_x2(self):
        self.model.set_JawX2(0.22)
        assert self.model.get_JawX2() == Decimal("0.22")

    def test_set_jaw_y1(self):
        self.model.set_JawY1(0.33)
        assert self.model.get_JawY1() == Decimal("0.33")

    def test_set_jaw_y2(self):
        self.model.set_JawY2(0.44)
        assert self.model.get_JawY2() == Decimal("0.44")

    def test_set_jaw_parallelism_x1(self):
        self.model.set_JawParallelismX1(0.01)
        assert self.model.get_JawParallelismX1() == Decimal("0.01")

    def test_set_jaw_parallelism_x2(self):
        self.model.set_JawParallelismX2(0.02)
        assert self.model.get_JawParallelismX2() == Decimal("0.02")

    def test_set_jaw_parallelism_y1(self):
        self.model.set_JawParallelismY1(0.03)
        assert self.model.get_JawParallelismY1() == Decimal("0.03")

    def test_set_jaw_parallelism_y2(self):
        self.model.set_JawParallelismY2(0.04)
        assert self.model.get_JawParallelismY2() == Decimal("0.04")

    def test_set_type_id(self):
        uid = "253c1694-12d0-4497-9bd0-8487ee7c6f6f"
        self.model.set_typeID(uid)
        assert self.model.get_typeID() == uid


# ===========================================================================
# ImageModel
# ===========================================================================

class TestImageModel:
    def setup_method(self):
        self.model = ImageModel()

    def test_set_and_get_flood_image_path(self):
        self.model.set_flood_image_path("/path/to/Floodfield-Raw.xim")
        assert self.model.get_flood_image_path() == "/path/to/Floodfield-Raw.xim"

    def test_set_and_get_dark_image_path(self):
        self.model.set_dark_image_path("/path/to/Offset.dat")
        assert self.model.get_dark_image_path() == "/path/to/Offset.dat"

    def test_set_and_get_image(self):
        mock_img = MagicMock()
        self.model.set_image(mock_img)
        assert self.model.get_image() is mock_img

    def test_set_and_get_image_name(self):
        self.model.set_image_name("SN6543/20250919/10x/074149/BeamProfileCheck")
        assert self.model.get_image_name() == "SN6543/20250919/10x/074149/BeamProfileCheck"

    def test_generate_image_name_format(self):
        self.model.set_machine_SN("SN6543")
        self.model.set_type("10x")
        self.model.set_date(datetime(2025, 9, 19, 7, 41, 49))
        name = self.model.generate_image_name()
        # Expected: SN6543/20250919/10x/074149/BeamProfileCheck
        assert name == "SN6543/20250919/10x/074149/BeamProfileCheck"

    def test_convert_xim_to_png_raises_when_no_image(self):
        """convert_XIM_to_PNG should raise ValueError when no image is set."""
        self.model.set_image(None)
        with pytest.raises(ValueError, match="No XIM image set"):
            self.model.convert_XIM_to_PNG()

    def test_convert_xim_to_png_converts_to_numpy_array(self):
        import numpy as np
        # Simulate an XIM image by using a numpy array (same as XIM's np.asarray result)
        dummy_array = np.ones((10, 10), dtype=np.float32)
        self.model.set_image(dummy_array)
        self.model.convert_XIM_to_PNG()
        result = self.model.get_image()
        assert isinstance(result, np.ndarray)
        assert result.shape == (10, 10)
