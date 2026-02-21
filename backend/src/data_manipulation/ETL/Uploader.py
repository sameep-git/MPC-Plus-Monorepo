"""
Uploader Module
----------------
This module defines the `Uploader` class, responsible for uploading beam data
from model objects to a database. It follows the Program-to-an-Interface principle,
allowing easy switching between different database management systems.

The module includes:
    - DatabaseAdapter: Abstract interface for database operations
    - PostgresAdapter: Concrete implementation for PostgreSQL (using psycopg2)
    - Uploader: Main class that uses model getters to upload data

Supported beam models:
    - Electron beams: `EBeamModel`
    - X-ray beams: `XBeamModel`
    - Geometric beams: `GeoModel`
"""

from abc import ABC, abstractmethod
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, Optional, List
import logging
import os
import json
import io
import numpy as np
from PIL import Image
import psycopg2
from psycopg2 import sql, extras

# Set up logger for this module
logger = logging.getLogger(__name__)


class DatabaseAdapter(ABC):
    """
    Abstract interface for database operations.
    Implementations should provide concrete methods for connecting and uploading data.
    """

    @abstractmethod
    def connect(self, connection_params: Dict[str, Any]) -> bool:
        """
        Establish connection to the database.
        
        Args:
            connection_params: Dictionary containing connection parameters
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def upload_beam_data(
        self, 
        table_name: str, 
        data: Dict[str, Any], 
        path: str = None
    ) -> Dict[str, Any]:
        """
        Upload beam data to the specified table.

        Returns:
            Dict[str, Any]: The inserted row, including primary key (e.g., 'id')
        """
        pass

    @abstractmethod
    def get_beam_variants(self) -> list:
        """
        Fetch the list of valid beam variants from the database.
        
        Returns:
            list: List of beam variant strings (e.g., ['6e', '10x'])
        """
        pass

    @abstractmethod
    def close(self):
        """Close the database connection."""
        pass


class PostgresAdapter(DatabaseAdapter):
    """
    Concrete implementation of DatabaseAdapter for PostgreSQL.
    Uses psycopg2 library.
    Handles image uploads by saving to local filesystem (for self-hosted setup).
    """

    def __init__(self):
        self.conn = None
        self.connected = False
        # Default local storage path matching the ASP.NET Core wwwroot/images structure
        # Assumes running from src/data_manipulation/ETL
        self.storage_root = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 
            "../../api/wwwroot/images"
        ))
        
        # Base URL for accessing images via the API (should match static file serving)
        self.base_url = "/images"

    def connect(self, connection_params: Dict[str, Any]) -> bool:
        """
        Establish connection to PostgreSQL.
        
        Args:
            connection_params: Dictionary with 'connection_string' or individual params
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            conn_str = connection_params.get('connection_string')
            if not conn_str:
                # Fallback to building from individual params
                host = connection_params.get('host', 'localhost')
                port = connection_params.get('port', 5432)
                dbname = connection_params.get('dbname', 'mpc_plus_db')
                user = connection_params.get('user', 'postgres')
                password = connection_params.get('password', os.environ.get('PGPASSWORD', ''))
                conn_str = f"host={host} port={port} dbname={dbname} user={user} password={password}"

            self.conn = psycopg2.connect(conn_str)
            self.connected = True
            logger.info("Successfully connected to PostgreSQL")
            return True
            
        except ImportError:
            logger.error("psycopg2 library not installed. Install with: pip install psycopg2-binary")
            return False
        except Exception as e:
            logger.error(f"Error connecting to PostgreSQL: {e}")
            self.connected = False
            return False

    def ensure_machine_exists(self, machine_id: str, path: str = None) -> bool:
        """
        Ensure a machine exists in the machines table.
        """
        if not self.connected or not self.conn:
            logger.error("Not connected to database")
            return False
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT id FROM machines WHERE id = %s", (machine_id,))
                if cur.fetchone():
                    return True
                
                # Create machine
                logger.info(f"Creating machine {machine_id}...")
                location = "Unknown"
                if path:
                    path_parts = path.split(os.sep)
                    for part in path_parts:
                        if part in ["Arlington", "Weatherford"]:
                            location = part
                            break
                            
                cur.execute(
                    "INSERT INTO machines (id, name, type, location) VALUES (%s, %s, %s, %s) RETURNING id",
                    (machine_id, f"Machine {machine_id}", 'NDS-WKS', location)
                )
                self.conn.commit()
                logger.info(f"Created machine {machine_id} in location {location}")
                return True
                
        except Exception as e:
            logger.error(f"Error ensuring machine exists: {e}", exc_info=True)
            self.conn.rollback()
            return False

    def upload_beam_data(self, table_name: str, data: Dict[str, Any], path: str = None) -> Dict[str, Any]:
        """
        Upload beam data to PostgreSQL table.
        """
        if not self.connected or not self.conn:
            logger.error("Not connected to database")
            return None
        
        try:
            # Ensure machine exists
            machine_id = data.get('machine_id')
            if machine_id:
                self.ensure_machine_exists(machine_id, path)
            
            # Serialize data (handle dates, JSON) and filter None keys if necessary
            # For SQL insert, we need strict column matching
            # Filter out keys that might not be in the table if they are strictly internal
            # But usually we pass correct keys.
            
            # Special handling for JSON fields (image_paths)
            # data has 'image_paths' as string json dump?
            
            columns = data.keys()
            values = [data[k] for k in columns]
            
            query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING *").format(
                sql.Identifier(table_name),
                sql.SQL(', ').join(map(sql.Identifier, columns)),
                sql.SQL(', ').join(sql.Placeholder() * len(columns))
            )
            
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, values)
                inserted = cur.fetchone()
                self.conn.commit()
                logger.info(f"Successfully uploaded data to {table_name}")
                return inserted

        except Exception as e:
            logger.error(f"Error uploading data to PostgreSQL: {e}", exc_info=True)
            self.conn.rollback()
            return None

    def get_beam_variants(self) -> list:
        if not self.connected or not self.conn:
            return []
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT id, variant FROM beam_variants")
                return cur.fetchall()
        except Exception as e:
            logger.error(f"Error fetching beam variants: {e}", exc_info=True)
            return []

    def upload_geocheck_data(self, data: Dict[str, Any], path: str = None) -> Optional[str]:
        # Reuse generic upload
        # Remove MLC detail lists that are not columns in geochecks
        data_clean = data.copy()
        keys_to_remove = ['mlc_leaves_a', 'mlc_leaves_b', 'mlc_backlash_a', 'mlc_backlash_b']
        for k in keys_to_remove:
            data_clean.pop(k, None)
            
        result = self.upload_beam_data('geochecks', data_clean, path)
        return result['id'] if result else None

    def upload_mlc_leaves(self, geocheck_id: str, leaves_data: list, bank: str) -> bool:
        if not self.connected or not self.conn or not geocheck_id or not leaves_data:
            return False
            
        table_name = f'geocheck_mlc_leaves_{bank.lower()}'
        
        try:
            records = []
            for leaf in leaves_data:
                records.append((
                    geocheck_id,
                    leaf.get('leaf_number'),
                    float(leaf.get('leaf_value')) if leaf.get('leaf_value') is not None else None
                ))
            
            with self.conn.cursor() as cur:
                extras.execute_values(
                    cur,
                    f"INSERT INTO {table_name} (geocheck_id, leaf_number, leaf_value) VALUES %s",
                    records
                )
                self.conn.commit()
                logger.info(f"Uploaded {len(records)} MLC leaves to {table_name}")
                return True
        except Exception as e:
            logger.error(f"Error uploading MLC leaves: {e}", exc_info=True)
            self.conn.rollback()
            return False

    def upload_mlc_backlash(self, geocheck_id: str, backlash_data: list, bank: str) -> bool:
        if not self.connected or not self.conn or not geocheck_id or not backlash_data:
            return False
            
        table_name = f'geocheck_mlc_backlash_{bank.lower()}'
        
        try:
            records = []
            for item in backlash_data:
                records.append((
                    geocheck_id,
                    item.get('leaf_number'),
                    float(item.get('backlash_value')) if item.get('backlash_value') is not None else None
                ))
            
            with self.conn.cursor() as cur:
                extras.execute_values(
                    cur,
                    f"INSERT INTO {table_name} (geocheck_id, leaf_number, backlash_value) VALUES %s",
                    records
                )
                self.conn.commit()
                logger.info(f"Uploaded {len(records)} MLC backlash to {table_name}")
                return True
        except Exception as e:
            logger.error(f"Error uploading MLC backlash: {e}", exc_info=True)
            self.conn.rollback()
            return False

    def _numpy_array_to_png_bytes(self, image_array: np.ndarray) -> Optional[bytes]:
        try:
            # Normalize array to 0-255 range if needed
            if image_array.dtype != np.uint8:
                if image_array.max() > 1.0:
                    image_array = image_array / image_array.max()
                image_array = (image_array * 255).astype(np.uint8)
            
            pil_image = Image.fromarray(image_array)
            img_bytes = io.BytesIO()
            pil_image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            return img_bytes.getvalue()
        except Exception as e:
            logger.error(f"Error converting numpy array to PNG: {e}")
            return None

    def _matplotlib_figure_to_png_bytes(self, fig) -> Optional[bytes]:
        try:
            img_bytes = io.BytesIO()
            fig.savefig(img_bytes, format='PNG', dpi=300, bbox_inches='tight')
            img_bytes.seek(0)
            return img_bytes.getvalue()
        except Exception as e:
            logger.error(f"Error converting matplotlib figure to PNG: {e}")
            return None

    def upload_beam_images(self, bucket_name: str, base_folder_path: str, 
                          beam_image: Optional[np.ndarray] = None,
                          horizontal_profile: Optional[Any] = None,
                          vertical_profile: Optional[Any] = None) -> Optional[Dict[str, str]]:
        
        # Determine local storage path
        # bucket_name is ignored essentially, mapped to 'images' folder
        # storage_path = storage_root / base_folder_path
        
        full_path = os.path.join(self.storage_root, base_folder_path)
        os.makedirs(full_path, exist_ok=True)
        
        image_urls = {}
        
        try:
            if beam_image is not None:
                b_bytes = self._numpy_array_to_png_bytes(beam_image)
                if b_bytes:
                    file_path = os.path.join(full_path, "beamImage.png")
                    with open(file_path, "wb") as f:
                        f.write(b_bytes)
                    image_urls["beamImage"] = f"{self.base_url}/{base_folder_path}/beamImage.png"
            
            if horizontal_profile is not None:
                b_bytes = self._matplotlib_figure_to_png_bytes(horizontal_profile)
                if b_bytes:
                    file_path = os.path.join(full_path, "horzProfile.png")
                    with open(file_path, "wb") as f:
                        f.write(b_bytes)
                    image_urls["horzProfile"] = f"{self.base_url}/{base_folder_path}/horzProfile.png"

            if vertical_profile is not None:
                b_bytes = self._matplotlib_figure_to_png_bytes(vertical_profile)
                if b_bytes:
                    file_path = os.path.join(full_path, "vertProfile.png")
                    with open(file_path, "wb") as f:
                        f.write(b_bytes)
                    image_urls["vertProfile"] = f"{self.base_url}/{base_folder_path}/vertProfile.png"
            
            if image_urls:
                logger.info(f"Saved {len(image_urls)} images to {full_path}")
                return image_urls
            else:
                return None
        except Exception as e:
            logger.error(f"Error saving images to disk: {e}", exc_info=True)
            return None

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.connected = False
            logger.info("PostgreSQL connection closed")


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
                    'date': date,
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
                    'date': date,
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
                        'date': date,
                        'value': center_shift
                    })

            # Add flatness and symmetry metrics if available
            # Note: getters are in AbstractBeamModel, so available for all beam types
            
            # vert_flatness
            flat_vert = model.get_flatness_vertical()
            if flat_vert is not None:
                metrics.append({
                    'machine_id': machine_id,
                    'check_type': check_type,
                    'beam_variant': beam_variant,
                    'typeID': typeID,
                    'metric_type': 'vert_flatness',
                    'date': date,
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
                    'date': date,
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
                    'date': date,
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
                    'date': date,
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
                        vertical_profile=vertical_profile
                    )
                
                # Prepare data dictionary using model getters, matching the beam table schema
                data = {
                    'typeID': eBeam.get_typeID(),
                    'type': eBeam.get_type(),
                    'date': eBeam.get_date(),
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
                    horizontal_profile = xBeam.get_horizontal_profile_graph() if hasattr(xBeam, 'get_horizontal_profile_graph') else None
                    vertical_profile = xBeam.get_vertical_profile_graph() if hasattr(xBeam, 'get_vertical_profile_graph') else None
                    
                    # Upload images
                    image_urls = self.db_adapter.upload_beam_images(
                        bucket_name="beam-images",
                        base_folder_path=base_folder_path,
                        beam_image=beam_image,
                        horizontal_profile=horizontal_profile,
                        vertical_profile=vertical_profile
                    )
                
                # Prepare data dictionary using model getters, matching the beam table schema
                data = {
                    'typeID': xBeam.get_typeID(),
                    'type': xBeam.get_type(),
                    'date': xBeam.get_date(),
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
                'date': geoModel.get_date(),
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
