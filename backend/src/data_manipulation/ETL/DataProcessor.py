import os
from pylinac.core.image import XIM
import logging
import re
from pathlib import Path
from dotenv import load_dotenv
import matplotlib.pyplot as plt
from src.data_manipulation.ETL.extractors.csv_data_extractor import csv_data_extractor
from src.data_manipulation.ETL.image.image_extractor import image_extractor
from src.data_manipulation.ETL.Uploader import Uploader
from src.data_manipulation.ETL.extractors.xml.xml_beam_extractor_entry import extract_beam_values

from src.data_manipulation.models.EBeamModel import EBeamModel
from src.data_manipulation.models.XBeamModel import XBeamModel
from src.data_manipulation.models.GeoModel import GeoModel
from src.data_manipulation.models.ImageModel import ImageModel


# Set up logger for this module
logger = logging.getLogger(__name__)


# Load environment variables from .env file in project root
# Search upwards from this file's directory for a .env file
def _find_project_root():
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / '.env').exists():
            return current
        current = current.parent
    # Fallback to 5-level parent if no .env found
    return Path(__file__).parent.parent.parent.parent.parent

project_root = _find_project_root()
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

        Automatically detects whether the results file is CSV or XML and sets
        self.data_format to 'csv' or 'xml' accordingly.
        """
        self.folder_path = path  # Store the folder path for uploads
        self.image_path = os.path.join(path, "BeamProfileCheck.xim")

        # --- Detect data format ---
        csv_path = os.path.join(path, "Results.csv")
        xml_path = os.path.join(path, "Results.xml")

        # CSV first because XML is a subset of CSV
        if os.path.exists(csv_path):
            self.data_format = "csv"
            self.data_path = csv_path
            logger.info("Data format detected: CSV (%s)", csv_path)
        elif os.path.exists(xml_path):
            self.data_format = "xml"
            self.data_path = xml_path
            logger.info("Data format detected: XML (%s)", xml_path)
        else:
            # Default to CSV path so downstream path helpers still work;
            # _process_beam will log an error if neither file exists.
            self.data_format = "unknown"
            self.data_path = csv_path
            logger.warning("Neither Results.csv nor Results.xml found in: %s", path)

        self.data_ex = csv_data_extractor()
        self.image_ex = image_extractor()

        # Database Uploader
        self.up = Uploader()

        # Timezone for converting local timestamps to UTC (fetched from DB)
        self._timezone = None

    # -------------------------------------------------------------------------
    # Generic helper method for beams
    # -------------------------------------------------------------------------

    def _init_beam_model(self, model_class, beam_type):
        """
        Generic initializer for any beam model.
        Sets path, type, date (UTC), and machine SN automatically.
        """
        model = model_class()
        model.set_path(self.folder_path)  # Use folder path instead of data_path for database
        model.set_type(beam_type)
        model.set_date(model._getDateFromPathName(self.data_path, tz_name=self._timezone))
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
        image.set_date(image._getDateFromPathName(self.image_path, tz_name=self._timezone))
        image.set_machine_SN(image._getSNFromPathName(self.image_path))
        image.set_image_name(image.generate_image_name())
        image.set_image(XIM(image.get_path()))
        # Attempt to find the flood image. Try user-specified "flood-field.xim" first, then fallback to "Floodfield-Raw.xim"
        flood_path = image.get_path().replace("BeamProfileCheck.xim", "flood-field.xim")
        if not os.path.exists(flood_path):
            flood_path = image.get_path().replace("BeamProfileCheck.xim", "Floodfield-Raw.xim")
        
        image.set_flood_image_path(flood_path)
        if os.path.exists(image.get_flood_image_path()):
            image.set_flood_image(XIM(image.get_flood_image_path()))
            
        # Retrieve recent floods for gain map construction
        past_floods = self._get_recent_floods(image, limit=5)

        image.set_dark_image_path(
            image.get_path().replace("BeamProfileCheck.xim", "Offset.dat")
            )
        #Process the image (Get flatness and symmetry from Pilinac FieldAnalysis)
        if is_test: logger.info("Processing test image in image_extractor.py")
        self.image_ex.process_image(image, past_floods, is_test)
        #self.image_ex.process_image(image.get_path(), image.get_dark_image_path(), image.get_flood_image_path(), is_test)
        image.convert_XIM_to_PNG()
        if is_test: 
            logger.info("Test image processed & returned from image_extractor.py")
            logger.info("Image Name: %s", image.get_image_name())

        return image

    def _get_recent_floods(self, image, limit: int = 5) -> list:
        """
        Retrieves the 'limit' most recent flood images for the machine/beam type.
        Returns a list of NumPy arrays.
        """
        past_floods = []
        try:
            # Current flood is the first in the "stack"
            if image.get_flood_image() is not None:
                past_floods.append(np.array(image.get_flood_image(), dtype=np.float64))
            
            # Query DB for up to (limit-1) more recent ones
            recent_paths = self.up.get_recent_flood_image_paths(
                image.get_machine_SN(), 
                image.get_type(), 
                image.get_date(), 
                limit=limit-1
            )
            
            # Paths come back as URLs like "/images/SN6543/20250919/12e/124149/floodImage.png"
            # We need to map them back to the local storage root
            storage_root = self.up.db_adapter.storage_root
            for rel_path in recent_paths:
                # rel_path = "/images/sub/path/to/image.png"
                # Strip leading "/images" and join with storage_root
                clean_rel = rel_path.replace("/images/", "").replace("/", os.sep)
                abs_path = os.path.join(storage_root, clean_rel)
                
                if os.path.exists(abs_path):
                    # These are already PNGs on disk (saved in previous uploads)
                    past_floods.append(np.array(plt.imread(abs_path), dtype=np.float64))
                    
            logger.info(f"Using {len(past_floods)} floods for gain map construction")
        except Exception as e:
            logger.error(f"Error retrieving past floods: {e}")
            
        return past_floods

    def _get_dynamic_beam_map(self, is_test=False):
        """
        Connects to PostgreSQL and determines the beam map dynamically 
        based on available variants.
        """
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
            if "6xMVkVEnhancedCouch" in variant:
                # Special case for 6x geometry check from path name mapped to 6xMVkVEnhancedCouch in database
                beam_map["6xMVkVEnhancedCouch"] = (GeoModel, "6x", typeID)
            elif "6xFFF" in variant:
                # Special case for 6xFFF check
                beam_map[variant] = (XBeamModel, "6xFFF", typeID)
            elif variant.endswith("x"):
                beam_map[variant] = (XBeamModel, variant, typeID)
            elif variant.endswith("e"):
                beam_map[variant] = (EBeamModel, variant, typeID)
            else:
                logger.warning(f"Unknown variant format from DB: {variant}. Skipping.")
        return beam_map

    def _get_static_beam_map(self, is_test=False):
        """
        Returns a static beam map for reingesting purposes.
        id,variant
        14ddae42-77a5-4e6a-8f27-6c2b98cb9780,10x
        1b1f54a1-d35f-4516-8c4b-0c19bada5d6c,16e
        253c1694-12d0-4497-9bd0-8487ee7c6f6f,6xMVkVEnhancedCouch
        439e3427-0e3d-4487-99fb-4d5e1c37ea34,12e
        7e997180-82f5-4922-b10a-d9ef9ecd22a9,15x
        a285aac2-1b63-4cd1-b7c5-76fcb4d95b84,9e
        b7afb3b6-8955-479f-a7b4-354b85ab9ff6,2.5x
        e6763342-a180-444a-a869-ce57d1b086b1,6e
        ffda6e9f-8f4d-48c3-8270-621d4a99db51,6xFFF
        """
        return {
            "6xMVkVEnhancedCouch": (GeoModel, "6x", "253c1694-12d0-4497-9bd0-8487ee7c6f6f"),
            "6xFFF": (XBeamModel, "6xFFF", "ffda6e9f-8f4d-48c3-8270-621d4a99db51"),
            "6e": (EBeamModel, "6e", "e6763342-a180-444a-a869-ce57d1b086b1"),
            "9e": (EBeamModel, "9e", "a285aac2-1b63-4cd1-b7c5-76fcb4d95b84"),
            "12e": (EBeamModel, "12e", "439e3427-0e3d-4487-99fb-4d5e1c37ea34"),
            "15x": (XBeamModel, "15x", "7e997180-82f5-4922-b10a-d9ef9ecd22a9"),
            "16e": (EBeamModel, "16e", "1b1f54a1-d35f-4516-8c4b-0c19bada5d6c"),
            "2.5x": (XBeamModel, "2.5x", "b7afb3b6-8955-479f-a7b4-354b85ab9ff6"),
            "10x": (XBeamModel, "10x", "14ddae42-77a5-4e6a-8f27-6c2b98cb9780"),
        }

    def extract_beam_type(self, path: str) -> str | None:
        """
        Extract the beam type from the path.
        """
        # Matches 6x, 6xFFF, 6xMVkVEnhancedCouch, 9x, 10x, etc.
        m = re.search(r'(?:Template|CheckTemplate)([A-Za-z0-9.]+)', path)
        if m:
            return m.group(1)
        return None
    
    def connect_to_db(self):
        # Connect to database using environment variables to fetch variants
        connection_params = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "database": os.getenv("POSTGRES_DATABASE"),
            "user": os.getenv("POSTGRES_USER"),
            "password": os.getenv("POSTGRES_PASSWORD"),
        }
        
        # Alternative: use connection_string if provided
        if os.getenv("POSTGRES_CONNECTION_STRING"):
            connection_params = {
                "connection_string": os.getenv("POSTGRES_CONNECTION_STRING")
            }
        
        # We need to connect to get static variants but connection is need for other parts of the program
        if not self.up.connect(connection_params):
            logger.error("Could not connect to PostgreSQL to fetch beam variants.")
            return None
        else:
            logger.info("Connected to PostgreSQL.")

        # Fetch timezone from app_settings — abort if not configured
        tz = self.up.get_app_timezone()
        if not tz:
            self.up.close()
            raise RuntimeError(
                "Timezone has not been configured. "
                "Please set the timezone in the MPC Plus Settings page before ingesting data."
            )
        self._timezone = tz
        logger.info(f"Using timezone: {self._timezone}")

        return self.up
    
    
    # -------------------------------------------------------------------------
    # Internal beam dispatcher
    # -------------------------------------------------------------------------
    def _process_beam(self, is_test=False):
        """
        Shared logic for both Run() and RunTest().
        Detects the beam type, initializes the model, and routes data
        extraction to the CSV or XML extractor based on self.data_format.
        """

        # Guard: unknown data format (neither Results.csv nor Results.xml present)
        if self.data_format == "unknown":
            logger.error("No Results.csv or Results.xml found in: %s", self.folder_path)
            return

        # Skip EnhancedMLCCheckTemplate6x - these have leaves we don't want to ingest
        if "EnhancedMLCCheckTemplate6x" in self.data_path:
            logger.info(f"Skipping EnhancedMLCCheckTemplate6x path (leaves not ingested): {self.data_path}")
            return

        self.connect_to_db()
        beam_map = self._get_dynamic_beam_map(is_test)
        #beam_map = self._get_static_beam_map(is_test)
        if not beam_map:
            return

        beam_token = self.extract_beam_type(self.data_path)

        for key, (model_class, beam_type, typeID) in beam_map.items():
            if beam_token == key:
                logger.info(f"{beam_type.upper()} Beam detected")
                if beam_type == "6x":
                    model_class = GeoModel
                # Initialize the correct beam model (EBeam, XBeam, etc.)
                beam = self._init_beam_model(model_class, beam_type)
                beam.set_typeID(typeID)
                logger.info(f"Setting Beam TypeID to: {typeID}")

                # --- Image Extraction for all beam types ---
                logger.info(f"Extracting image data for {beam_type} beam...")
                beam.set_image_model(self._init_beam_image(beam_type, is_test))
                beam.set_flat_and_sym_vals_from_image()

                # -----------------------------------------------------------------
                # Data Extraction — branch on detected file format
                # -----------------------------------------------------------------
                if self.data_format == "csv":
                    logger.info("Running CSV extraction...")
                    if is_test:
                        self.data_ex.extractTest(beam)
                    else:
                        self.data_ex.extract(beam)

                elif self.data_format == "xml":
                    logger.info("Running XML extraction...")
                    populated_beam = extract_beam_values(self.folder_path, beam)
                    if populated_beam is None:
                        logger.error("XML extractor returned no data for: %s", self.folder_path)
                        return

                    logger.info(
                        "XML extraction complete — output: %s, uniformity: %s",
                        round(beam.get_relative_output(), 4),
                        round(beam.get_relative_uniformity(), 4),
                    )
                    if beam_type == "6x":
                        logger.info(
                            "XML Geo Model — Gantry: %s, Couch: %s (Show Null)",
                            beam.get_GantryAbsolute(),
                            beam.get_RotationInducedCouchShiftFullRange(),
                        )

                # -----------------------------------------------------------------
                # Upload (skipped during test runs)
                # -----------------------------------------------------------------
                if not is_test:
                    logger.info("Uploading to PostgreSQL...")
                    if not self.up.upload(beam):
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

    