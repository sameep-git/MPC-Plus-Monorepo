"""
Tests for the data_extractor ETL class.

Strategy: write minimal CSV content to a temp directory, set the model
path to that directory, then call the extractor and verify that the
model's getters return the expected Decimal values.
"""

import os
import sys
import csv
import pytest
import tempfile
from decimal import Decimal

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from src.data_manipulation.ETL.data_extractor import data_extractor
from src.data_manipulation.models.XBeamModel import XBeamModel
from src.data_manipulation.models.EBeamModel import EBeamModel
from src.data_manipulation.models.GeoModel import GeoModel


# ---------------------------------------------------------------------------
# CSV writing helpers
# ---------------------------------------------------------------------------

def write_results_csv(directory: str, rows: list[dict]) -> str:
    """Write a Results.csv with the standard headers and return its path."""
    path = os.path.join(directory, "Results.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Name [Unit]", " Value"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


# ===========================================================================
# data_extractor.extract() – dispatch logic
# ===========================================================================

class TestExtractDispatch:
    """extract() routes to the correct sub-method based on model class name."""

    def test_unsupported_model_raises_type_error(self):
        ex = data_extractor()

        class Unsupported:
            pass

        with pytest.raises(TypeError, match="Unsupported model type"):
            ex.extract(Unsupported())

    def test_extract_test_dispatch_raises_for_unsupported(self):
        ex = data_extractor()

        class Unknown:
            pass

        with pytest.raises(TypeError, match="Unsupported model type"):
            ex.extractTest(Unknown())


# ===========================================================================
# EBeamModel extraction
# ===========================================================================

class TestEModelExtraction:
    def setup_method(self):
        self.ex = data_extractor()
        self.tmp = tempfile.mkdtemp()

    def test_sets_relative_output(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "BeamOutputChange [%]", " Value": "1.23"},
        ])
        model = EBeamModel()
        model.set_path(self.tmp)
        self.ex.eModelExtraction(model)
        assert model.get_relative_output() == Decimal("1.23")

    def test_sets_relative_uniformity(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "BeamUniformityChange [%]", " Value": "2.34"},
        ])
        model = EBeamModel()
        model.set_path(self.tmp)
        self.ex.eModelExtraction(model)
        assert model.get_relative_uniformity() == Decimal("2.34")

    def test_sets_both_output_and_uniformity(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "BeamOutputChange [%]", " Value": "0.50"},
            {"Name [Unit]": "BeamUniformityChange [%]", " Value": "0.75"},
        ])
        model = EBeamModel()
        model.set_path(self.tmp)
        self.ex.eModelExtraction(model)
        assert model.get_relative_output() == Decimal("0.50")
        assert model.get_relative_uniformity() == Decimal("0.75")

    def test_invalid_value_defaults_to_negative_one(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "BeamOutputChange [%]", " Value": "NOT_A_NUMBER"},
        ])
        model = EBeamModel()
        model.set_path(self.tmp)
        self.ex.eModelExtraction(model)
        assert model.get_relative_output() == Decimal("-1")

    def test_empty_csv_leaves_defaults_unchanged(self):
        write_results_csv(self.tmp, [])
        model = EBeamModel()
        model.set_path(self.tmp)
        self.ex.eModelExtraction(model)
        assert model.get_relative_output() == Decimal("0.0")
        assert model.get_relative_uniformity() == Decimal("0.0")

    def test_missing_csv_does_not_raise(self):
        """A missing CSV is handled gracefully (logged, no exception raised)."""
        model = EBeamModel()
        model.set_path(self.tmp)  # no Results.csv written
        self.ex.eModelExtraction(model)  # should not raise

    def test_extract_dispatch_calls_emodel(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "BeamOutputChange [%]", " Value": "1.11"},
        ])
        model = EBeamModel()
        model.set_path(self.tmp)
        self.ex.extract(model)
        assert model.get_relative_output() == Decimal("1.11")

    def test_extract_test_dispatch_calls_emodel(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "BeamOutputChange [%]", " Value": "2.22"},
        ])
        model = EBeamModel()
        model.set_path(self.tmp)
        self.ex.extractTest(model)
        assert model.get_relative_output() == Decimal("2.22")

    def test_rows_with_empty_name_are_skipped(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "", " Value": "9.99"},
            {"Name [Unit]": "BeamOutputChange [%]", " Value": "0.11"},
        ])
        model = EBeamModel()
        model.set_path(self.tmp)
        self.ex.eModelExtraction(model)
        assert model.get_relative_output() == Decimal("0.11")


