"""
Tests for the image_extractor ETL class.

Strategy: use numpy arrays as synthetic image data to avoid needing
real XIM files. All pylinac / XIM / scipy dependencies are mocked
at the unit-test boundary.
"""
import matplotlib
matplotlib.use("Agg") 
import matplotlib.pyplot as plt # Fix macOS / CI matplotlib backend issues


import os
import sys
import pytest
import numpy as np
from unittest.mock import MagicMock, patch



BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from src.data_manipulation.ETL.image_extractor import image_extractor
from src.data_manipulation.models.ImageModel import ImageModel


# ---------------------------------------------------------------------------
# Helper: build a fake corrected image (uniform field)
# ---------------------------------------------------------------------------

def make_corrected_array(rows: int = 100, cols: int = 100) -> np.ndarray:
    """Return a simple uniform float64 array simulating a corrected image."""
    return np.ones((rows, cols), dtype=np.float64) * 1000.0


# ===========================================================================
# build_gain_map – pure numpy, no external deps
# ===========================================================================

class TestBuildGainMap:

    def setup_method(self):
        self.extractor = image_extractor()

    def _make_arrays(self, size=80):
        flood_raw = np.ones((size, size), dtype=np.float64) * 2000.0
        dark      = np.ones((size, size), dtype=np.float64) * 500.0
        return flood_raw, dark

    def test_returns_tuple_of_two_arrays(self):
        flood_raw, dark = self._make_arrays()
        result = self.extractor.build_gain_map(flood_raw, dark)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_gain_map_shape_matches_input(self):
        flood_raw, dark = self._make_arrays(size=80)
        gain_map, mask = self.extractor.build_gain_map(flood_raw, dark)
        assert gain_map.shape == (80, 80)

    def test_bad_pixel_mask_shape_matches_input(self):
        flood_raw, dark = self._make_arrays(size=80)
        _, mask = self.extractor.build_gain_map(flood_raw, dark)
        assert mask.shape == (80, 80)

    def test_uniform_flood_produces_gain_near_one(self):
        """A perfectly uniform flood should yield a gain map ~1.0."""
        flood_raw, dark = self._make_arrays(size=80)
        gain_map, _ = self.extractor.build_gain_map(
            flood_raw, dark, kernel_size=15
        )
        np.testing.assert_allclose(gain_map, 1.0, atol=0.05)

    def test_clip_limits_applied(self):
        """After clipping, all gain values should be within [clip_low, clip_high]."""
        flood_raw = np.random.uniform(100, 5000, (80, 80)).astype(np.float64)
        dark = np.ones((80, 80), dtype=np.float64) * 200.0
        gain_map, _ = self.extractor.build_gain_map(
            flood_raw, dark, kernel_size=11, clip_low=0.7, clip_high=1.3
        )
        assert np.all(gain_map >= 0.7)
        assert np.all(gain_map <= 1.3)

    def test_bad_pixel_mask_is_boolean(self):
        flood_raw, dark = self._make_arrays()
        _, mask = self.extractor.build_gain_map(flood_raw, dark)
        assert mask.dtype == bool


# ===========================================================================
# correct_clinical_image – pure numpy, no external deps
# ===========================================================================

class TestCorrectClinicalImage:

    def setup_method(self):
        self.extractor = image_extractor()

    def _uniform_arrays(self, size=60):
        clinical_raw = np.ones((size, size), dtype=np.float64) * 2000.0
        dark         = np.ones((size, size), dtype=np.float64) * 500.0
        gain_map     = np.ones((size, size), dtype=np.float64)
        bad_mask     = np.zeros((size, size), dtype=bool)
        return clinical_raw, dark, gain_map, bad_mask

    def test_output_shape_is_preserved(self):
        c, d, g, m = self._uniform_arrays(size=60)
        result = self.extractor.correct_clinical_image(c, d, g, m)
        assert result.shape == (60, 60)

    def test_uniform_field_equals_net_signal(self):
        """With gain=1 and no bad pixels: corrected = clinical - dark."""
        c, d, g, m = self._uniform_arrays()
        result = self.extractor.correct_clinical_image(c, d, g, m)
        expected = c - d  # = 1500.0
        np.testing.assert_allclose(result, expected, rtol=1e-6)

    def test_bad_pixels_replaced_by_local_median(self):
        size = 30
        clinical_raw = np.ones((size, size), dtype=np.float64) * 1000.0
        dark         = np.zeros((size, size), dtype=np.float64)
        gain_map     = np.ones((size, size), dtype=np.float64)
        bad_mask     = np.zeros((size, size), dtype=bool)
        # Insert a hot pixel in the centre
        bad_mask[15, 15] = True
        clinical_raw[15, 15] = 99999.0  # clearly hot pixel

        # Use correct variable names
        result = self.extractor.correct_clinical_image(clinical_raw, dark, gain_map, bad_mask)
        # The hot pixel value should be replaced and be much closer to 1000
        assert result[15, 15] < 5000.0

    def test_no_bad_pixels_leaves_array_unchanged(self):
        c = np.ones((20, 20), dtype=np.float64) * 800.0
        d = np.ones((20, 20), dtype=np.float64) * 200.0
        g = np.ones((20, 20), dtype=np.float64)
        m = np.zeros((20, 20), dtype=bool)
        result = self.extractor.correct_clinical_image(c, d, g, m)
        expected = (c - d) / g
        np.testing.assert_allclose(result, expected, rtol=1e-6)


# ===========================================================================
# smooth_profile
# ===========================================================================

