"""
Uploader Module
----------------
This module defines the `Uploader` class, responsible for uploading beam data
from model objects to a database. It follows the Program-to-an-Interface principle,
allowing easy switching between different database management systems.

The module includes:
    - DatabaseAdapter: Abstract interface for database operations
    - SupabaseAdapter: Concrete implementation for Supabase DBMS
    - Uploader: Main class that uses model getters to upload data

Supported beam models:
    - Electron beams: `EBeamModel`
    - X-ray beams: `XBeamModel`
    - Geometric beams: `GeoModel`
"""

from abc import ABC, abstractmethod
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, Optional
import logging
import os
import json
import io
import numpy as np
from PIL import Image

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
                              (e.g., url, key, etc.)
        
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


class SupabaseAdapter(DatabaseAdapter):
    """
    Concrete implementation of DatabaseAdapter for Supabase DBMS.
    Uses the supabase-py library to interact with Supabase.
    """

    def __init__(self):
        self.client = None
        self.connected = False

    def connect(self, connection_params: Dict[str, Any]) -> bool:
        """
        Establish connection to Supabase.
        
        Args:
            connection_params: Dictionary with 'url' and 'key' keys
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            from supabase import create_client, Client
            url = connection_params.get('url')
            key = connection_params.get('key')

            if not url or not key:
                logger.error("Supabase connection requires 'url' and 'key' parameters")
                return False
            
            self.client: Client = create_client(url, key)
            self._supabase_url = url.rstrip('/')  # Store URL for constructing public URLs
            self.connected = True
            logger.info("Successfully connected to Supabase")
            return True
            
        except ImportError:
            logger.error("supabase-py library not installed. Install with: pip install supabase")
            return False
        except Exception as e:
            logger.error(f"Error connecting to Supabase: {e}")
            self.connected = False
            return False

    def ensure_machine_exists(self, machine_id: str, path: str = None) -> bool:
        """
        Ensure a machine exists in the machines table before uploading beams.
        Creates the machine if it doesn't exist.
        
        Args:
            machine_id: The machine ID (serial number)
            path: Optional path to extract location from (e.g., "/Volumes/Lexar/MPC Data/Arlington/...")
        
        Returns:
            bool: True if machine exists or was created successfully, False otherwise
        """
        if not self.connected or not self.client:
            logger.error("Not connected to Supabase")
            return False
        
        try:
            # Check if machine exists
            response = self.client.table('machines').select('id').eq('id', machine_id).execute()
            
            if response.data and len(response.data) > 0:
                logger.debug(f"Machine {machine_id} already exists")
                return True
            
            # Machine doesn't exist, create it
            logger.info(f"Creating machine {machine_id}...")
            
            # Extract location from path if provided
            location = "Unknown"
            if path:
                # Try to extract location from path (e.g., "/Volumes/Lexar/MPC Data/Arlington/..." -> "Arlington")
                path_parts = path.split(os.sep)
                for part in path_parts:
                    if part in ["Arlington", "Weatherford"]:
                        location = part
                        break
            
            # Create machine with default values
            machine_data = {
                'id': machine_id,
                'name': f"Machine {machine_id}",
                'location': location,
                'type': 'NDS-WKS'  # Default type based on folder naming pattern
            }
            
            response = self.client.table('machines').insert(machine_data).execute()
            
            if response.data:
                logger.info(f"Created machine {machine_id} in location {location}")
                return True
            else:
                logger.warning(f"No data returned when creating machine {machine_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error ensuring machine exists: {e}", exc_info=True)
            return False

    def upload_beam_data(self, table_name: str, data: Dict[str, Any], path: str = None) -> bool:
        """
        Upload beam data to Supabase table.
        
        Args:
            table_name: Name of the Supabase table
            data: Dictionary containing the data to upload
            path: Optional path to extract location from for machine creation
        
        Returns:
            bool: True if upload successful, False otherwise
        """
        if not self.connected or not self.client:
            logger.error("Not connected to Supabase")
            return False
        
        try:
            # Ensure machine exists before uploading beam
            machine_id = data.get('machine_id')
            if machine_id:
                if not self.ensure_machine_exists(machine_id, path):
                    logger.warning(f"Could not ensure machine {machine_id} exists, but continuing with upload attempt")
            
            # Convert Decimal to float for JSON serialization
            serialized_data = self._serialize_data(data)
            logger.debug(f"Uploading data to {table_name}: {serialized_data}")
            
            # Insert data into Supabase table
            response = self.client.table(table_name).insert(serialized_data).execute()
            
            if response.data:
                logger.info(f"Successfully uploaded data to {table_name}")
                return response.data[0]
            else:
                logger.warning("No data returned from Supabase insert")
                return False
                
        except Exception as e:
            logger.error(f"Error uploading data to Supabase: {e}", exc_info=True)
            return False
            
    def get_beam_variants(self) -> list:
        """
        Fetch the list of valid beam variants from the beam_variants table.
        
        Returns:
            list: List of beam variant strings (e.g., ['6e', '10x'])
        """
        if not self.connected or not self.client:
            logger.error("Not connected to Supabase")
            return []
            
        try:
            response = self.client.table('beam_variants').select('id, variant').execute()
            
            if response.data:
                # Return the list of dictionaries directly (e.g., [{'id': '...', 'variant': '...'}])
                variants = response.data
                logger.info(f"Fetched {len(variants)} beam variants from database")
                return variants
            else:
                logger.warning("No beam variants found in database")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching beam variants: {e}", exc_info=True)
            return []

    def upload_geocheck_data(self, data: Dict[str, Any], path: str = None) -> Optional[str]:
        """
        Upload geometry check data to geochecks table.
        Note: MLC leaves and backlash should NOT be included here - they go to separate tables.
        
        Args:
            data: Dictionary containing the geocheck data to upload (geometry data only: jaws, couch, gantry, etc.)
            path: Optional path to extract location from for machine creation
        
        Returns:
            str: The geocheck_id if upload successful, None otherwise
        """
        if not self.connected or not self.client:
            logger.error("Not connected to Supabase")
            return None
        
        try:
            # Ensure machine exists before uploading geocheck
            machine_id = data.get('machine_id')
            if machine_id:
                if not self.ensure_machine_exists(machine_id, path):
                    logger.warning(f"Could not ensure machine {machine_id} exists, but continuing with upload attempt")
            
            # Remove MLC data if accidentally included (it goes to separate tables)
            data.pop('mlc_leaves_a', None)
            data.pop('mlc_leaves_b', None)
            data.pop('mlc_backlash_a', None)
            data.pop('mlc_backlash_b', None)
            
            # Convert Decimal to float for JSON serialization
            serialized_data = self._serialize_data(data)
            logger.debug(f"Uploading geocheck data: {serialized_data}")
            
            # Insert data into geochecks table
            response = self.client.table('geochecks').insert(serialized_data).execute()
            
            if response.data and len(response.data) > 0:
                geocheck_id = response.data[0].get('id')
                logger.info(f"Successfully uploaded geocheck data with id: {geocheck_id}")
                return geocheck_id
            else:
                logger.warning("No data returned from Supabase geocheck insert")
                return None
                
        except Exception as e:
            logger.error(f"Error uploading geocheck data to Supabase: {e}", exc_info=True)
            return None

    def upload_mlc_leaves(self, geocheck_id: str, leaves_data: list, bank: str) -> bool:
        """
        Upload MLC leaves data to geocheck_mlc_leaves_a or geocheck_mlc_leaves_b table.
        
        Args:
            geocheck_id: The geocheck ID to associate leaves with
            leaves_data: List of dictionaries with 'leaf_number' and 'leaf_value'
            bank: Either 'a' or 'b' to determine which table to use
        
        Returns:
            bool: True if all leaves uploaded successfully, False otherwise
        """
        if not self.connected or not self.client:
            logger.error("Not connected to Supabase")
            return False
        
        if not geocheck_id or not leaves_data:
            return False
        
        table_name = f'geocheck_mlc_leaves_{bank.lower()}'
        
        try:
            # Prepare data with geocheck_id
            upload_data = []
            for leaf in leaves_data:
                leaf_record = {
                    'geocheck_id': geocheck_id,
                    'leaf_number': leaf.get('leaf_number'),
                    'leaf_value': float(leaf.get('leaf_value')) if leaf.get('leaf_value') is not None else None
                }
                upload_data.append(leaf_record)
            
            # Insert all leaves at once
            response = self.client.table(table_name).insert(upload_data).execute()
            
            if response.data:
                logger.info(f"Successfully uploaded {len(upload_data)} MLC leaves to {table_name}")
                return True
            else:
                logger.warning(f"No data returned from {table_name} insert")
                return False
                
        except Exception as e:
            logger.error(f"Error uploading MLC leaves to {table_name}: {e}", exc_info=True)
            return False

    def upload_mlc_backlash(self, geocheck_id: str, backlash_data: list, bank: str) -> bool:
        """
        Upload MLC backlash data to geocheck_mlc_backlash_a or geocheck_mlc_backlash_b table.
        
        Args:
            geocheck_id: The geocheck ID to associate backlash with
            backlash_data: List of dictionaries with 'leaf_number' and 'backlash_value'
            bank: Either 'a' or 'b' to determine which table to use
        
        Returns:
            bool: True if all backlash data uploaded successfully, False otherwise
        """
        if not self.connected or not self.client:
            logger.error("Not connected to Supabase")
            return False
        
        if not geocheck_id or not backlash_data:
            return False
        
        table_name = f'geocheck_mlc_backlash_{bank.lower()}'
        
        try:
            # Prepare data with geocheck_id
            upload_data = []
            for backlash in backlash_data:
                backlash_record = {
                    'geocheck_id': geocheck_id,
                    'leaf_number': backlash.get('leaf_number'),
                    'backlash_value': float(backlash.get('backlash_value')) if backlash.get('backlash_value') is not None else None
                }
                upload_data.append(backlash_record)
            
            # Insert all backlash records at once
            response = self.client.table(table_name).insert(upload_data).execute()
            
            if response.data:
                logger.info(f"Successfully uploaded {len(upload_data)} MLC backlash records to {table_name}")
                return True
            else:
                logger.warning(f"No data returned from {table_name} insert")
                return False
                
        except Exception as e:
            logger.error(f"Error uploading MLC backlash to {table_name}: {e}", exc_info=True)
            return False

    def _serialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert data types to JSON-serializable formats.
        
        Args:
            data: Dictionary with potentially non-serializable values
        
        Returns:
            Dictionary with serialized values
        """
        serialized = {}
        for key, value in data.items():
            if isinstance(value, Decimal):
                serialized[key] = float(value)
            elif isinstance(value, (datetime, date)):
                # Convert both datetime and date objects to ISO format strings
                serialized[key] = value.isoformat()
            elif value is None:
                serialized[key] = None
            else:
                serialized[key] = value
        return serialized

    def upload_image_to_storage(self, bucket_name: str, file_path: str, image_data: bytes, content_type: str = "image/png") -> Optional[str]:
        """
        Upload an image file to Supabase Storage and return the public URL.
        
        Args:
            bucket_name: Name of the storage bucket
            file_path: Path within the bucket (e.g., "machine_id/date/beam_type/time/image.png")
            image_data: Image file data as bytes
            content_type: MIME type of the image (default: "image/png")
        
        Returns:
            str: Public URL of the uploaded image if successful, None otherwise
            Format: {SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{file_path}
        """
        if not self.connected or not self.client:
            logger.error("Not connected to Supabase")
            return None
        
        try:
            # Upload file to storage bucket
            # Supabase storage accepts bytes directly
            response = self.client.storage.from_(bucket_name).upload(
                path=file_path,
                file=image_data,  # Pass bytes directly
                file_options={"content-type": content_type, "upsert": "true"}
            )
            
            # Check if upload was successful
            if response is not None:
                logger.info(f"Successfully uploaded image to {bucket_name}/{file_path}")
                
                # Get the public URL for the uploaded file
                # Try to get public URL from Supabase client
                try:
                    # get_public_url() returns the full public URL
                    public_url = self.client.storage.from_(bucket_name).get_public_url(file_path)
                    if public_url:
                        logger.debug(f"Got public URL: {public_url}")
                        return public_url
                    else:
                        raise ValueError("get_public_url returned None")
                except (AttributeError, Exception) as url_error:
                    # Fallback: construct URL manually if get_public_url fails or doesn't exist
                    logger.debug(f"Constructing public URL manually: {url_error}")
                    # Get Supabase URL from connection params or environment
                    supabase_url = None
                    if hasattr(self, '_supabase_url'):
                        supabase_url = self._supabase_url
                    else:
                        # Try to get from environment or extract from client
                        supabase_url = os.getenv("SUPABASE_URL", "").rstrip('/')
                        # Store for future use
                        self._supabase_url = supabase_url
                    
                    if supabase_url:
                        public_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{file_path}"
                        logger.debug(f"Constructed public URL: {public_url}")
                        return public_url
                    else:
                        logger.error("Cannot construct public URL: SUPABASE_URL not available")
                        return None
            else:
                logger.warning(f"Upload response was empty for {file_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error uploading image to storage: {e}", exc_info=True)
            return None

    def _numpy_array_to_png_bytes(self, image_array: np.ndarray) -> Optional[bytes]:
        """
        Convert a numpy array image to PNG bytes.
        
        Args:
            image_array: NumPy array representing the image
        
        Returns:
            bytes: PNG image data as bytes, or None if conversion fails
        """
        try:
            # Normalize array to 0-255 range if needed
            if image_array.dtype != np.uint8:
                # Normalize to 0-1 range first
                if image_array.max() > 1.0:
                    image_array = image_array / image_array.max()
                # Convert to 0-255 range
                image_array = (image_array * 255).astype(np.uint8)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(image_array)
            
            # Convert to PNG bytes
            img_bytes = io.BytesIO()
            pil_image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            return img_bytes.getvalue()
            
        except Exception as e:
            logger.error(f"Error converting numpy array to PNG bytes: {e}", exc_info=True)
            return None

    def _matplotlib_figure_to_png_bytes(self, fig) -> Optional[bytes]:
        """
        Convert a matplotlib figure to PNG bytes.
        
        Args:
            fig: Matplotlib figure object
        
        Returns:
            bytes: PNG image data as bytes, or None if conversion fails
        """
        try:
            img_bytes = io.BytesIO()
            fig.savefig(img_bytes, format='PNG', dpi=300, bbox_inches='tight')
            img_bytes.seek(0)
            return img_bytes.getvalue()
            
        except Exception as e:
            logger.error(f"Error converting matplotlib figure to PNG bytes: {e}", exc_info=True)
            return None

    def upload_beam_images(self, bucket_name: str, base_folder_path: str, 
                          beam_image: Optional[np.ndarray] = None,
                          horizontal_profile: Optional[Any] = None,
                          vertical_profile: Optional[Any] = None) -> Optional[Dict[str, str]]:
        """
        Upload beam images to Supabase Storage.
        
        Args:
            bucket_name: Name of the storage bucket (e.g., "beam-images")
            base_folder_path: Base folder path (e.g., "SN6543/20250919/10x/074149")
            beam_image: NumPy array of the main beam image
            horizontal_profile: Matplotlib figure for horizontal profile graph
            vertical_profile: Matplotlib figure for vertical profile graph
        
        Returns:
            Dict[str, str]: Dictionary mapping image types to their public URLs, or None if upload fails
            Format: {
                "beamImage": "https://...supabase.co/storage/v1/object/public/beam-images/SN6543/20250919/6e/074149/beamImage.png",
                "horzProfile": "https://...supabase.co/storage/v1/object/public/beam-images/SN6543/20250919/6e/074149/horzProfile.png",
                "vertProfile": "https://...supabase.co/storage/v1/object/public/beam-images/SN6543/20250919/6e/074149/vertProfile.png"
            }
        """
        image_urls = {}
        
        # Upload main beam image
        if beam_image is not None:
            beam_image_bytes = self._numpy_array_to_png_bytes(beam_image)
            if beam_image_bytes:
                beam_image_path = f"{base_folder_path}/beamImage.png"
                public_url = self.upload_image_to_storage(bucket_name, beam_image_path, beam_image_bytes)
                if public_url:
                    image_urls["beamImage"] = public_url
                else:
                    logger.warning("Failed to upload beam image")
        
        # Upload horizontal profile graph
        if horizontal_profile is not None:
            horz_profile_bytes = self._matplotlib_figure_to_png_bytes(horizontal_profile)
            if horz_profile_bytes:
                horz_profile_path = f"{base_folder_path}/horzProfile.png"
                public_url = self.upload_image_to_storage(bucket_name, horz_profile_path, horz_profile_bytes)
                if public_url:
                    image_urls["horzProfile"] = public_url
                else:
                    logger.warning("Failed to upload horizontal profile graph")
        
        # Upload vertical profile graph
        if vertical_profile is not None:
            vert_profile_bytes = self._matplotlib_figure_to_png_bytes(vertical_profile)
            if vert_profile_bytes:
                vert_profile_path = f"{base_folder_path}/vertProfile.png"
                public_url = self.upload_image_to_storage(bucket_name, vert_profile_path, vert_profile_bytes)
                if public_url:
                    image_urls["vertProfile"] = public_url
                else:
                    logger.warning("Failed to upload vertical profile graph")
        
        if image_urls:
            logger.info(f"Successfully uploaded {len(image_urls)} image(s) to storage")
            return image_urls
        else:
            logger.warning("No images were successfully uploaded")
            return None

    def close(self):
        """Close the Supabase connection."""
        self.client = None
        self.connected = False
        logger.info("Supabase connection closed")


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
            db_adapter: Database adapter instance. If None, defaults to SupabaseAdapter
        """
        if db_adapter is None:
            self.db_adapter = SupabaseAdapter()
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

        if "ebeam" in model_type:
            return self.eModelUpload(model)
        elif "xbeam" in model_type:
            return self.xModelUpload(model)
        elif "geo" in model_type:
            return self.geoModelUpload(model)
        else:
            raise TypeError(f"Unsupported model type: {type(model).__name__}")

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
            
            logger.error(f"Uploaded {success_count}/{len(metrics)} baseline metric records")
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
            return self.testeModelUpload(model)
        elif "xbeam" in model_type:
            return self.testxModelUpload(model)
        elif "geo" in model_type:
            return self.testGeoModelUpload(model)
        else:
            raise TypeError(f"Unsupported model type: {type(model).__name__}")

    def _generate_image_folder_path(self, model) -> str:
        """
        Generate the base folder path for storing images in Supabase Storage.
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
        Maps to schema: type, date, path, rel_uniformity, rel_output, center_shift, machine_id, note
        
        For baselines: Uploads individual metric records to baseline table.
        For regular beams: Uploads single record to beam table.
        Also uploads images to Supabase Storage and stores paths in image_paths column.
        """
        try:
            # Check if this is a baseline
            if eBeam.get_baseline():
                # Upload to baseline table as individual metric records
                return self._upload_baseline_metrics(eBeam, check_type='beam')
            else:
                # Upload images to Supabase Storage first
                image_urls = None
                image_model = eBeam.get_image_model()
                if image_model:
                    base_folder_path = self._generate_image_folder_path(eBeam)
                    
                    # Get images from the model
                    beam_image = image_model.get_image() if hasattr(image_model, 'get_image') else None
                    horizontal_profile = eBeam.get_horizontal_profile_graph()
                    vertical_profile = eBeam.get_vertical_profile_graph()
                    
                    # Upload images (using default bucket name "beam-images", can be configured)
                    # Returns dictionary with public URLs: {"beamImage": "https://...", "horzProfile": "https://...", "vertProfile": "https://..."}
                    image_urls = self.db_adapter.upload_beam_images(
                        bucket_name="beam-images",
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
                return self.db_adapter.upload_beam_data('beams', data)

        except Exception as e:
            logger.error(f"Error during E-beam upload: {e}", exc_info=True)
            return False


    # --- X-BEAM ---
    def xModelUpload(self, xBeam):
        """
        Upload data for X-beam model to the single beam table or baseline table.
        Maps to schema: type, date, path, rel_uniformity, rel_output, center_shift, machine_id, note
        
        For baselines: Uploads individual metric records to baseline table.
        For regular beams: Uploads single record to beam table.
        Also uploads images to Supabase Storage and stores paths in image_paths column.
        """
        try:
            # Check if this is a baseline
            if xBeam.get_baseline():
                # Upload to baseline table as individual metric records
                return self._upload_baseline_metrics(xBeam, check_type='beam')
            else:
                # Upload images to Supabase Storage first
                image_urls = None
                image_model = xBeam.get_image_model()
                if image_model:
                    base_folder_path = self._generate_image_folder_path(xBeam)
                    
                    # Get images from the model
                    beam_image = image_model.get_image() if hasattr(image_model, 'get_image') else None
                    horizontal_profile = xBeam.get_horizontal_profile_graph()
                    vertical_profile = xBeam.get_vertical_profile_graph()
                    
                    # Upload images (using default bucket name "beam-images", can be configured)
                    # Returns dictionary with public URLs: {"beamImage": "https://...", "horzProfile": "https://...", "vertProfile": "https://..."}
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
                return self.db_adapter.upload_beam_data('beams', data)

        except Exception as e:
            logger.error(f"Error during X-beam upload: {e}", exc_info=True)
            return False


    # --- GEO MODEL ---
    def geoModelUpload(self, geoModel):
        """
        Upload data for GeoModel to the single beam table or baseline table.
        Maps to schema: type, date, path, rel_uniformity, rel_output, center_shift, machine_id, note
        
        For baselines: Uploads individual metric records to baseline table.
        For regular beams: Uploads single record to beam table.
        Also uploads images to Supabase Storage and stores paths in image_paths column.
        
        Note: Geometry models have additional data (isocenter, gantry, couch, MLC, jaws) 
        that is not stored in the basic beam table. The full extraction code is 
        commented out below for easy re-enabling when geometry tables are created.
        """
        try:
            # Check if this is a baseline
            if geoModel.get_baseline():
                # Upload to baseline table as individual metric records
                return self._upload_baseline_metrics(geoModel, check_type='geometry')
            else:
                # Upload images to Supabase Storage first
                image_urls = None
                image_model = geoModel.get_image_model()
                if image_model:
                    base_folder_path = self._generate_image_folder_path(geoModel)
                    
                    # Get images from the model
                    beam_image = image_model.get_image() if hasattr(image_model, 'get_image') else None
                    horizontal_profile = geoModel.get_horizontal_profile_graph()
                    vertical_profile = geoModel.get_vertical_profile_graph()
                    
                    # Upload images (using default bucket name "beam-images", can be configured)
                    # Returns dictionary with public URLs: {"beamImage": "https://...", "horzProfile": "https://...", "vertProfile": "https://..."}
                    image_urls = self.db_adapter.upload_beam_images(
                        bucket_name="beam-images",
                        base_folder_path=base_folder_path,
                        beam_image=beam_image,
                        horizontal_profile=horizontal_profile,
                        vertical_profile=vertical_profile
                    )
                
                # Prepare basic beam data matching the beam table schema
                data = {
                    'typeID': geoModel.get_typeID(),
                    'type': geoModel.get_type(),
                    'date': geoModel.get_date(),
                    'path': geoModel.get_path(),
                    'rel_uniformity': geoModel.get_relative_uniformity(),
                    'rel_output': geoModel.get_relative_output(),
                    'center_shift': geoModel.get_center_shift(),
                    'vert_flatness': geoModel.get_flatness_vertical(),
                    'hori_flatness': geoModel.get_flatness_horizontal(),
                    'vert_symmetry': geoModel.get_symmetry_vertical(),
                    'hori_symmetry': geoModel.get_symmetry_horizontal(),
                    'machine_id': geoModel.get_machine_SN(),
                    'note': None,  # Add note if available in the model
                    'image_paths': json.dumps(image_urls) if image_urls else None  # Store public URLs as JSONB
                }
                result = self.db_adapter.upload_beam_data('beams', data)
                result_id = result.get('id') if isinstance(result, dict) else None
                if not result_id:
                    raise RuntimeError("Failed to get beam result_id from upload_beam_data()")
            
            # ========================================================================
            # COMMENTED OUT: Full geometry data extraction
            # Uncomment when geometry_data table is created
            # ========================================================================
            
            # ---- Extract IsoCenterGroup data ----
            isocenter_data = {
                'beam_id': result_id,  # Foreign key to beam table
                'isoCenterSize': geoModel.get_IsoCenterSize(),
                'isoCenterMVOffset': geoModel.get_IsoCenterMVOffset(),
                'isoCenterKVOffset': geoModel.get_IsoCenterKVOffset(),
            }
            
            # ---- Extract CollimationGroup data ----
            collimation_data = {
                'beam_id': result_id,
                'collimationRotationOffset': geoModel.get_CollimationRotationOffset(),
            }
            
            # ---- Extract GantryGroup data ----
            gantry_data = {
                'beam_id': result_id,
                'gantryAbsolute': geoModel.get_GantryAbsolute(),
                'gantryRelative': geoModel.get_GantryRelative(),
            }
            
            # ---- Extract EnhancedCouchGroup data ----
            couch_data = {
                'beam_id': result_id,
                'couchMaxPositionError': geoModel.get_CouchMaxPositionError(),
                'couchLat': geoModel.get_CouchLat(),
                'couchLng': geoModel.get_CouchLng(),
                'couchVrt': geoModel.get_CouchVrt(),
                'couchRtnFine': geoModel.get_CouchRtnFine(),
                'couchRtnLarge': geoModel.get_CouchRtnLarge(),
                'rotationInducedCouchShiftFullRange': geoModel.get_RotationInducedCouchShiftFullRange(),
            }
            
            # ---- Extract MLC Leaves data (A and B banks, leaves 11-50) ----
            mlc_leaves_a = {}
            mlc_leaves_b = {}
            for i in range(11, 51):
                mlc_leaves_a[f"leaf_{i}"] = geoModel.get_MLCLeafA(i)
                mlc_leaves_b[f"leaf_{i}"] = geoModel.get_MLCLeafB(i)
            
            # ---- Extract MLC Offsets ----
            mlc_offset_data = {
                'beam_id': result_id,
                'mlcMaxOffsetA': geoModel.get_MaxOffsetA(),
                'mlcMaxOffsetB': geoModel.get_MaxOffsetB(),
                'mlcMeanOffsetA': geoModel.get_MeanOffsetA(),
                'mlcMeanOffsetB': geoModel.get_MeanOffsetB(),
                #'mlcLeavesA': json.dumps(mlc_leaves_a),  # Store as JSONB
                #'mlcLeavesB': json.dumps(mlc_leaves_b),  # Store as JSONB
                'mlcLeavesA': json.dumps(self.make_json_safe(mlc_leaves_a)),
                'mlcLeavesB': json.dumps(self.make_json_safe(mlc_leaves_b)),
            }
            
            # ---- Extract MLC Backlash data (A and B banks, leaves 11-50) ----
            mlc_backlash_a = {}
            mlc_backlash_b = {}
            for i in range(11, 51):
                mlc_backlash_a[f"leaf_{i}"] = geoModel.get_MLCBacklashA(i)
                mlc_backlash_b[f"leaf_{i}"] = geoModel.get_MLCBacklashB(i)
            
            mlc_backlash_data = {
                'beam_id': result_id,
                'mlcBacklashMaxA': geoModel.get_MLCBacklashMaxA(),
                'mlcBacklashMaxB': geoModel.get_MLCBacklashMaxB(),
                'mlcBacklashMeanA': geoModel.get_MLCBacklashMeanA(),
                'mlcBacklashMeanB': geoModel.get_MLCBacklashMeanB(),
                #'mlcBacklashA': json.dumps(mlc_backlash_a),  # Store as JSONB
                #'mlcBacklashB': json.dumps(mlc_backlash_b),  # Store as JSONB
                'mlcBacklashA': json.dumps(self.make_json_safe(mlc_backlash_a)),  # Store as JSONB
                'mlcBacklashB': json.dumps(self.make_json_safe(mlc_backlash_b)),  # Store as JSONB
            }
            
            # ---- Extract Jaws data ----
            jaws_data = {
                'beam_id': result_id,
                'jawX1': geoModel.get_JawX1(),
                'jawX2': geoModel.get_JawX2(),
                'jawY1': geoModel.get_JawY1(),
                'jawY2': geoModel.get_JawY2(),
            }
            
            # ---- Extract Jaw Parallelism data ----
            jaw_parallelism_data = {
                'beam_id': result_id,
                'jawParallelismX1': geoModel.get_JawParallelismX1(),
                'jawParallelismX2': geoModel.get_JawParallelismX2(),
                'jawParallelismY1': geoModel.get_JawParallelismY1(),
                'jawParallelismY2': geoModel.get_JawParallelismY2(),
            }
            
            # ---- Upload to geometry tables ----
            # Uncomment and adjust table names when geometry tables are created
            self.db_adapter.upload_beam_data('geometry_isocenter', isocenter_data)
            self.db_adapter.upload_beam_data('geometry_collimation', collimation_data)
            self.db_adapter.upload_beam_data('geometry_gantry', gantry_data)
            self.db_adapter.upload_beam_data('geometry_couch', couch_data)
            self.db_adapter.upload_beam_data('geometry_mlc', mlc_offset_data)
            self.db_adapter.upload_beam_data('geometry_mlc_backlash', mlc_backlash_data)
            self.db_adapter.upload_beam_data('geometry_jaws', jaws_data)
            self.db_adapter.upload_beam_data('geometry_jaw_parallelism', jaw_parallelism_data)
            
            # ========================================================================
            # END OF COMMENTED GEOMETRY DATA
            # ========================================================================
            
            return result

        except Exception as e:
            logger.error(f"Error during Geo model upload: {e}", exc_info=True)
            return False

    def uploadMLCLeaves(self, geoModel, table_name: str = 'mlc_leaves_data'):
        """
        Upload MLC leaf data separately (optional helper method).
        This can be called after geoModelUpload() if you want to store
        individual leaf data in a separate table.
        """
        try:
            leaves_data = []
            
            # Collect all MLC leaf A data (leaves 1-60)
            for i in range(1, 61):
                leaves_data.append({
                    'date': geoModel.get_date(),
                    'machine_sn': geoModel.get_machine_SN(),
                    'leaf_bank': 'A',
                    'leaf_index': i,
                    'leaf_value': geoModel.get_MLCLeafA(i),
                })
            
            # Collect all MLC leaf B data (leaves 1-60)
            for i in range(1, 61):
                leaves_data.append({
                    'date': geoModel.get_date(),
                    'machine_sn': geoModel.get_machine_SN(),
                    'leaf_bank': 'B',
                    'leaf_index': i,
                    'leaf_value': geoModel.get_MLCLeafB(i),
                })
            
            # Upload each leaf record
            success_count = 0
            for leaf_data in leaves_data:
                if self.db_adapter.upload_beam_data(table_name, leaf_data):
                    success_count += 1
            
            logger.info(f"Uploaded {success_count}/{len(leaves_data)} MLC leaf records")
            return success_count == len(leaves_data)

        except Exception as e:
            logger.error(f"Error uploading MLC leaves: {e}", exc_info=True)
            return False

    def uploadMLCBacklash(self, geoModel, table_name: str = 'mlc_backlash_data'):
        """
        Upload MLC backlash data separately (optional helper method).
        This can be called after geoModelUpload() if you want to store
        individual backlash data in a separate table.
        """
        try:
            backlash_data = []
            
            # Collect all MLC backlash A data (leaves 1-60)
            for i in range(1, 61):
                backlash_data.append({
                    'date': geoModel.get_date(),
                    'machine_sn': geoModel.get_machine_SN(),
                    'leaf_bank': 'A',
                    'leaf_index': i,
                    'backlash_value': geoModel.get_MLCBacklashA(i),
                })
            
            # Collect all MLC backlash B data (leaves 1-60)
            for i in range(1, 61):
                backlash_data.append({
                    'date': geoModel.get_date(),
                    'machine_sn': geoModel.get_machine_SN(),
                    'leaf_bank': 'B',
                    'leaf_index': i,
                    'backlash_value': geoModel.get_MLCBacklashB(i),
                })
            
            # Upload each backlash record
            success_count = 0
            for backlash_record in backlash_data:
                if self.db_adapter.upload_beam_data(table_name, backlash_record):
                    success_count += 1
            
            logger.info(f"Uploaded {success_count}/{len(backlash_data)} MLC backlash records")
            return success_count == len(backlash_data)

        except Exception as e:
            logger.error(f"Error uploading MLC backlash: {e}", exc_info=True)
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

    def close(self):
        """Close the database connection."""
        if self.db_adapter and hasattr(self.db_adapter, 'close'):
            self.db_adapter.close()