# ===========================================================================
# XBeamModel extraction
# ===========================================================================

class TestXModelExtraction:
    def setup_method(self):
        self.ex = data_extractor()
        self.tmp = tempfile.mkdtemp()

    def test_sets_relative_output(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "BeamOutputChange [%]", " Value": "0.99"},
        ])
        model = XBeamModel()
        model.set_path(self.tmp)
        self.ex.xModelExtraction(model)
        assert model.get_relative_output() == Decimal("0.99")

    def test_sets_relative_uniformity(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "BeamUniformityChange [%]", " Value": "1.05"},
        ])
        model = XBeamModel()
        model.set_path(self.tmp)
        self.ex.xModelExtraction(model)
        assert model.get_relative_uniformity() == Decimal("1.05")

    def test_sets_center_shift(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "BeamCenterShift [mm]", " Value": "0.40"},
        ])
        model = XBeamModel()
        model.set_path(self.tmp)
        self.ex.xModelExtraction(model)
        assert model.get_center_shift() == Decimal("0.40")

    def test_all_three_xbeam_fields(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "BeamOutputChange [%]", " Value": "1.00"},
            {"Name [Unit]": "BeamUniformityChange [%]", " Value": "2.00"},
            {"Name [Unit]": "BeamCenterShift [mm]", " Value": "0.10"},
        ])
        model = XBeamModel()
        model.set_path(self.tmp)
        self.ex.xModelExtraction(model)
        assert model.get_relative_output() == Decimal("1.00")
        assert model.get_relative_uniformity() == Decimal("2.00")
        assert model.get_center_shift() == Decimal("0.10")

    def test_invalid_value_falls_back_to_negative_one(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "BeamCenterShift [mm]", " Value": "BAD"},
        ])
        model = XBeamModel()
        model.set_path(self.tmp)
        self.ex.xModelExtraction(model)
        assert model.get_center_shift() == Decimal("-1")

    def test_extract_dispatch_calls_xmodel(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "BeamOutputChange [%]", " Value": "0.77"},
        ])
        model = XBeamModel()
        model.set_path(self.tmp)
        self.ex.extract(model)
        assert model.get_relative_output() == Decimal("0.77")

    def test_missing_csv_does_not_raise(self):
        model = XBeamModel()
        model.set_path(self.tmp)
        self.ex.xModelExtraction(model)  # should not raise


# ===========================================================================
# GeoModel extraction
# ===========================================================================

