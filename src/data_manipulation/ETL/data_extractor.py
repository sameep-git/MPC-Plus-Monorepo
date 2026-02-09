"""
Data Extractor Module
----------------
This module defines the `data_extractor` class, responsible for reading and parsing
beam data from CSV files and populating model objects (EBeamModel, XBeamModel,
GeoModel) with corresponding numerical values.

Each extractor method is tailored to a specific beam type and calls the
appropriate model's setter methods based on CSV field names.

Supported beam models:
    - Electron beams: `EBeamModel`
    - X-ray beams: `XBeamModel`
    - Geometric beams: `GeoModel`
"""

import csv
import decimal
import logging
from decimal import Decimal

# Set up logger for this module
logger = logging.getLogger(__name__)

class data_extractor:
    """
    Handles data extraction from CSV files for various beam models.
    Each method corresponds to a specific model type and maps CSV entries
    to model attributes via setter methods.
    """

    def extract(self, model):
        """
        Automatically calls the correct extraction method
        based on the type of model object passed in.

        Supported models:
            - EBeamModel
            - XBeamModel
            - GeoModel
        """
        model_type = type(model).__name__.lower()

        if "ebeam" in model_type:
            return self.eModelExtraction(model)
        elif "xbeam" in model_type:
            return self.xModelExtraction(model)
        elif "geo" in model_type:
            return self.geoModelExtraction(model)
        else:
            raise TypeError(f"Unsupported model type: {type(model).__name__}")

    def extractTest(self, model):
        """
        Automatically calls the correct extraction method
        based on the type of model object passed in.

        Supported models:
            - EBeamModel
            - XBeamModel
            - GeoModel
        """
        model_type = type(model).__name__.lower()

        if "ebeam" in model_type:
            return self.testeModelExtraction(model)
        elif "xbeam" in model_type:
            return self.testxModelExtraction(model)
        elif "geo" in model_type:
            return self.testGeoModelExtraction(model)
        else:
            raise TypeError(f"Unsupported model type: {type(model).__name__}")
    # --- E-BEAM ---
    def eModelExtraction(self, eBeam):
        """
        Extract data for E-beam model from CSV file
        """
        import os
        
        try:
            # Get the folder path and construct the CSV file path
            folder_path = eBeam.get_path()
            path = os.path.join(folder_path, "Results.csv")
            
            # Parse the CSV file
            with open(path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Read through the CSV rows
                for row in reader:
                    name = row.get('Name [Unit]', '').strip()
                    value = row.get(' Value', '').strip()
                    if not name or not value:
                        continue
                    
                    # Convert value to Decimal
                    try:
                        dec_val = Decimal(value)
                    except (ValueError, TypeError, decimal.InvalidOperation):
                        dec_val = Decimal(-1)
                    
                    # Check for relative output (BeamOutputChange)
                    if 'BeamOutputChange' in name:
                        eBeam.set_relative_output(dec_val)
                    
                    # Check for relative uniformity (BeamUniformityChange)
                    elif 'BeamUniformityChange' in name:
                        eBeam.set_relative_uniformity(dec_val)
                
        except FileNotFoundError:
            logger.error(f"CSV file not found: {path}")
        except csv.Error as e:
            logger.error(f"Error parsing CSV file: {e}")
        except Exception as e:
            logger.error(f"Error during extraction: {e}", exc_info=True)

    def testeModelExtraction(self, eBeam):
        """
        Test method for E model extraction.
        Runs eModelExtraction() and prints all values using getters.
        """
        self.eModelExtraction(eBeam)


    # --- X-BEAM ---
    def xModelExtraction(self, xBeam):
        """
        Extract data for X-beam model from CSV file
        """
        import os
        
        try:
            # Get the folder path and construct the CSV file path
            folder_path = xBeam.get_path()
            path = os.path.join(folder_path, "Results.csv")
            
            # Parse the CSV file
            with open(path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Read through the CSV rows
                for row in reader:
                    name = row.get('Name [Unit]', '').strip()
                    value = row.get(' Value', '').strip()
                    if not name or not value:
                        continue
                    
                    # Convert value to Decimal
                    try:
                        dec_val = Decimal(value)
                    except (ValueError, TypeError, decimal.InvalidOperation):
                        dec_val = Decimal(-1)
                    
                    # Check for relative output (BeamOutputChange)
                    if 'BeamOutputChange' in name:
                        xBeam.set_relative_output(dec_val)
                    
                    # Check for relative uniformity (BeamUniformityChange)
                    elif 'BeamUniformityChange' in name:
                        xBeam.set_relative_uniformity(dec_val)

                    # Check for Center Shift (BeamCenterShift)
                    elif 'BeamCenterShift' in name:
                        xBeam.set_center_shift(dec_val)
                
        except FileNotFoundError:
            logger.error(f"CSV file not found: {path}")
        except csv.Error as e:
            logger.error(f"Error parsing CSV file: {e}")
        except Exception as e:
            logger.error(f"Error during extraction: {e}", exc_info=True)

    def testxModelExtraction(self, xBeam):
        """
        Test method for X model extraction.
        Runs xModelExtraction() and prints all values using getters.
        """
        self.xModelExtraction(xBeam)

    
    def geoModelExtraction(self, geoModel):
        """
        Extract data for GeoModel from CSV file.
        Reads each row and calls the appropriate setter.
        """
        import csv
        import os
        from decimal import Decimal, InvalidOperation

        try:
            # Get the folder path and construct the CSV file path
            folder_path = geoModel.get_path()
            path = os.path.join(folder_path, "Results.csv")

            with open(path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    name = row.get('Name [Unit]', '').strip()
                    value = row.get(' Value', '').strip()
                    if not name or not value:
                        continue
                    
                    # Convert value to Decimal
                    try:
                        dec_val = Decimal(value)
                    except (ValueError, TypeError, InvalidOperation):
                        dec_val = Decimal(-1)

                    # ---- IsoCenterGroup ----
                    if 'IsoCenterSize' in name:
                        geoModel.set_IsoCenterSize(dec_val)
                    elif 'IsoCenterMVOffset' in name:
                        geoModel.set_IsoCenterMVOffset(dec_val)
                    elif 'IsoCenterKVOffset' in name:
                        geoModel.set_IsoCenterKVOffset(dec_val)

                    # ---- BeamGroup ----
                    elif 'BeamOutputChange' in name:
                        geoModel.set_relative_output(dec_val)
                    elif 'BeamUniformityChange' in name:
                        geoModel.set_relative_uniformity(dec_val)
                    elif 'BeamCenterShift' in name:
                        geoModel.set_center_shift(dec_val)

                    # ---- CollimationGroup ----
                    elif 'CollimationRotationOffset' in name:
                        geoModel.set_CollimationRotationOffset(dec_val)

                    # ---- GantryGroup ----
                    elif 'GantryAbsolute' in name:
                        geoModel.set_GantryAbsolute(dec_val)
                    elif 'GantryRelative' in name:
                        geoModel.set_GantryRelative(dec_val)

                    # ---- EnhancedCouchGroup ----
                    elif 'CouchMaxPositionError' in name:
                        geoModel.set_CouchMaxPositionError(dec_val)
                    elif 'CouchLat' in name:
                        geoModel.set_CouchLat(dec_val)
                    elif 'CouchLng' in name:
                        geoModel.set_CouchLng(dec_val)
                    elif 'CouchVrt' in name:
                        geoModel.set_CouchVrt(dec_val)
                    elif 'CouchRtnFine' in name:
                        geoModel.set_CouchRtnFine(dec_val)
                    elif 'CouchRtnLarge' in name:
                        geoModel.set_CouchRtnLarge(dec_val)
                    elif 'RotationInducedCouchShiftFullRange' in name:
                        geoModel.set_RotationInducedCouchShiftFullRange(dec_val)

                    # ---- MLC Leaves ----
                    elif 'MLCLeavesA/MLCLeaf' in name or '/MLCLeavesA/MLCLeaf' in name:
                        try:
                            # Extract leaf number from patterns like:
                            # "CollimationGroup/MLCGroup/MLCLeavesA/MLCLeaf11 [mm]"
                            # or "MLCLeavesA/MLCLeaf11 [mm]"
                            parts = name.split('MLCLeaf')
                            if len(parts) > 1:
                                # Get the part after "MLCLeaf" and extract the number
                                leaf_part = parts[1].strip()
                                # Remove brackets and extract number: "11 [mm]" -> "11"
                                index_str = leaf_part.split()[0] if ' ' in leaf_part else leaf_part.split('[')[0]
                                index = int(index_str)
                                if 1 <= index <= 60:  # Validate leaf number range (1-60)
                                    geoModel.set_MLCLeafA(index, dec_val)
                        except (ValueError, IndexError, Exception) as e:
                            # Silently skip invalid entries
                            pass
                    elif 'MLCLeavesB/MLCLeaf' in name or '/MLCLeavesB/MLCLeaf' in name:
                        try:
                            # Extract leaf number from patterns like:
                            # "CollimationGroup/MLCGroup/MLCLeavesB/MLCLeaf11 [mm]"
                            # or "MLCLeavesB/MLCLeaf11 [mm]"
                            parts = name.split('MLCLeaf')
                            if len(parts) > 1:
                                # Get the part after "MLCLeaf" and extract the number
                                leaf_part = parts[1].strip()
                                # Remove brackets and extract number: "11 [mm]" -> "11"
                                index_str = leaf_part.split()[0] if ' ' in leaf_part else leaf_part.split('[')[0]
                                index = int(index_str)
                                if 1 <= index <= 60:  # Validate leaf number range (1-60)
                                    geoModel.set_MLCLeafB(index, dec_val)
                        except (ValueError, IndexError, Exception) as e:
                            # Silently skip invalid entries
                            pass

                    # ---- MLC Offsets ----
                    elif 'MLCMaxOffsetA' in name or 'MaxOffsetA' in name:
                        geoModel.set_MaxOffsetA(dec_val)
                    elif 'MLCMaxOffsetB' in name or 'MaxOffsetB' in name:
                        geoModel.set_MaxOffsetB(dec_val)
                    elif 'MLCMeanOffsetA' in name or 'MeanOffsetA' in name:
                        geoModel.set_MeanOffsetA(dec_val)
                    elif 'MLCMeanOffsetB' in name or 'MeanOffsetB' in name:
                        geoModel.set_MeanOffsetB(dec_val)

                    # ---- MLC Backlash ----
                    elif 'MLCBacklashLeavesA/MLCBacklashLeaf' in name or '/MLCBacklashLeavesA/MLCBacklashLeaf' in name:
                        try:
                            # Extract leaf number from patterns like:
                            # "CollimationGroup/MLCBacklashGroup/MLCBacklashLeavesA/MLCBacklashLeaf11 [mm]"
                            # or "MLCBacklashLeavesA/MLCBacklashLeaf11 [mm]"
                            parts = name.split('MLCBacklashLeaf')
                            if len(parts) > 1:
                                # Get the part after "MLCBacklashLeaf" and extract the number
                                leaf_part = parts[1].strip()
                                # Remove brackets and extract number: "11 [mm]" -> "11"
                                index_str = leaf_part.split()[0] if ' ' in leaf_part else leaf_part.split('[')[0]
                                index = int(index_str)
                                if 1 <= index <= 60:  # Validate leaf number range (1-60)
                                    geoModel.set_MLCBacklashA(index, dec_val)
                        except (ValueError, IndexError, Exception) as e:
                            # Silently skip invalid entries
                            pass
                    elif 'MLCBacklashLeavesB/MLCBacklashLeaf' in name or '/MLCBacklashLeavesB/MLCBacklashLeaf' in name:
                        try:
                            # Extract leaf number from patterns like:
                            # "CollimationGroup/MLCBacklashGroup/MLCBacklashLeavesB/MLCBacklashLeaf11 [mm]"
                            # or "MLCBacklashLeavesB/MLCBacklashLeaf11 [mm]"
                            parts = name.split('MLCBacklashLeaf')
                            if len(parts) > 1:
                                # Get the part after "MLCBacklashLeaf" and extract the number
                                leaf_part = parts[1].strip()
                                # Remove brackets and extract number: "11 [mm]" -> "11"
                                index_str = leaf_part.split()[0] if ' ' in leaf_part else leaf_part.split('[')[0]
                                index = int(index_str)
                                if 1 <= index <= 60:  # Validate leaf number range (1-60)
                                    geoModel.set_MLCBacklashB(index, dec_val)
                        except (ValueError, IndexError, Exception) as e:
                            # Silently skip invalid entries
                            pass
                    elif 'MLCBacklashMaxA' in name:
                        geoModel.set_MLCBacklashMaxA(dec_val)
                    elif 'MLCBacklashMaxB' in name:
                        geoModel.set_MLCBacklashMaxB(dec_val)
                    elif 'MLCBacklashMeanA' in name:
                        geoModel.set_MLCBacklashMeanA(dec_val)
                    elif 'MLCBacklashMeanB' in name:
                        geoModel.set_MLCBacklashMeanB(dec_val)

                    # ---- Jaws Group ----
                    elif 'JawX1' in name:
                        geoModel.set_JawX1(dec_val)
                    elif 'JawX2' in name:
                        geoModel.set_JawX2(dec_val)
                    elif 'JawY1' in name:
                        geoModel.set_JawY1(dec_val)
                    elif 'JawY2' in name:
                        geoModel.set_JawY2(dec_val)

                    # ---- Jaws Parallelism ----
                    elif 'JawParallelismX1' in name:
                        geoModel.set_JawParallelismX1(dec_val)
                    elif 'JawParallelismX2' in name:
                        geoModel.set_JawParallelismX2(dec_val)
                    elif 'JawParallelismY1' in name:
                        geoModel.set_JawParallelismY1(dec_val)
                    elif 'JawParallelismY2' in name:
                        geoModel.set_JawParallelismY2(dec_val)

        except FileNotFoundError:
            logger.error(f"CSV file not found: {path}")
        except csv.Error as e:
            logger.error(f"Error parsing CSV file: {e}")
        except Exception as e:
            logger.error(f"Error during extraction: {e}", exc_info=True)

    def testGeoModelExtraction(self, geoModel):
        """
        Test method for Geo model extraction.
        Runs geoModelExtraction() and prints all values using getters.
        """
        self.geoModelExtraction(geoModel)

