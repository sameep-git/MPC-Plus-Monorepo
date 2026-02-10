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

from pylinac.field_analysis import FieldAnalysis, Protocol
from pylinac.core.image import XIM, ArrayImage

# Set up logger for this module
logger = logging.getLogger(__name__)

class image_extractor:
    def process_image(self,imageModel, is_test=False):
        # Load images 
        clinicalPath = imageModel.get_path()
        darkPath = imageModel.get_dark_image_path()
        floodPath = imageModel.get_flood_image_path()
        #Load images as numpy arrays
        clinical = np.array(XIM(clinicalPath))
        dark = np.array(XIM(darkPath))
        flood = np.array(XIM(floodPath))
        self.show_all_images( clinical, dark, flood)
        if is_test:
            logger.info("Clinical Path: %s", clinicalPath)
            logger.info("Dark Path: %s", darkPath)
            logger.info("Flood Path: %s", floodPath)
            #self.show_all_images(clinical, dark, flood)
        
        # Apply corrections
        #corrected_flood = flood - dark
        corrected_flood = (flood - dark ) / dark
        #Replce / dark with middle average of clinical 
        #h, w = clinical.shape
        #center_pixel = clinical[h//2, w//2]  # Simple center (what you probably want)
        # h, w = clinical.shape
        # if h % 2 == 0 and w % 2 == 0:
        #     # Average of 4 center pixels
        #     center_pixel = np.mean(clinical[h//2-1:h//2+1, w//2-1:w//2+1])
        # else:
        #     center_pixel = clinical[h//2, w//2]
        # corrected_flood = (flood - dark ) / center_pixel
        corrected_clinical = clinical - dark
        
        # Avoid division by zero
        threshold = 1e-6
        corrected_flood[corrected_flood < threshold] = threshold
        #corrected_clinical[corrected_flood < threshold] = threshold
        
        # Normalize
        #normalized = corrected_clinical / corrected_flood
        normalized = np.divide(
        corrected_clinical,
        corrected_flood,
        out=np.zeros_like(corrected_clinical, dtype=np.float32),
        where=corrected_flood > threshold
        )

        # Create ArrayImage from normalized data
        img = ArrayImage(normalized, dpi=280)

        # Create FieldAnalysis with the image
        analysis = FieldAnalysis(img)

        # Define the sequence of analysis attempts
        attempts = [
            {"protocol": Protocol.VARIAN, "in_field_ratio": 0.8, "edge_detection_method": "FWHM"},
            {"protocol": Protocol.VARIAN, "in_field_ratio": 0.5, "edge_detection_method": "FWHM"},
            {}  # Generic call with no parameters
        ]

        analysis_successful = False

        for i, params in enumerate(attempts, start=1):
            try:
                logger.info(f"Attempt {i}: Running FieldAnalysis")
                analysis.analyze(**params)
                r = analysis.results_data()

                # Extract and store horizontal and vertical flatness graphs
                self.create_graphs(analysis, imageModel)

                # Set flatness and symmetry values from analysis results
                imageModel.set_symmetry_horizontal(r.protocol_results['symmetry_horizontal'])
                imageModel.set_symmetry_vertical(r.protocol_results['symmetry_vertical'])
                imageModel.set_flatness_horizontal(r.protocol_results['flatness_horizontal'])
                imageModel.set_flatness_vertical(r.protocol_results['flatness_vertical'])

                analysis_successful = True
                logger.info("FieldAnalysis completed successfully")
                if is_test:
                    logger.info(f"Flatness (Horizontal): {imageModel.get_flatness_horizontal()}")
                    logger.info(f"Flatness (Vertical):   {imageModel.get_flatness_vertical()}")
                    logger.info(f"Symmetry (Horizontal): {imageModel.get_symmetry_horizontal()}")
                    logger.info(f"Symmetry (Vertical):   {imageModel.get_symmetry_vertical()}")
                    # Display Flatness and Symmetry Profiles
                    fig = imageModel.get_horizontal_profile_graph()
                    fig.savefig("horizontal_profile.png") 
                    fig = imageModel.get_vertical_profile_graph()
                    fig.savefig("vertical_profile.png") 
                break

            except Exception as e:
                logger.error(f"Attempt {i} failed: {e}")
                if i < len(attempts):
                    logger.warning("Trying next analysis attempt...")
                else:
                    logger.error("All FieldAnalysis attempts failed, falling back to basic graph extraction")
                    try:
                        self.create_basic_graphs(img, imageModel)
                        imageModel.set_symmetry_horizontal(None)
                        imageModel.set_symmetry_vertical(None)
                        imageModel.set_flatness_horizontal(None)
                        imageModel.set_flatness_vertical(None)
                    except Exception as e2:
                        logger.error(f"Failed to create basic graphs: {e2}")
                        raise


    
    def create_graphs(self, analysis, imageModel):
        """
        Create profile graphs from pylinac FieldAnalysis results.
        
        Args:
            analysis: FieldAnalysis object that has been analyzed
            imageModel: ImageModel to store the graphs in
        """
        # Horizontal profile
        # Get horizontal profile data from pylinac FieldAnalysis
        # This is calculated from the normalized beam image
        h = analysis.horiz_profile
        fig_h, ax_h = plt.subplots()  # Create Figure and Axes
        ax_h.plot(h.values)  # Plot the intensity values across horizontal axis
        ax_h.set_title("Horizontal Profile")
        ax_h.set_xlabel("Pixel")
        ax_h.set_ylabel("Intensity")
        ax_h.grid(True)
        imageModel.set_horizontal_profile_graph(fig_h)  # store the Figure
        # Note: Not closing figure here - it needs to remain open for later PNG conversion
        # The figure will be garbage collected when no longer referenced

        # Vertical profile
        # Get vertical profile data from pylinac FieldAnalysis
        # This is calculated from the normalized beam image
        v = analysis.vert_profile
        fig_v, ax_v = plt.subplots()
        ax_v.plot(v.values)  # Plot the intensity values across vertical axis
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
        #plt.show()
        # Note: Not closing figure here - it needs to remain open for later PNG conversion
        # The figure will be garbage collected when no longer referenced

    def create_basic_graphs(self, image, imageModel):
        """
        Create basic profile graphs directly from image data when FieldAnalysis fails.
        This is a fallback method that extracts profiles from the center of the image.
        
        Args:
            image: ArrayImage object
            imageModel: ImageModel to store the graphs in
        """
        # Get image array
        img_array = image.array
        
        # Get center row (horizontal profile) and center column (vertical profile)
        center_row = img_array.shape[0] // 2
        center_col = img_array.shape[1] // 2
        
        # Horizontal profile (across columns at center row)
        horiz_values = img_array[center_row, :]
        fig_h, ax_h = plt.subplots()
        ax_h.plot(horiz_values)
        ax_h.set_title("Horizontal Profile (Center Row)")
        ax_h.set_xlabel("Pixel")
        ax_h.set_ylabel("Intensity")
        ax_h.grid(True)
        imageModel.set_horizontal_profile_graph(fig_h)
        
        # Vertical profile (across rows at center column)
        vert_values = img_array[:, center_col]
        fig_v, ax_v = plt.subplots()
        ax_v.plot(vert_values)
        ax_v.set_title("Vertical Profile (Center Column)")
        ax_v.set_xlabel("Pixel")
        ax_v.set_ylabel("Intensity")
        ax_v.grid(True)
        imageModel.set_vertical_profile_graph(fig_v)
        
        logger.info("Created basic profile graphs from image center (FieldAnalysis failed)")

        plt.tight_layout()
        #plt.show()
