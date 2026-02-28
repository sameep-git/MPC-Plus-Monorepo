"""
Image Extractor Module (EPID Gain Map Corrected Version)
---------------------------------------------------------
Implements proper EPID gain-map pipeline:

Offline-style gain map build (using provided flood(s))
Daily correction:
    - Dark subtract
    - Gain correction
    - 1D profile smoothing
    - FieldAnalysis

Follows MPC EPID Gain Map Pipeline specification.
"""

import logging
import numpy as np
import matplotlib.pyplot as plt

from scipy.ndimage import median_filter, generic_filter
from scipy.signal import savgol_filter

from pylinac.field_analysis import FieldAnalysis, Protocol
from pylinac.core.image import XIM, ArrayImage

logger = logging.getLogger(__name__)


class image_extractor:

    # ==========================================================
    # MAIN ENTRY
    # ==========================================================
    def process_image(self, imageModel, is_test=False):

        clinical_path = imageModel.get_path()
        dark_path = imageModel.get_dark_image_path()
        flood_path = imageModel.get_flood_image_path()

        # ------------------------------------------------------
        # Load images
        # ------------------------------------------------------
        clinical_raw = np.array(XIM(clinical_path), dtype=np.float64)
        dark = np.array(XIM(dark_path), dtype=np.float64)
        flood_raw = np.array(XIM(flood_path), dtype=np.float64)

        # ------------------------------------------------------
        # Build Gain Map (single-flood version)
        # ------------------------------------------------------
        gain_map, bad_pixel_mask = self.build_gain_map(
            flood_raw=flood_raw,
            dark=dark,
            kernel_size=75,
            clip_low=0.7,
            clip_high=1.3,
            field_fraction=0.8
        )

        # ------------------------------------------------------
        # Correct Clinical Image
        # ------------------------------------------------------
        corrected = self.correct_clinical_image(
            clinical_raw,
            dark,
            gain_map,
            bad_pixel_mask
        )

        # ------------------------------------------------------
        # Create ArrayImage for pylinac
        # ------------------------------------------------------
        img = ArrayImage(corrected.astype(np.float32), dpi=280)

        # ------------------------------------------------------
        # Run FieldAnalysis
        # ------------------------------------------------------
        analysis = FieldAnalysis(img)

        analysis.analyze(
            protocol=Protocol.VARIAN,
            in_field_ratio=0.8,
            edge_detection_method="FWHM"
        )

        r = analysis.results_data()

        imageModel.set_symmetry_horizontal(r.protocol_results['symmetry_horizontal'])
        imageModel.set_symmetry_vertical(r.protocol_results['symmetry_vertical'])
        imageModel.set_flatness_horizontal(r.protocol_results['flatness_horizontal'])
        imageModel.set_flatness_vertical(r.protocol_results['flatness_vertical'])

        # ------------------------------------------------------
        # Generate smoothed profile graphs
        # ------------------------------------------------------
        self.create_smoothed_profile_graphs(corrected, imageModel)

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

        # Step 1: Dark subtract flood
        flood_net = flood_raw - dark

        # Step 2: Beam shape estimate via large-kernel median filter
        beam_shape = median_filter(flood_net, size=kernel_size)

        # Avoid divide-by-zero
        beam_shape_safe = np.where(
            beam_shape > 0.01 * np.max(beam_shape),
            beam_shape,
            1.0
        )

        # Step 3: Isolate detector sensitivity
        gain_map = flood_net / beam_shape_safe

        # Step 4: Normalize over in-field ROI (80%)
        rows, cols = gain_map.shape
        margin = int((1 - field_fraction) / 2 * min(rows, cols))
        roi = gain_map[margin:rows - margin, margin:cols - margin]
        gain_map /= np.mean(roi)

        # Step 5: Flag + clip dead/hot pixels
        bad_pixel_mask = (gain_map < clip_low) | (gain_map > clip_high)
        gain_map = np.clip(gain_map, clip_low, clip_high)

        logger.info("Gain map built successfully")

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

        # Step 1: Dark subtract
        c_net = clinical_raw - dark

        # Step 2: Apply gain correction
        corrected = c_net / gain_map

        # Step 3: Replace bad pixels with local median
        if np.any(bad_pixel_mask):
            local_med = generic_filter(corrected, np.nanmedian, size=5)
            corrected[bad_pixel_mask] = local_med[bad_pixel_mask]

        return corrected

    # ==========================================================
    # PROFILE EXTRACTION + SMOOTHING
    # ==========================================================
    def smooth_profile(self, profile, window=15, poly=3):
        if window >= len(profile):
            window = len(profile) - 1
        if window % 2 == 0:
            window += 1
        return savgol_filter(profile, window, poly)

    def create_smoothed_profile_graphs(self, corrected, imageModel):

        rows, cols = corrected.shape
        center_row = rows // 2
        center_col = cols // 2

        crossline_raw = corrected[center_row, :]
        inline_raw = corrected[:, center_col]

        crossline = self.smooth_profile(crossline_raw)
        inline = self.smooth_profile(inline_raw)

        # Horizontal
        fig_h, ax_h = plt.subplots()
        ax_h.plot(crossline_raw, alpha=0.4, label="Raw")
        ax_h.plot(crossline, label="Smoothed")
        ax_h.set_title("Crossline Profile")
        ax_h.legend()
        ax_h.grid(True)
        imageModel.set_horizontal_profile_graph(fig_h)

        # Vertical
        fig_v, ax_v = plt.subplots()
        ax_v.plot(inline_raw, alpha=0.4, label="Raw")
        ax_v.plot(inline, label="Smoothed")
        ax_v.set_title("Inline Profile")
        ax_v.legend()
        ax_v.grid(True)
        imageModel.set_vertical_profile_graph(fig_v)

        logger.info("Smoothed profiles generated")