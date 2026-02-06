import os
from pylinac.core.image import XIM
import logging
import re
from pathlib import Path
from dotenv import load_dotenv
from src.data_manipulation.ETL.data_extractor import data_extractor
from src.data_manipulation.ETL.image_extractor import image_extractor
from src.data_manipulation.ETL.Uploader import Uploader

from src.data_manipulation.models.EBeamModel import EBeamModel
from src.data_manipulation.models.XBeamModel import XBeamModel
from src.data_manipulation.models.GeoModel import GeoModel
from src.data_manipulation.models.ImageModel import ImageModel

# Set up logger for this module
logger = logging.getLogger(__name__)


# Load environment variables from .env file in project root
project_root = Path(__file__).parent.parent.parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)


class DataProcessor:
    """
    Identifies the beam type from the input path,
    creates the appropriate model, and uses extractors
    to process data and images.
    """

    def __init__(self, path: str):
        """
        Initialize the DataProcessor with the directory path containing beam data.
        """
        self.folder_path = path  # Store the folder path for uploads
        self.data_path = os.path.join(path, "Results.csv")
        self.image_path = os.path.join(path, "BeamProfileCheck.xim")

        self.data_ex = data_extractor()
        self.image_ex = image_extractor()
        
        # Database Uploader
        self.up = Uploader()
        # If ran as test, coded so that no database connection is made

    # -------------------------------------------------------------------------
    # Generic helper method for beams
    # -------------------------------------------------------------------------

    def _init_beam_model(self, model_class, beam_type):
        """
        Generic initializer for any beam model.
        Sets path, type, date, and machine SN automatically.
        """
        model = model_class()
        model.set_path(self.folder_path)  # Use folder path instead of data_path for database
        model.set_type(beam_type)
        model.set_date(model._getDateFromPathName(self.data_path))
        model.set_machine_SN(model._getSNFromPathName(self.data_path))
        model.set_baseline(model._getIsBaselineFromPathName(self.data_path))
        return model
    
    # -------------------------------------------------------------------------
    # Generic helper method for images
    # -------------------------------------------------------------------------
    def _init_beam_image(self, beam_type, is_test=False):
        """
        Initialize an ImageModel for a given beam type and extract the image data.

        Args:
            beam_type (str): The type of the beam (e.g., "6e", "10x", "6x").
        """
        image = ImageModel()
        image.set_path(self.image_path) #Path to the BeamProfileCheck.xim file
        image.set_type(beam_type)
        image.set_date(image._getDateFromPathName(self.image_path))
        image.set_machine_SN(image._getSNFromPathName(self.image_path))
        image.set_image_name(image.generate_image_name())
        image.set_image(XIM(image.get_path()))
        #Image path has suffix "BeamProfileCheck.xim", remove and add "Flood" and "Dark" to get flood and dark image paths
        image.set_flood_image_path(
            image.get_path().replace("BeamProfileCheck.xim", "Floodfield-Raw.xim")
            )
        image.set_dark_image_path(
            image.get_path().replace("BeamProfileCheck.xim", "Offset.dat")
            )
        #Process the image (Get flatness and symmetry from Pilinac FieldAnalysis)
        if is_test: logger.info("Processing test image in image_extractor.py")
        self.image_ex.process_image(image, is_test)
        #self.image_ex.process_image(image.get_path(), image.get_dark_image_path(), image.get_flood_image_path(), is_test)
        image.convert_XIM_to_PNG()
        if is_test: 
            logger.info("Test image processed & returned from image_extractor.py")
            logger.info("Image Name: %s", image.get_image_name())

        return image

    def _get_dynamic_beam_map(self, is_test=False):
        """
        Connects to Supabase and determines the beam map dynamically 
        based on available variants.
        """
        # Connect to database using environment variables to fetch variants
        connection_params = {
            "url": os.getenv("SUPABASE_URL"),
            "key": os.getenv("SUPABASE_KEY"),
        }
        
        # We need to connect to get dynamic variants
        if not self.up.connect(connection_params):
            logger.error("Could not connect to Supabase to fetch beam variants.")
            return None

        variants = self.up.get_beam_variants()
        if not variants:
            logger.error("No beam variants returned from database. Cannot proceed.")
            self.up.close()
            return None

        beam_map = {}
        for item in variants:
            variant = item['variant']
            typeID = item['id']
            
            # Map database variant string to Model Class
            # Heuristic based on ending char
            if variant == "6xMVkVEnhancedCouch":
                # Special case for 6x geometry check
                beam_map[variant] = (GeoModel, "6xMVkVEnhancedCouch", typeID)
            elif variant == "6xFFF":
                # Special case for 6xFFF check
                beam_map[variant] = (XBeamModel, "6xFFF", typeID)
            elif variant.endswith("x"):
                beam_map[variant] = (XBeamModel, variant, typeID)
            elif variant.endswith("e"):
                beam_map[variant] = (EBeamModel, variant, typeID)
            else:
                logger.warning(f"Unknown variant format from DB: {variant}. Skipping.")
        
        return beam_map

    def extract_beam_type(self, path: str) -> str | None:
        """
        Extract the beam type from the path.
        """
        # Matches 6x, 6xFFF, 6xMVkVEnhancedCouch, 9x, 10x, etc.
        m = re.search(r'(?:Template|CheckTemplate)([A-Za-z0-9]+)', path)
        if m:
            return m.group(1)
        return None
    
    
    # -------------------------------------------------------------------------
    # Internal beam dispatcher
    # -------------------------------------------------------------------------
    def _process_beam(self, is_test=False):
        """
        Shared logic for both Run() and RunTest().
        Detects the beam type, initializes the model, 
        and sends it to the correct extractor method.
        """
        
        # Skip EnhancedMLCCheckTemplate6x - these have leaves we don't want to ingest
        if "EnhancedMLCCheckTemplate6x" in self.data_path:
            logger.info(f"Skipping EnhancedMLCCheckTemplate6x path (leaves not ingested): {self.data_path}")
            return

        beam_map = self._get_dynamic_beam_map(is_test)
        if not beam_map:
            return

        # for key, (model_class, beam_type) in beam_map.items():
        #     if key in self.data_path:
        #         # Special handling for 6x: use "6xFFF" only for BeamCheckTemplate6xFFF
        #         if key == "6x":
        #             if "BeamCheckTemplate6xFFF" in self.data_path:
        #                 beam_type = "6xFFF"
        #             # For other 6x templates (like GeometryCheckTemplate6xMVkVEnhancedCouch), use "6x"
        beam_token = self.extract_beam_type(self.data_path)
        for key, (model_class, beam_type, typeID) in beam_map.items():
            if beam_token == key:
                #return model_class(beam_type=beam_type)
                logger.info(f"{beam_type.upper()} Beam detected")

                # Initialize the correct beam model (EBeam, XBeam, etc.)
                beam = self._init_beam_model(model_class, beam_type)
                beam.set_typeID(typeID)
                logger.info(f"Setting Beam TypeID to: {typeID}")

                # --- Image Extraction for all beam types ---
                logger.info(f"Extracting image data for {beam_type} beam...")
                beam.set_image_model(self._init_beam_image(beam_type, is_test))
                
                ##Unsure of the cleanliness of this soln
                #Problem: Beams need to hold flatness and sym of images
                #Sol1: Data processor will tell beam to get  its vals from image
                # ^ implemented soln
                # Alt Soln: Image holds a direct link to its beam (Doublely Linked) 
                # and updates its parent beam stats as they are calculated
                beam.set_flat_and_sym_vals_from_image()

                if(is_test):
                    logger.info("Running test extraction...")
                    self.data_ex.extractTest(beam)
                else:
                    logger.info("Running normal extraction...")
                    self.data_ex.extract(beam)
                    logger.info("Uploading to Supabase...")
                    # Connection is already established at start of function
                    if(not self.up.upload(beam)):
                        logger.error("Cannot upload to the database")
                        return
                    logger.info("Beam Uploading Complete")
                    self.up.close()
                return

        # --- No beam type matched ---
        logger.error(f"Unknown or unsupported beam type for path: {self.data_path}")
        logger.error("Ensure the folder name includes one of the supported identifiers:")
        logger.error("→ 6e, 9e, 12e, 16e, 10x, 15x, or 6x (6xfff)")


    # -------------------------------------------------------------------------
    # Public entrypoints
    # -------------------------------------------------------------------------
    def Run(self):
        """Run the normal data processing workflow."""
        self._process_beam(is_test=False)

    def RunTest(self):
        """ Run the test data processing workflow.
            For Testing Print logger.info to console
        """
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self._process_beam(is_test=True)

    