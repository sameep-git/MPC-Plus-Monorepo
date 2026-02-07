"""
Image Extractor Module
----------------
This module defines the `image_extractor` class, responsible create an 
image object from the given image path.

Supported Image Types:
    - BeamProfileCheck.xim
"""

import logging

import numpy as np
import matplotlib.pyplot as plt

from pylinac.field_analysis import FieldAnalysis
from pylinac.core.image import XIM, ArrayImage

# Set up logger for this module
logger = logging.getLogger(__name__)

class image_extractor:
    def process_image(self,imageModel, is_test=False):
        # Load images (you may need to convert XIM to a format pylinac accepts)
        clinicalPath = imageModel.get_path()
        darkPath = imageModel.get_dark_image_path()
        floodPath = imageModel.get_flood_image_path()
        #Load images as numpy arrays
        clinical = np.array(XIM(clinicalPath))
        dark = np.array(XIM(darkPath))
        flood = np.array(XIM(floodPath))
        if is_test:
            logger.info("Clinical Path: %s", clinicalPath)
            logger.info("Dark Path: %s", darkPath)
            logger.info("Flood Path: %s", floodPath)
            self.show_all_images(clinical, dark, flood)
        
        # Apply corrections
        corrected_flood = flood - dark
        corrected_clinical = clinical - dark
        
        # Avoid division by zero
        threshold = 1e-6
        corrected_flood[corrected_flood < threshold] = threshold
        
        # Normalize
        #normalized = corrected_clinical / corrected_flood
        normalized = np.divide(
        corrected_clinical,
        corrected_flood,
        out=np.zeros_like(corrected_clinical, dtype=np.float32),
        where=corrected_flood > threshold
        )
        normalized = np.clip(normalized, 0, None)
        print("IM HERE 1")
        img = ArrayImage(normalized, dpi = 280)
        print("IM HERE 2")
        analysis = FieldAnalysis(img)
        print("IM HERE 3")
        #ERROR HERE FOR 6e BEAMS
        analysis.analyze()
        # analysis.analyze(
        #     invert=True,
        #     field_edge_method="inflection",
        #     edge_smoothing_ratio=0.1,
        #     profile_smoothing_ratio=0.1
        # )

        print("IM HERE 4")
        r = analysis.results_data()
        
        #Extract and store horizontal and vertical flatness graphs
        self.create_graphs(analysis, imageModel)

        imageModel.set_symmetry_horizontal(r.protocol_results['symmetry_horizontal'])
        imageModel.set_symmetry_vertical(r.protocol_results['symmetry_vertical'])
        imageModel.set_flatness_horizontal(r.protocol_results['flatness_horizontal'])
        imageModel.set_flatness_vertical(r.protocol_results['flatness_vertical'])
        if is_test:
            # Print numerical analysis results to the console
            logger.info(f"Flatness (Horizontal): {imageModel.get_flatness_horizontal()}")
            logger.info(f"Flatness (Vertical):   {imageModel.get_flatness_vertical()}")
            logger.info(f"Symmetry (Horizontal): {imageModel.get_symmetry_horizontal()}")
            logger.info(f"Symmetry (Vertical):   {imageModel.get_symmetry_vertical()}")
            # Display Flatness and Symmetry Profiles
            fig = imageModel.get_horizontal_profile_graph()
            fig.savefig("horizontal_profile.png") 
            fig = imageModel.get_vertical_profile_graph()
            fig.savefig("vertical_profile.png") 

    
    def create_graphs(self, analysis, imageModel):
        # Horizontal profile
        h = analysis.horiz_profile
        fig_h, ax_h = plt.subplots()  # Create Figure and Axes
        ax_h.plot(h.values)
        ax_h.set_title("Horizontal Profile")
        ax_h.set_xlabel("Pixel")
        ax_h.set_ylabel("Intensity")
        ax_h.grid(True)
        imageModel.set_horizontal_profile_graph(fig_h)  # store the Figure
        plt.close(fig_h)  # prevent automatic display

        # Vertical profile
        v = analysis.vert_profile
        fig_v, ax_v = plt.subplots()
        ax_v.plot(v.values)
        ax_v.set_title("Vertical Profile")
        ax_v.set_xlabel("Pixel")
        ax_v.set_ylabel("Intensity")
        ax_v.grid(True)
        imageModel.set_vertical_profile_graph(fig_v)
        plt.close(fig_v)
    
    def show_all_images(self, clinical, dark, flood):
        plt.figure(figsize=(9, 3))

        plt.subplot(1, 3, 1)
        plt.imshow(clinical, cmap='gray')
        plt.title("Clinical")
        plt.axis('off')

        plt.subplot(1, 3, 2)
        plt.imshow(dark, cmap='gray')
        plt.title("Dark")
        plt.axis('off')

        plt.subplot(1, 3, 3)
        plt.imshow(flood, cmap='gray')
        plt.title("Flood")
        plt.axis('off')

        plt.tight_layout()
        plt.show()