class TestGeoModelExtraction:
    def setup_method(self):
        self.ex = data_extractor()
        self.tmp = tempfile.mkdtemp()

    def test_sets_iso_center_size(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "IsoCenterSize [mm]", " Value": "0.5"},
        ])
        model = GeoModel()
        model.set_path(self.tmp)
        self.ex.geoModelExtraction(model)
        assert model.get_IsoCenterSize() == Decimal("0.5")

    def test_sets_iso_center_mv_offset(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "IsoCenterMVOffset [mm]", " Value": "0.2"},
        ])
        model = GeoModel()
        model.set_path(self.tmp)
        self.ex.geoModelExtraction(model)
        assert model.get_IsoCenterMVOffset() == Decimal("0.2")

    def test_sets_iso_center_kv_offset(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "IsoCenterKVOffset [mm]", " Value": "0.3"},
        ])
        model = GeoModel()
        model.set_path(self.tmp)
        self.ex.geoModelExtraction(model)
        assert model.get_IsoCenterKVOffset() == Decimal("0.3")

    def test_sets_gantry_absolute(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "GantryAbsolute [deg]", " Value": "0.8"},
        ])
        model = GeoModel()
        model.set_path(self.tmp)
        self.ex.geoModelExtraction(model)
        assert model.get_GantryAbsolute() == Decimal("0.8")

    def test_sets_gantry_relative(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "GantryRelative [deg]", " Value": "0.9"},
        ])
        model = GeoModel()
        model.set_path(self.tmp)
        self.ex.geoModelExtraction(model)
        assert model.get_GantryRelative() == Decimal("0.9")

    def test_sets_jaw_x1(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "JawX1 [mm]", " Value": "0.11"},
        ])
        model = GeoModel()
        model.set_path(self.tmp)
        self.ex.geoModelExtraction(model)
        assert model.get_JawX1() == Decimal("0.11")

    def test_sets_mlc_leaf_a_by_index(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "MLCLeavesA/MLCLeaf11 [mm]", " Value": "0.07"},
        ])
        model = GeoModel()
        model.set_path(self.tmp)
        self.ex.geoModelExtraction(model)
        assert model.get_MLCLeafA(11) == Decimal("0.07")

    def test_sets_mlc_leaf_b_by_index(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "MLCLeavesB/MLCLeaf23 [mm]", " Value": "0.09"},
        ])
        model = GeoModel()
        model.set_path(self.tmp)
        self.ex.geoModelExtraction(model)
        assert model.get_MLCLeafB(23) == Decimal("0.09")

    def test_sets_max_offset_a(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "MaxOffsetA [mm]", " Value": "0.55"},
        ])
        model = GeoModel()
        model.set_path(self.tmp)
        self.ex.geoModelExtraction(model)
        assert model.get_MaxOffsetA() == Decimal("0.55")

    def test_sets_mlc_backlash_a(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "MLCBacklashLeavesA/MLCBacklashLeaf5 [mm]", " Value": "0.04"},
        ])
        model = GeoModel()
        model.set_path(self.tmp)
        self.ex.geoModelExtraction(model)
        assert model.get_MLCBacklashA(5) == Decimal("0.04")

    def test_sets_mlc_backlash_max_a(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "MLCBacklashMaxA [mm]", " Value": "0.18"},
        ])
        model = GeoModel()
        model.set_path(self.tmp)
        self.ex.geoModelExtraction(model)
        assert model.get_MLCBacklashMaxA() == Decimal("0.18")

    def test_extract_dispatch_calls_geo_model(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "GantryAbsolute [deg]", " Value": "0.3"},
        ])
        model = GeoModel()
        model.set_path(self.tmp)
        self.ex.extract(model)
        assert model.get_GantryAbsolute() == Decimal("0.3")

    def test_missing_csv_does_not_raise(self):
        model = GeoModel()
        model.set_path(self.tmp)
        self.ex.geoModelExtraction(model)  # should not raise

    def test_mlc_leaf_index_out_of_range_is_skipped(self):
        """Leaf indices outside 1–60 should be silently skipped."""
        write_results_csv(self.tmp, [
            {"Name [Unit]": "MLCLeavesA/MLCLeaf99 [mm]", " Value": "5.00"},
        ])
        model = GeoModel()
        model.set_path(self.tmp)
        self.ex.geoModelExtraction(model)
        # Leaf 99 doesn't exist; all should remain at default 0.0
        for i in range(1, 61):
            assert model.get_MLCLeafA(i) == Decimal("0.0")

    def test_multiple_fields_in_one_csv(self):
        write_results_csv(self.tmp, [
            {"Name [Unit]": "IsoCenterSize [mm]",         " Value": "1.0"},
            {"Name [Unit]": "GantryAbsolute [deg]",       " Value": "2.0"},
            {"Name [Unit]": "JawY2 [mm]",                 " Value": "3.0"},
            {"Name [Unit]": "CouchLat [mm]",              " Value": "4.0"},
            {"Name [Unit]": "BeamOutputChange [%]",       " Value": "5.0"},
        ])
        model = GeoModel()
        model.set_path(self.tmp)
        self.ex.geoModelExtraction(model)
        assert model.get_IsoCenterSize() == Decimal("1.0")
        assert model.get_GantryAbsolute() == Decimal("2.0")
        assert model.get_JawY2() == Decimal("3.0")
        assert model.get_CouchLat() == Decimal("4.0")
        assert model.get_relative_output() == Decimal("5.0")
