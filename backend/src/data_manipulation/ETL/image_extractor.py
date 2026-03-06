"""
Image Extractor Module (EPID Gain Map Corrected Version)
---------------------------------------------------------
Implements proper EPID gain-map pipeline.

Offline-style gain map build (using provided flood(s))
Daily correction:
    - Dark subtract
    - Gain correction
    - 1D profile smoothing
    - FieldAnalysis
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

        clinical_raw = np.asarray(XIM(clinical_path), dtype=np.float64)
        dark = np.asarray(XIM(dark_path), dtype=np.float64)
        flood_raw = np.asarray(XIM(flood_path), dtype=np.float64)

        gain_map, bad_pixel_mask = self.build_gain_map(
            flood_raw,
            dark,
            kernel_size=75,
            clip_low=0.7,
            clip_high=1.3,
            field_fraction=0.8
        )

        corrected = self.correct_clinical_image(
            clinical_raw,
            dark,
            gain_map,
            bad_pixel_mask
        )

        img = ArrayImage(corrected.astype(np.float32), dpi=280)

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

        flood_net = flood_raw - dark

        beam_shape = median_filter(flood_net, size=kernel_size)

        beam_shape_safe = np.where(
            beam_shape > 0.01 * np.max(beam_shape),
            beam_shape,
            1.0
        )

        gain_map = flood_net / beam_shape_safe

        rows, cols = gain_map.shape
        margin = int((1 - field_fraction) / 2 * min(rows, cols))

        roi = gain_map[margin:rows - margin, margin:cols - margin]

        mean_val = np.mean(roi)

        if mean_val == 0 or np.isnan(mean_val):
            mean_val = 1.0

        gain_map /= mean_val

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

        c_net = clinical_raw - dark

        corrected = c_net / gain_map

        if np.any(bad_pixel_mask):
            local_med = generic_filter(corrected, np.nanmedian, size=5)
            corrected[bad_pixel_mask] = local_med[bad_pixel_mask]

        return corrected

    # ==========================================================
    # PROFILE SMOOTHING
    # ==========================================================
    def smooth_profile(self, profile, window=15, poly=3):

        profile = np.asarray(profile, dtype=float)

        n = len(profile)

        if n < 5:
            return profile

        window = min(window, n)

        if window % 2 == 0:
            window -= 1

        if window <= poly:
            window = poly + 2

        if window % 2 == 0:
            window += 1

        if window >= n:
            window = n - 1 if n % 2 == 0 else n

        if window <= poly or window < 3:
            return profile

        try:
            return savgol_filter(profile, window_length=window, polyorder=poly)
        except Exception:
            return profile

    # ==========================================================
    # PROFILE GRAPH GENERATION
    # ==========================================================
    def create_smoothed_profile_graphs(self, corrected, imageModel):

        corrected = np.asarray(corrected, dtype=float)

        rows, cols = corrected.shape

        center_row = rows // 2
        center_col = cols // 2

        crossline_raw = corrected[center_row, :]
        inline_raw = corrected[:, center_col]

        crossline = self.smooth_profile(crossline_raw)
        inline = self.smooth_profile(inline_raw)

        fig_h, ax_h = plt.subplots()

        ax_h.plot(crossline_raw, alpha=0.4, label="Raw")
        ax_h.plot(crossline, label="Smoothed")

        ax_h.set_title("Crossline Profile")
        ax_h.legend()
        ax_h.grid(True)

        imageModel.set_horizontal_profile_graph(fig_h)

        fig_v, ax_v = plt.subplots()

        ax_v.plot(inline_raw, alpha=0.4, label="Raw")
        ax_v.plot(inline, label="Smoothed")

        ax_v.set_title("Inline Profile")
        ax_v.legend()
        ax_v.grid(True)

        imageModel.set_vertical_profile_graph(fig_v)

        logger.info("Smoothed profiles generated")