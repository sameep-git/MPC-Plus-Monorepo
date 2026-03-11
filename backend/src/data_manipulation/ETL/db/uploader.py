"""
Uploader Module
----------------
Main class that uses model getters to upload data via a DatabaseAdapter.

Supported beam models:
    - Electron beams: `EBeamModel`
    - X-ray beams: `XBeamModel`
    - Geometric beams: `GeoModel`
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, Optional, List
import logging
import json

from src.data_manipulation.ETL.db.adapter import DatabaseAdapter
from src.data_manipulation.ETL.db.postgres_adapter import PostgresAdapter

# Set up logger for this module
logger = logging.getLogger(__name__)


class Uploader:
    """
    Handles data upload from model objects to a database.
    Each method corresponds to a specific model type and uses model getters
    to retrieve data for upload.
    """

    def __init__(self, db_adapter: Optional[DatabaseAdapter] = None):
        """
        Initialize the Uploader with a database adapter.
        
        Args:
            db_adapter: Database adapter instance. If None, defaults to PostgresAdapter
        """
        if db_adapter is None:
            self.db_adapter = PostgresAdapter()
        else:
            self.db_adapter = db_adapter
        
        self.connected = False

    def connect(self, connection_params: Dict[str, Any]) -> bool:
        """
        Connect to the database using the adapter.
        
        Args:
            connection_params: Dictionary containing connection parameters
        """
        self.connected = self.db_adapter.connect(connection_params)
        return self.connected

    def close(self):
        """
        Close the database connection using the adapter.
        """
        if self.db_adapter:
            self.db_adapter.close()
        self.connected = False

    def get_app_timezone(self) -> Optional[str]:
        """
        Retrieve the configured timezone from app_settings via the adapter.
        """
        if hasattr(self.db_adapter, 'get_app_timezone'):
            return self.db_adapter.get_app_timezone()
        return None

    def upload(self, model):
        """
        Automatically calls the correct upload method
        based on the type of model object passed in.

        Supported models:
            - EBeamModel
            - XBeamModel
            - GeoModel
        """
        if not self.connected:
            logger.error("Not connected to database. Call connect() first.")
            return False

        model_type = type(model).__name__.lower()
        logger.info(f"Uploading {model_type} data...")
        if "ebeam" in model_type:
            return self.eModelUpload(model)
        elif "xbeam" in model_type:
            return self.xModelUpload(model)
        elif "geo" in model_type:
            return self.geoModelUpload(model)
        else:
            raise TypeError(f"Unsupported model type: {type(model).__name__}")

    def get_beam_variants(self) -> list:
        """
        Fetch the list of valid beam variants using the adapter.
        """
        if not self.connected:
            logger.error("Not connected to database. Call connect() first.")
            return []
            
        return self.db_adapter.get_beam_variants()

    def get_recent_flood_image_paths(self, machine_id, beam_type, before_timestamp, limit=5):
        """
        Fetch the list of valid beam variants using the adapter.
        """
        if not self.connected:
            logger.error("Not connected to database. Call connect() first.")
            return []
            
        return self.db_adapter.get_recent_flood_image_paths(machine_id, beam_type, before_timestamp, limit)

    def _upload_baseline_metrics(self, model, check_type: str):
        """
        Upload baseline data as individual metric records to the baseline table.
        Creates one record per metric (rel_uniformity, rel_output, center_shift if applicable).
        
        Args:
            model: The beam model (EBeam, XBeam, or GeoModel)
            check_type: "beam" for EBeam/XBeam, "geometry" for GeoModel
        
        Returns:
            bool: True if all metrics uploaded successfully, False otherwise
        """
        try:
            machine_id = model.get_machine_SN()
            beam_variant = model.get_type()  # e.g., "6e", "15x", "6x"
            typeID = model.get_typeID()
            date = model.get_date()
            
            # List of metrics to upload
            metrics = []
            
            # Add rel_uniformity
            rel_uniformity = model.get_relative_uniformity()
            if rel_uniformity is not None:
                metrics.append({
                    'machine_id': machine_id,
                    'check_type': check_type,
                    'beam_variant': beam_variant,
                    'typeID': typeID,
                    'metric_type': 'rel_uniformity',
                    'timestamp': date,
                    'value': rel_uniformity
                })
            
            # Add rel_output
            rel_output = model.get_relative_output()
            if rel_output is not None:
                metrics.append({
                    'machine_id': machine_id,
                    'check_type': check_type,
                    'beam_variant': beam_variant,
                    'typeID': typeID,
                    'metric_type': 'rel_output',
                    'timestamp': date,
                    'value': rel_output
                })
            
            # Add center_shift (only for XBeam and GeoModel, not EBeam)
            if hasattr(model, 'get_center_shift'):
                center_shift = model.get_center_shift()
                if center_shift is not None:
                    metrics.append({
                        'machine_id': machine_id,
                        'check_type': check_type,
                        'beam_variant': beam_variant,
                        'typeID': typeID,
                        'metric_type': 'center_shift',
                        'timestamp': date,
                        'value': center_shift
                    })

            # Add flatness and symmetry metrics if available
            
            # vert_flatness
            flat_vert = model.get_flatness_vertical()
            if flat_vert is not None:
                metrics.append({
                    'machine_id': machine_id,
                    'check_type': check_type,
                    'beam_variant': beam_variant,
                    'typeID': typeID,
                    'metric_type': 'vert_flatness',
                    'timestamp': date,
                    'value': flat_vert
                })

            # hori_flatness
            flat_hori = model.get_flatness_horizontal()
            if flat_hori is not None:
                metrics.append({
                    'machine_id': machine_id,
                    'check_type': check_type,
                    'beam_variant': beam_variant,
                    'typeID': typeID,
                    'metric_type': 'hori_flatness',
                    'timestamp': date,
                    'value': flat_hori
                })

            # vert_symmetry
            sym_vert = model.get_symmetry_vertical()
            if sym_vert is not None:
                metrics.append({
                    'machine_id': machine_id,
                    'check_type': check_type,
                    'beam_variant': beam_variant,
                    'typeID': typeID,
                    'metric_type': 'vert_symmetry',
                    'timestamp': date,
                    'value': sym_vert
                })

            # hori_symmetry
            sym_hori = model.get_symmetry_horizontal()
            if sym_hori is not None:
                metrics.append({
                    'machine_id': machine_id,
                    'check_type': check_type,
                    'beam_variant': beam_variant,
                    'typeID': typeID,
                    'metric_type': 'hori_symmetry',
                    'timestamp': date,
                    'value': sym_hori
                })
            
            # Upload each metric record
            success_count = 0
            for metric_data in metrics:
                if self.db_adapter.upload_beam_data('baselines', metric_data):
                    success_count += 1
                else:
                    logger.error(f"Failed to upload baseline metric: {metric_data['metric_type']}")
            
            logger.info(f"Uploaded {success_count}/{len(metrics)} baseline metric records")
            return success_count == len(metrics) and len(metrics) > 0
            
        except Exception as e:
            logger.error(f"Error uploading baseline metrics: {e}")
            return False

    def uploadTest(self, model):
        """
        Automatically calls the correct upload method
        based on the type of model object passed in, with test output.

        Supported models:
            - EBeamModel
            - XBeamModel
            - GeoModel
    
        For Testing Print logger.info to console
        """
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        if not self.connected:
            logger.error("Not connected to database. Call connect() first.")
            return False

        model_type = type(model).__name__.lower()

        if "ebeam" in model_type:
            return self.eModelUpload(model)
        elif "xbeam" in model_type:
            return self.xModelUpload(model)
        elif "geo" in model_type:
            return self.geoModelUpload(model)
        else:
            raise TypeError(f"Unsupported model type: {type(model).__name__}")

    def _generate_image_folder_path(self, model) -> str:
        """
        Generate the base folder path for storing images.
        Format: machine_id/date/beam_type/time
        
        Args:
            model: Beam model with get_machine_SN(), get_type(), get_date() methods
        
        Returns:
            str: Folder path for images (e.g., "SN6543/20250919/10x/074149")
        """
        machine_id = model.get_machine_SN()
        beam_type = model.get_type()
        date_obj = model.get_date()
        
        date_str = date_obj.strftime("%Y%m%d")    # YYYYMMDD
        time_str = date_obj.strftime("%H%M%S")    # HHMMSS
        
        return f"{machine_id}/{date_str}/{beam_type}/{time_str}"

    # --- E-BEAM ---
    def eModelUpload(self, eBeam):
        """
        Upload data for E-beam model to the single beam table or baseline table.
        """
        try:
            # Check if this is a baseline
            if eBeam.get_baseline():
                # Upload to baseline table as individual metric records
                return self._upload_baseline_metrics(eBeam, check_type='beam')
            else:
                # Upload images
                image_urls = None
                image_model = eBeam.get_image_model()
                if image_model:
                    base_folder_path = self._generate_image_folder_path(eBeam)
                    
                    # Get images from the model
                    beam_image = image_model.get_image() if hasattr(image_model, 'get_image') else None
                    flood_image = image_model.get_flood_image() if hasattr(image_model, 'get_flood_image') else None
                    
                    horizontal_profile = None
                    if hasattr(eBeam, 'get_horizontal_profile_graph'):
                         horizontal_profile = eBeam.get_horizontal_profile_graph()
                         
                    vertical_profile = None
                    if hasattr(eBeam, 'get_vertical_profile_graph'):
                         vertical_profile = eBeam.get_vertical_profile_graph()
                    
                    # Upload images
                    image_urls = self.db_adapter.upload_beam_images(
                        bucket_name="beam-images", # Ignored by PostgresAdapter
                        base_folder_path=base_folder_path,
                        beam_image=beam_image,
                        horizontal_profile=horizontal_profile,
                        vertical_profile=vertical_profile,
                        flood_image=flood_image
                    )
                
                # Prepare data dictionary using model getters, matching the beam table schema
                data = {
                    'typeID': eBeam.get_typeID(),
                    'type': eBeam.get_type(),
                    'timestamp': eBeam.get_date(),
                    'date': eBeam.get_date().date(),
                    'path': eBeam.get_path(),
                    'rel_uniformity': eBeam.get_relative_uniformity(),
                    'rel_output': eBeam.get_relative_output(),
                    'center_shift': None,  # E-beams don't have center_shift
                    'vert_flatness': eBeam.get_flatness_vertical(),
                    'hori_flatness': eBeam.get_flatness_horizontal(),
                    'vert_symmetry': eBeam.get_symmetry_vertical(),
                    'hori_symmetry': eBeam.get_symmetry_horizontal(),
                    'machine_id': eBeam.get_machine_SN(),
                    'note': None,  # Add note if available in the model
                    'image_paths': json.dumps(image_urls) if image_urls else None  # Store public URLs as JSONB
                }
                result = self.db_adapter.upload_beam_data('beams', data)
                return result is not None

        except Exception as e:
            logger.error(f"Error during E-beam upload: {e}", exc_info=True)
            return False


    # --- X-BEAM ---
    def xModelUpload(self, xBeam):
        """
        Upload data for X-beam model to the single beam table or baseline table.
        """
        try:
            # Check if this is a baseline
            if xBeam.get_baseline():
                # Upload to baseline table as individual metric records
                return self._upload_baseline_metrics(xBeam, check_type='beam')
            else:
                # Upload images
                image_urls = None
                image_model = xBeam.get_image_model()
                if image_model:
                    base_folder_path = self._generate_image_folder_path(xBeam)
                    
                    # Get images from the model
                    beam_image = image_model.get_image() if hasattr(image_model, 'get_image') else None
                    flood_image = image_model.get_flood_image() if hasattr(image_model, 'get_flood_image') else None
                    horizontal_profile = xBeam.get_horizontal_profile_graph() if hasattr(xBeam, 'get_horizontal_profile_graph') else None
                    vertical_profile = xBeam.get_vertical_profile_graph() if hasattr(xBeam, 'get_vertical_profile_graph') else None
                    
                    # Upload images
                    image_urls = self.db_adapter.upload_beam_images(
                        bucket_name="beam-images",
                        base_folder_path=base_folder_path,
                        beam_image=beam_image,
                        horizontal_profile=horizontal_profile,
                        vertical_profile=vertical_profile,
                        flood_image=flood_image
                    )
                
                # Prepare data dictionary using model getters, matching the beam table schema
                data = {
                    'typeID': xBeam.get_typeID(),
                    'type': xBeam.get_type(),
                    'timestamp': xBeam.get_date(),
                    'date': xBeam.get_date().date(),
                    'path': xBeam.get_path(),
                    'rel_uniformity': xBeam.get_relative_uniformity(),
                    'rel_output': xBeam.get_relative_output(),
                    'center_shift': xBeam.get_center_shift(),
                    'vert_flatness': xBeam.get_flatness_vertical(),
                    'hori_flatness': xBeam.get_flatness_horizontal(),
                    'vert_symmetry': xBeam.get_symmetry_vertical(),
                    'hori_symmetry': xBeam.get_symmetry_horizontal(),
                    'machine_id': xBeam.get_machine_SN(),
                    'note': None,  # Add note if available in the model
                    'image_paths': json.dumps(image_urls) if image_urls else None  # Store public URLs as JSONB
                }
                result = self.db_adapter.upload_beam_data('beams', data)
                return result is not None

        except Exception as e:
            logger.error(f"Error during X-beam upload: {e}", exc_info=True)
            return False


    # --- GEO MODEL ---
    def geoModelUpload(self, geoModel):
        """
        Upload data for GeoModel to the geochecks table (with MLC detail rows)
        or the baseline table.
        """
        try:
            # Check if this is a baseline
            if geoModel.get_baseline():
                # Upload to baseline table as individual metric records
                return self._upload_baseline_metrics(geoModel, check_type='geometry')
            
            # ---- Build single geochecks row with ALL geometry fields ----
            geocheck_data = {
                'machine_id': geoModel.get_machine_SN(),
                'timestamp': geoModel.get_date(),
                'date': geoModel.get_date().date(),
                'path': geoModel.get_path(),
                'type': geoModel.get_type(),
                'note': None,
                # Beam metrics
                'relative_output': geoModel.get_relative_output(),
                'relative_uniformity': geoModel.get_relative_uniformity(),
                'center_shift': geoModel.get_center_shift(),
                # Isocenter
                'iso_center_size': geoModel.get_IsoCenterSize(),
                'iso_center_mv_offset': geoModel.get_IsoCenterMVOffset(),
                'iso_center_kv_offset': geoModel.get_IsoCenterKVOffset(),
                # Collimation
                'collimation_rotation_offset': geoModel.get_CollimationRotationOffset(),
                # Gantry
                'gantry_absolute': geoModel.get_GantryAbsolute(),
                'gantry_relative': geoModel.get_GantryRelative(),
                # Couch
                'couch_max_position_error': geoModel.get_CouchMaxPositionError(),
                'couch_lat': geoModel.get_CouchLat(),
                'couch_lng': geoModel.get_CouchLng(),
                'couch_vrt': geoModel.get_CouchVrt(),
                'couch_rtn_fine': geoModel.get_CouchRtnFine(),
                'couch_rtn_large': geoModel.get_CouchRtnLarge(),
                'rotation_induced_couch_shift_full_range': geoModel.get_RotationInducedCouchShiftFullRange(),
                # MLC offsets (summary values)
                'max_offset_a': geoModel.get_MaxOffsetA(),
                'max_offset_b': geoModel.get_MaxOffsetB(),
                'mean_offset_a': geoModel.get_MeanOffsetA(),
                'mean_offset_b': geoModel.get_MeanOffsetB(),
                # MLC backlash (summary values)
                'mlc_backlash_max_a': geoModel.get_MLCBacklashMaxA(),
                'mlc_backlash_max_b': geoModel.get_MLCBacklashMaxB(),
                'mlc_backlash_mean_a': geoModel.get_MLCBacklashMeanA(),
                'mlc_backlash_mean_b': geoModel.get_MLCBacklashMeanB(),
                # Jaws
                'jaw_x1': geoModel.get_JawX1(),
                'jaw_x2': geoModel.get_JawX2(),
                'jaw_y1': geoModel.get_JawY1(),
                'jaw_y2': geoModel.get_JawY2(),
                # Jaw parallelism
                'jaw_parallelism_x1': geoModel.get_JawParallelismX1(),
                'jaw_parallelism_x2': geoModel.get_JawParallelismX2(),
                'jaw_parallelism_y1': geoModel.get_JawParallelismY1(),
                'jaw_parallelism_y2': geoModel.get_JawParallelismY2(),
            }
            
            # Upload to geochecks table (returns geocheck_id)
            geocheck_id = self.db_adapter.upload_geocheck_data(geocheck_data, path=geoModel.get_path())
            
            if not geocheck_id:
                raise RuntimeError("Failed to get geocheck_id from upload_geocheck_data()")
            
            # ---- Upload MLC leaf detail rows to child tables ----
            leaves_a_list = [
                {'leaf_number': i, 'leaf_value': geoModel.get_MLCLeafA(i)}
                for i in range(11, 51)
            ]
            leaves_b_list = [
                {'leaf_number': i, 'leaf_value': geoModel.get_MLCLeafB(i)}
                for i in range(11, 51)
            ]
            # Use bank='a' / 'b'
            self.db_adapter.upload_mlc_leaves(geocheck_id, leaves_a_list, bank='a')
            self.db_adapter.upload_mlc_leaves(geocheck_id, leaves_b_list, bank='b')
            
            # ---- Upload MLC backlash detail rows to child tables ----
            backlash_a_list = [
                {'leaf_number': i, 'backlash_value': geoModel.get_MLCBacklashA(i)}
                for i in range(11, 51)
            ]
            backlash_b_list = [
                {'leaf_number': i, 'backlash_value': geoModel.get_MLCBacklashB(i)}
                for i in range(11, 51)
            ]
            self.db_adapter.upload_mlc_backlash(geocheck_id, backlash_a_list, bank='a')
            self.db_adapter.upload_mlc_backlash(geocheck_id, backlash_b_list, bank='b')
            
            # ---- Also upload beam-group metrics to the beams table ----
            # Upload images (same logic as xModelUpload / eModelUpload)
            image_urls = None
            image_model = geoModel.get_image_model()
            if image_model:
                base_folder_path = self._generate_image_folder_path(geoModel)
                beam_image = image_model.get_image() if hasattr(image_model, 'get_image') else None
                flood_image = image_model.get_flood_image() if hasattr(image_model, 'get_flood_image') else None
                horizontal_profile = geoModel.get_horizontal_profile_graph() if hasattr(geoModel, 'get_horizontal_profile_graph') else None
                vertical_profile = geoModel.get_vertical_profile_graph() if hasattr(geoModel, 'get_vertical_profile_graph') else None
                image_urls = self.db_adapter.upload_beam_images(
                    bucket_name="beam-images",
                    base_folder_path=base_folder_path,
                    beam_image=beam_image,
                    horizontal_profile=horizontal_profile,
                    vertical_profile=vertical_profile,
                    flood_image=flood_image
                )

            beam_data = {
                'typeID': geoModel.get_typeID(),
                'type': geoModel.get_type(),
                'timestamp': geoModel.get_date(),
                'date': geoModel.get_date().date(),
                'path': geoModel.get_path(),
                'rel_uniformity': geoModel.get_relative_uniformity(),
                'rel_output': geoModel.get_relative_output(),
                'center_shift': geoModel.get_center_shift(),
                'vert_flatness': geoModel.get_flatness_vertical(),
                'hori_flatness': geoModel.get_flatness_horizontal(),
                'vert_symmetry': geoModel.get_symmetry_vertical(),
                'hori_symmetry': geoModel.get_symmetry_horizontal(),
                'machine_id': geoModel.get_machine_SN(),
                'note': None,
                'image_paths': json.dumps(image_urls) if image_urls else None,
            }
            beam_result = self.db_adapter.upload_beam_data('beams', beam_data)
            if beam_result:
                logger.info(f"Also uploaded beam-group metrics to beams table for 6x geo check")
            else:
                logger.warning(f"Failed to upload beam-group metrics to beams table")
            
            logger.info(f"Successfully uploaded geometry check with geocheck_id: {geocheck_id}")
            return geocheck_id

        except Exception as e:
            logger.error(f"Error during Geo model upload: {e}", exc_info=True)
            return False

    def make_json_safe(self, obj):
        """
        Recursively convert Decimal objects to float for JSON serialization.
        """
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, list):
            return [self.make_json_safe(x) for x in obj]
        elif isinstance(obj, dict):
            return {k: self.make_json_safe(v) for k, v in obj.items()}
        else:
            return obj
