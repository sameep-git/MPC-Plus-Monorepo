"""
Image Extractor Module (EPID Gain Map Corrected Version)
---------------------------------------------------------
This module implements a proper EPID gain-map pipeline. It follows
an offline-style workflow for building gain maps from a flood image,
then applies daily corrections to clinical images.

Key steps:
1. Build gain map from flood image and dark frame.
2. Correct clinical image using gain map and dark subtraction.
3. Smooth 1D profiles for analysis and plotting.
4. Use pylinac FieldAnalysis for flatness and symmetry metrics.

Notes:
- Headless matplotlib backend should be used in CI/testing to avoid
  '_NoValueType' errors, e.g., matplotlib.use("Agg") before any pyplot import.
- Numpy arrays are used for calculations to avoid file dependencies.
"""

import logging
import numpy as np
import matplotlib.pyplot as plt  # Backend must be set BEFORE this import in CI/testing

# SciPy filters for smoothing and local median for bad pixels
from scipy.ndimage import median_filter, generic_filter
from scipy.signal import savgol_filter

# pylinac for QA analysis
from pylinac.field_analysis import FieldAnalysis, Protocol
from pylinac.core.image import XIM, ArrayImage

logger = logging.getLogger(__name__)


class image_extractor:

    # ==========================================================
    # MAIN ENTRY
    # ==========================================================
    def process_image(self, imageModel, is_test=False):
        """
        Main processing pipeline for a single EPID image.

        Steps:
        1. Load clinical, dark, and flood images as float arrays.
        2. Build gain map and detect bad pixels.
        3. Correct the clinical image (dark subtract + gain correction + bad pixel replacement).
        4. Generate pylinac FieldAnalysis results.
        5. Optionally, create smoothed profile graphs (only if not in test mode).
        """

        # Retrieve file paths from the model
        clinical_path = imageModel.get_path()
        dark_path = imageModel.get_dark_image_path()
        flood_path = imageModel.get_flood_image_path()

        # Load images as float64 numpy arrays for precision
        clinical_raw = np.array(XIM(clinical_path), dtype=np.float64)
        dark = np.array(XIM(dark_path), dtype=np.float64)
        flood_raw = np.array(XIM(flood_path), dtype=np.float64)

        # Build gain map from flood + dark images
        gain_map, bad_pixel_mask = self.build_gain_map(
            flood_raw=flood_raw,
            dark=dark,
            kernel_size=75,
            clip_low=0.7,
            clip_high=1.3,
            field_fraction=0.8
        )

        # Apply gain correction to clinical image
        corrected = self.correct_clinical_image(
            clinical_raw,
            dark,
            gain_map,
            bad_pixel_mask
        )

        # Wrap corrected image for pylinac analysis
        img = ArrayImage(corrected.astype(np.float32), dpi=280)

        # Perform QA analysis using FieldAnalysis
        analysis = FieldAnalysis(img)
        analysis.analyze(
            protocol=Protocol.VARIAN,
            in_field_ratio=0.8,
            edge_detection_method="FWHM"
        )

        # Extract results
        r = analysis.results_data()
        imageModel.set_symmetry_horizontal(r.protocol_results['symmetry_horizontal'])
        imageModel.set_symmetry_vertical(r.protocol_results['symmetry_vertical'])
        imageModel.set_flatness_horizontal(r.protocol_results['flatness_horizontal'])
        imageModel.set_flatness_vertical(r.protocol_results['flatness_vertical'])

        # Generate smoothed profile graphs (skip in unit tests)
        if not is_test:
            self.create_smoothed_profile_graphs(corrected, imageModel)

        # For testing, log results instead of plotting
        if is_test:
            logger.info("Flatness H: %s", imageModel.get_flatness_horizontal())
            logger.info("Flatness V: %s", imageModel.get_flatness_vertical())
            logger.info("Symmetry H: %s", imageModel.get_symmetry_horizontal())
            logger.info("Symmetry V: %s", imageModel.get_symmetry_vertical())

    # ==========================================================
    # GAIN MAP BUILD
    # ==========================================================
    def build_gain_map(
        self,
        flood_raw,
        dark,
        kernel_size=75,
        clip_low=0.7,
        clip_high=1.3,
        field_fraction=0.8
    ):
        """
        Construct a gain map from a flood and dark image.

        Steps:
        1. Subtract dark from flood (flood_net).
        2. Smooth flood_net with median_filter to approximate beam profile.
        3. Avoid divide-by-zero using beam_shape_safe.
        4. Normalize over in-field region (ROI).
        5. Identify bad pixels (outside clipping range).
        """

        flood_net = flood_raw - dark  # Net signal

        # Smooth image to approximate beam shape
        beam_shape = median_filter(flood_net, size=kernel_size)

        # Avoid divide-by-zero for flat regions
        beam_shape_safe = np.where(
            beam_shape > 0.01 * np.max(beam_shape),
            beam_shape,
            1.0
        )

        # Raw gain map
        gain_map = flood_net / beam_shape_safe

        # Compute in-field ROI for normalization
        rows, cols = gain_map.shape
        margin = int((1 - field_fraction) / 2 * min(rows, cols))
        roi = gain_map[margin:rows - margin, margin:cols - margin]

        mean_val = np.mean(roi)
        if mean_val == 0 or np.isnan(mean_val):
            # Fallback to uniform map if invalid
            return np.ones_like(gain_map), np.zeros_like(gain_map, dtype=bool)

        gain_map /= mean_val  # Normalize

        # Detect bad pixels
        bad_pixel_mask = (gain_map < clip_low) | (gain_map > clip_high)

        # Clip gain map to allowed range
        gain_map = np.clip(gain_map, clip_low, clip_high)

        return gain_map, bad_pixel_mask

    # ==========================================================
    # CLINICAL CORRECTION
    # ==========================================================
    def correct_clinical_image(
        self,
        clinical_raw,
        dark,
        gain_map,
        bad_pixel_mask
    ):
        """
        Apply dark subtraction, gain correction, and bad-pixel replacement.

        - Dark subtraction: clinical_raw - dark
        - Gain correction: divide by gain_map
        - Bad pixels: replaced with local median (5x5 window)
        """

        c_net = clinical_raw - dark

        corrected = c_net / gain_map

        if np.any(bad_pixel_mask):
            # Replace bad pixels with local median to avoid spikes
            local_med = generic_filter(corrected, np.nanmedian, size=5)
            corrected[bad_pixel_mask] = local_med[bad_pixel_mask]

        return corrected

    # ==========================================================
    # PROFILE SMOOTHING
    # ==========================================================
    def smooth_profile(self, profile, window=15, poly=3):
        """
        Smooth a 1D profile using Savitzky-Golay filter.

        Adjusts window to handle:
        - Short profiles
        - Even windows (must be odd)
        - Window smaller than polynomial order
        """

        profile = np.asarray(profile, dtype=float)
        n = len(profile)

        if n < 3:
            return profile  # Too short to smooth

        window = min(window, n)

        # Make sure window is odd
        if window % 2 == 0:
            window -= 1

        # Window must be bigger than polynomial order
        if window <= poly:
            window = poly + 2
        if window % 2 == 0:
            window += 1

        if window > n:
            return profile  # Window too large, skip smoothing

        return savgol_filter(profile, window, poly)

    # ==========================================================
    # PROFILE GRAPHS
    # ==========================================================
    def create_smoothed_profile_graphs(self, corrected, imageModel):
        """
        Generate horizontal and vertical smoothed profile plots.

        Notes:
        - Always convert corrected to float
        - Use center row/col for crossline/inline
        - Raw vs. smoothed overlaid for QA visualization
        - Must avoid interactive backends in CI (set Agg before pyplot import)
        """

        corrected = np.asarray(corrected, dtype=float)

        rows, cols = corrected.shape
        center_row = rows // 2
        center_col = cols // 2

        crossline_raw = corrected[center_row, :]
        inline_raw = corrected[:, center_col]

        crossline = self.smooth_profile(crossline_raw)
        inline = self.smooth_profile(inline_raw)

        # Horizontal profile figure
        fig_h, ax_h = plt.subplots()
        ax_h.plot(crossline_raw, alpha=0.4, label="Raw")
        ax_h.plot(crossline, label="Smoothed")
        ax_h.set_title("Crossline Profile")
        ax_h.legend()
        ax_h.grid(True)
        imageModel.set_horizontal_profile_graph(fig_h)

        # Vertical profile figure
        fig_v, ax_v = plt.subplots()
        ax_v.plot(inline_raw, alpha=0.4, label="Raw")
        ax_v.plot(inline, label="Smoothed")
        ax_v.set_title("Inline Profile")
        ax_v.legend()
        ax_v.grid(True)
        imageModel.set_vertical_profile_graph(fig_v)

        logger.info("Smoothed profiles generated")