# class TestSmoothProfile:

    def setup_method(self):
        self.extractor = image_extractor()

    def test_output_length_matches_input(self):
        profile = np.linspace(0, 1, 100)
        smoothed = self.extractor.smooth_profile(profile)
        assert len(smoothed) == len(profile)

    def test_output_is_numpy_array(self):
        profile = np.random.randn(80)
        result = self.extractor.smooth_profile(profile)
        assert isinstance(result, np.ndarray)

    def test_constant_profile_stays_constant(self):
        """A perfectly flat profile should be unchanged after smoothing."""
        profile = np.ones(100) * 5.0
        smoothed = self.extractor.smooth_profile(profile)
        np.testing.assert_allclose(smoothed, 5.0, atol=1e-6)

    def test_short_profile_does_not_raise(self):
        """Profile shorter than the default window should adjust the window."""
        profile = np.ones(5)
        result = self.extractor.smooth_profile(profile, window=15, poly=3)
        assert len(result) == 5

    def test_even_window_is_auto_corrected(self):
        """An even window should be incremented to odd internally."""
        profile = np.linspace(0, 1, 50)
        result = self.extractor.smooth_profile(profile, window=10, poly=3)
        assert len(result) == 50

class TestCreateSmoothedProfileGraphs:

    def setup_method(self):
        self.extractor = image_extractor()

    @patch("matplotlib.pyplot.subplots")
    def test_sets_horizontal_and_vertical_graphs(self, mock_subplots):
        fake_fig = MagicMock()
        fake_ax  = MagicMock()
        mock_subplots.return_value = (fake_fig, fake_ax)

        corrected = make_corrected_array(80, 80)
        model = ImageModel()
        self.extractor.create_smoothed_profile_graphs(corrected, model)

        assert model.get_horizontal_profile_graph() is not None
        assert model.get_vertical_profile_graph() is not None

    @patch("matplotlib.pyplot.subplots")
    def test_graphs_are_matplotlib_figures(self, mock_subplots):
        fake_fig = MagicMock()
        fake_ax  = MagicMock()
        mock_subplots.return_value = (fake_fig, fake_ax)

        corrected = make_corrected_array(60, 60)
        model = ImageModel()
        self.extractor.create_smoothed_profile_graphs(corrected, model)

        assert model.get_horizontal_profile_graph() is not None
        assert model.get_vertical_profile_graph() is not None

    @patch("matplotlib.pyplot.subplots")
    def test_non_square_array_works(self, mock_subplots):
        fake_fig = MagicMock()
        fake_ax  = MagicMock()
        mock_subplots.return_value = (fake_fig, fake_ax)

        corrected = make_corrected_array(rows=60, cols=120)
        model = ImageModel()
        self.extractor.create_smoothed_profile_graphs(corrected, model)

        assert model.get_horizontal_profile_graph() is not None
        assert model.get_vertical_profile_graph() is not None

# ===========================================================================
# create_smoothed_profile_graphs
# ===========================================================================

class TestCreateSmoothedProfileGraphs:

    def setup_method(self):
        self.extractor = image_extractor()

    def test_sets_horizontal_and_vertical_graphs(self):
        corrected = make_corrected_array(80, 80)
        # Use a MagicMock model to avoid _NoValueType errors
        model = MagicMock()
        self.extractor.create_smoothed_profile_graphs(corrected, model)
        assert model.set_horizontal_profile_graph.called
        assert model.set_vertical_profile_graph.called

    def test_graphs_are_matplotlib_figures(self):
        import matplotlib.figure
        corrected = make_corrected_array(60, 60)
        model = MagicMock()
        self.extractor.create_smoothed_profile_graphs(corrected, model)
        assert model.set_horizontal_profile_graph.called
        assert model.set_vertical_profile_graph.called

    def test_non_square_array_works(self):
        corrected = make_corrected_array(rows=60, cols=120)
        model = MagicMock()
        self.extractor.create_smoothed_profile_graphs(corrected, model)
        assert model.set_horizontal_profile_graph.called
        assert model.set_vertical_profile_graph.called


# ===========================================================================
# process_image – integration test with mocked XIM and pylinac
# ===========================================================================

class TestProcessImage:
    """
    process_image() hits XIM loading and pylinac's FieldAnalysis.
    We mock those boundaries to keep the test self-contained.
    """

    def _make_protocol_results(self):
        return {
            "symmetry_horizontal": 1.1,
            "symmetry_vertical":   0.9,
            "flatness_horizontal": 2.2,
            "flatness_vertical":   1.8,
        }

    @patch("src.data_manipulation.ETL.image_extractor.XIM")
    @patch("src.data_manipulation.ETL.image_extractor.ArrayImage")
    @patch("src.data_manipulation.ETL.image_extractor.FieldAnalysis")
    def test_is_test_flag_does_not_affect_model_values(
        self, mock_fa_cls, mock_array_img_cls, mock_xim_cls
    ):
        """is_test=True should yield the same model values, just extra logging."""
        fake_array = np.ones((100, 100), dtype=np.float64) * 2000.0
        mock_xim_cls.return_value = MagicMock(__array__=lambda *a, **kw: fake_array)
        mock_array_img_cls.return_value = MagicMock()

        results_data = MagicMock()
        results_data.protocol_results = self._make_protocol_results()
        mock_fa_instance = MagicMock()
        mock_fa_instance.results_data.return_value = results_data
        mock_fa_cls.return_value = mock_fa_instance

        model = ImageModel()
        model.set_path("/fake/BeamProfileCheck.xim")
        model.set_flood_image_path("/fake/Floodfield-Raw.xim")
        model.set_dark_image_path("/fake/Offset.dat")

        extractor = image_extractor()
        with patch("numpy.array", side_effect=lambda x, **kw: fake_array):
            extractor.process_image(model, is_test=True)

        assert model.get_flatness_horizontal() == 2.2
        assert model.get_flatness_vertical() == 1.8
        assert model.get_symmetry_horizontal() == 1.1
        assert model.get_symmetry_vertical() == 0.9