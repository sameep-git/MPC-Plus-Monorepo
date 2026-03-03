"""
Tests for DataProcessor.

Most of DataProcessor relies on a live database connection and real XIM files,
so we focus on the pure-logic methods that are testable without external deps:
  - extract_beam_type()
  - _get_static_beam_map()
  - _get_dynamic_beam_map() (mocked DB response)
  - connect_to_db() (mocked Uploader)
  - EnhancedMLCCheckTemplate early-return guard in _process_beam()
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

# ---------------------------------------------------------------------------
# Patch heavy imports that are not needed for these unit tests
# ---------------------------------------------------------------------------
_PATCH_TARGETS = {
    "pylinac.core.image.XIM": MagicMock(),
    "pylinac.field_analysis.FieldAnalysis": MagicMock(),
    "pylinac.field_analysis.Protocol": MagicMock(),
}

# We import DataProcessor after inserting the mocked modules so that the
# module-level load_dotenv / psycopg2 calls don't fail in CI.
with patch.dict("sys.modules", _PATCH_TARGETS):
    from src.data_manipulation.ETL.DataProcessor import DataProcessor


# ---------------------------------------------------------------------------
# Fixture: a DataProcessor with a path that avoids real FS access
# ---------------------------------------------------------------------------
FAKE_PATH = r"C:\data\NDS-WKS-SN6543-2025-09-19-07-41-49-0008-BeamCheckTemplate10x"


@pytest.fixture
def dp():
    """Return a DataProcessor instance with all external connectors mocked."""
    with patch("src.data_manipulation.ETL.DataProcessor.Uploader") as mock_up_cls:
        mock_up_cls.return_value = MagicMock()
        with patch("src.data_manipulation.ETL.DataProcessor.data_extractor"):
            with patch("src.data_manipulation.ETL.DataProcessor.image_extractor"):
                processor = DataProcessor(FAKE_PATH)
    return processor


# ===========================================================================
# extract_beam_type
# ===========================================================================

class TestExtractBeamType:

    @pytest.fixture(autouse=True)
    def _make_dp(self):
        with patch("src.data_manipulation.ETL.DataProcessor.Uploader"):
            with patch("src.data_manipulation.ETL.DataProcessor.data_extractor"):
                with patch("src.data_manipulation.ETL.DataProcessor.image_extractor"):
                    self.dp = DataProcessor(FAKE_PATH)

    @pytest.mark.parametrize("path,expected", [
        (r"C:\NDS-WKS-SN1234-2025-01-01-00-00-00-BeamCheckTemplate10x\Results.csv", "10x"),
        (r"C:\NDS-WKS-SN1234-2025-01-01-00-00-00-BeamCheckTemplate6e\Results.csv", "6e"),
        (r"C:\NDS-WKS-SN1234-2025-01-01-00-00-00-BeamCheckTemplate9e\Results.csv", "9e"),
        (r"C:\NDS-WKS-SN1234-2025-01-01-00-00-00-BeamCheckTemplate12e\Results.csv", "12e"),
        (r"C:\NDS-WKS-SN1234-2025-01-01-00-00-00-BeamCheckTemplate16e\Results.csv", "16e"),
        (r"C:\NDS-WKS-SN1234-2025-01-01-00-00-00-BeamCheckTemplate15x\Results.csv", "15x"),
        (r"C:\NDS-WKS-SN1234-2025-01-01-00-00-00-BeamCheckTemplate2.5x\Results.csv", "2.5x"),
        (r"C:\NDS-WKS-SN1234-2025-01-01-00-00-00-BeamCheckTemplate6xFFF\Results.csv", "6xFFF"),
        (r"C:\NDS-WKS-SN1234-2025-01-01-00-00-00-GeometryCheckTemplate6xMVkVEnhancedCouch\Results.csv", "6xMVkVEnhancedCouch"),
    ])
    def test_known_beam_types(self, path, expected):
        result = self.dp.extract_beam_type(path)
        assert result == expected

    def test_returns_none_for_paths_without_template(self):
        result = self.dp.extract_beam_type(r"C:\some\random\path\Results.csv")
        assert result is None

    def test_returns_none_for_empty_string(self):
        assert self.dp.extract_beam_type("") is None

    def test_case_sensitive_match(self):
        # "template" in lowercase won't match the regex (capital T required)
        result = self.dp.extract_beam_type(r"C:\data\beamchecktemplate10x\Results.csv")
        assert result is None


# ===========================================================================
# _get_static_beam_map
# ===========================================================================

class TestGetStaticBeamMap:

    @pytest.fixture(autouse=True)
    def _make_dp(self):
        with patch("src.data_manipulation.ETL.DataProcessor.Uploader"):
            with patch("src.data_manipulation.ETL.DataProcessor.data_extractor"):
                with patch("src.data_manipulation.ETL.DataProcessor.image_extractor"):
                    self.dp = DataProcessor(FAKE_PATH)

    def test_returns_dict(self):
        result = self.dp._get_static_beam_map()
        assert isinstance(result, dict)

    def test_contains_expected_keys(self):
        result = self.dp._get_static_beam_map()
        assert "10x" in result
        assert "6e" in result
        assert "6xMVkVEnhancedCouch" in result
        assert "6xFFF" in result

    def test_10x_mapped_to_xbeam(self):
        from src.data_manipulation.models.XBeamModel import XBeamModel
        beam_map = self.dp._get_static_beam_map()
        model_class, beam_type, type_id = beam_map["10x"]
        assert model_class is XBeamModel
        assert beam_type == "10x"

    def test_6e_mapped_to_ebeam(self):
        from src.data_manipulation.models.EBeamModel import EBeamModel
        beam_map = self.dp._get_static_beam_map()
        model_class, beam_type, type_id = beam_map["6e"]
        assert model_class is EBeamModel
        assert beam_type == "6e"

    def test_6x_mv_kv_mapped_to_geo(self):
        from src.data_manipulation.models.GeoModel import GeoModel
        beam_map = self.dp._get_static_beam_map()
        model_class, beam_type, type_id = beam_map["6xMVkVEnhancedCouch"]
        assert model_class is GeoModel

    def test_type_ids_are_non_empty_strings(self):
        beam_map = self.dp._get_static_beam_map()
        for key, (model_class, beam_type, type_id) in beam_map.items():
            assert isinstance(type_id, str)
            assert len(type_id) > 0

    def test_all_known_variants_present(self):
        expected_keys = {"6xMVkVEnhancedCouch", "6xFFF", "6e", "9e", "12e", "15x", "16e", "2.5x", "10x"}
        beam_map = self.dp._get_static_beam_map()
        assert expected_keys.issubset(set(beam_map.keys()))


# ===========================================================================
# _get_dynamic_beam_map – with mocked DB variants
# ===========================================================================

class TestGetDynamicBeamMap:

    @pytest.fixture(autouse=True)
    def _make_dp(self):
        with patch("src.data_manipulation.ETL.DataProcessor.Uploader") as mock_up_cls:
            self.mock_up = MagicMock()
            mock_up_cls.return_value = self.mock_up
            with patch("src.data_manipulation.ETL.DataProcessor.data_extractor"):
                with patch("src.data_manipulation.ETL.DataProcessor.image_extractor"):
                    self.dp = DataProcessor(FAKE_PATH)
                    self.dp.up = self.mock_up

    def test_x_suffix_maps_to_xbeam(self):
        from src.data_manipulation.models.XBeamModel import XBeamModel
        self.mock_up.get_beam_variants.return_value = [
            {"variant": "10x", "id": "uuid-10x"},
        ]
        beam_map = self.dp._get_dynamic_beam_map()
        assert "10x" in beam_map
        assert beam_map["10x"][0] is XBeamModel

    def test_e_suffix_maps_to_ebeam(self):
        from src.data_manipulation.models.EBeamModel import EBeamModel
        self.mock_up.get_beam_variants.return_value = [
            {"variant": "6e", "id": "uuid-6e"},
        ]
        beam_map = self.dp._get_dynamic_beam_map()
        assert "6e" in beam_map
        assert beam_map["6e"][0] is EBeamModel

    def test_6x_mv_kv_special_case_maps_to_xbeam(self):
        from src.data_manipulation.models.XBeamModel import XBeamModel
        self.mock_up.get_beam_variants.return_value = [
            {"variant": "6xMVkVEnhancedCouch", "id": "uuid-geo"},
        ]
        beam_map = self.dp._get_dynamic_beam_map()
        assert "6xMVkVEnhancedCouch" in beam_map
        assert beam_map["6xMVkVEnhancedCouch"][0] is XBeamModel

    def test_6x_fff_special_case_maps_to_xbeam(self):
        from src.data_manipulation.models.XBeamModel import XBeamModel
        self.mock_up.get_beam_variants.return_value = [
            {"variant": "6xFFF", "id": "uuid-fff"},
        ]
        beam_map = self.dp._get_dynamic_beam_map()
        assert "6xFFF" in beam_map
        assert beam_map["6xFFF"][0] is XBeamModel

    def test_empty_variants_returns_none(self):
        self.mock_up.get_beam_variants.return_value = []
        result = self.dp._get_dynamic_beam_map()
        assert result is None

    def test_unknown_variant_format_is_skipped(self):
        self.mock_up.get_beam_variants.return_value = [
            {"variant": "unknown_beam", "id": "uuid-unknown"},
            {"variant": "10x", "id": "uuid-10x"},
        ]
        beam_map = self.dp._get_dynamic_beam_map()
        assert "unknown_beam" not in beam_map
        assert "10x" in beam_map


# ===========================================================================
# connect_to_db
# ===========================================================================

class TestConnectToDb:

    @pytest.fixture(autouse=True)
    def _make_dp(self):
        with patch("src.data_manipulation.ETL.DataProcessor.Uploader") as mock_up_cls:
            self.mock_up = MagicMock()
            mock_up_cls.return_value = self.mock_up
            with patch("src.data_manipulation.ETL.DataProcessor.data_extractor"):
                with patch("src.data_manipulation.ETL.DataProcessor.image_extractor"):
                    self.dp = DataProcessor(FAKE_PATH)
                    self.dp.up = self.mock_up

    def test_returns_uploader_on_successful_connect(self):
        self.mock_up.connect.return_value = True
        result = self.dp.connect_to_db()
        assert result is self.mock_up

    def test_returns_none_on_failed_connect(self):
        self.mock_up.connect.return_value = False
        result = self.dp.connect_to_db()
        assert result is None


# ===========================================================================
# _process_beam – EnhancedMLCCheckTemplate guard
# ===========================================================================

class TestProcessBeamGuards:

    @pytest.fixture(autouse=True)
    def _make_dp(self):
        with patch("src.data_manipulation.ETL.DataProcessor.Uploader") as mock_up_cls:
            self.mock_up = MagicMock()
            mock_up_cls.return_value = self.mock_up
            with patch("src.data_manipulation.ETL.DataProcessor.data_extractor"):
                with patch("src.data_manipulation.ETL.DataProcessor.image_extractor"):
                    enhanced_path = (
                        r"C:\data\NDS-WKS-SN6543-2025-09-19-07-41-49-"
                        r"0008-EnhancedMLCCheckTemplate6x"
                    )
                    self.dp = DataProcessor(enhanced_path)
                    self.dp.up = self.mock_up

    def test_enhanced_mlc_path_returns_early(self):
        """_process_beam should return without connecting to DB for this template."""
        self.dp._process_beam(is_test=False)
        # connect should NOT have been called
        self.mock_up.connect.assert_not_called()
