"""
PostgreSQL Database Adapter
----------------------------
Concrete implementation of DatabaseAdapter for PostgreSQL.
Uses psycopg2 library.
Handles image uploads by saving to local filesystem (for self-hosted setup).
"""

from typing import Dict, Any, Optional
import logging
import os
import io
import numpy as np
from PIL import Image
import psycopg2
from psycopg2 import sql, extras

from src.data_manipulation.ETL.db.adapter import DatabaseAdapter

# Set up logger for this module
logger = logging.getLogger(__name__)


class PostgresAdapter(DatabaseAdapter):
    """
    Concrete implementation of DatabaseAdapter for PostgreSQL.
    Uses psycopg2 library.
    Handles image uploads by saving to local filesystem (for self-hosted setup).
    """

    def __init__(self):
        self.conn = None
        self.connected = False
        # Local storage path for saved images.
        # STORAGE_ROOT env var overrides the default relative path.
        # Default: src/api/wwwroot/images (relative to the backend root).
        # __file__ is at backend/src/data_manipulation/ETL/db/postgres_adapter.py
        #   → dirname five levels up = backend/
        _this_dir = os.path.dirname(os.path.abspath(__file__))
        _backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_this_dir))))
        self.storage_root = os.environ.get("STORAGE_ROOT") or os.path.join(
            _backend_root, "src", "api", "wwwroot", "images"
        )
        
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
                dbname = connection_params.get('dbname', 'mpc_plus')
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

    def get_app_timezone(self) -> str | None:
        """
        Look up the configured timezone from the app_settings table.
        Returns the IANA timezone name (e.g. 'America/Chicago') or None.
        """
        if not self.connected or not self.conn:
            return None
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT value FROM app_settings WHERE key = 'timezone'"
                )
                row = cur.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"Error fetching timezone from app_settings: {e}")
            return None

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
            
            # Special handling for JSON fields (image_paths)
            
            columns = data.keys()
            values = [data[k] for k in columns]
            # FIX: convert numpy scalars to python types
            values = [
                v.item() if isinstance(v, np.generic) else v
                for v in values
            ]
            
            query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING *").format(
                sql.Identifier(table_name),
                sql.SQL(', ').join(map(sql.Identifier, columns)),
                sql.SQL(', ').join(sql.Placeholder() * len(columns))
            )
            
            # Determine conflict target for UPSERT functionality
            if table_name in ['beams', 'geochecks']:
                conflict_target = sql.SQL("(path)")
            elif table_name == 'baselines':
                conflict_target = sql.SQL("(machine_id, check_type, beam_variant, metric_type)")
            else:
                conflict_target = None

            if conflict_target:
                set_clauses = sql.SQL(', ').join(
                    sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(col), sql.Identifier(col))
                    for col in columns
                )
                query = sql.SQL(
                    "INSERT INTO {} ({}) VALUES ({}) "
                    "ON CONFLICT {} DO UPDATE SET {} "
                    "RETURNING *"
                ).format(
                    sql.Identifier(table_name),
                    sql.SQL(', ').join(map(sql.Identifier, columns)),
                    sql.SQL(', ').join(sql.Placeholder() * len(columns)),
                    conflict_target,
                    set_clauses
                )
            else:
                query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING *").format(
                    sql.Identifier(table_name),
                    sql.SQL(', ').join(map(sql.Identifier, columns)),
                    sql.SQL(', ').join(sql.Placeholder() * len(columns))
                )
                
            values = tuple(float(data[k]) if isinstance(data[k], np.floating) else data[k] for k in columns)
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
                    f"INSERT INTO {table_name} (geocheck_id, leaf_number, leaf_value) VALUES %s "
                    "ON CONFLICT (geocheck_id, leaf_number) DO UPDATE SET leaf_value = EXCLUDED.leaf_value",
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
                    f"INSERT INTO {table_name} (geocheck_id, leaf_number, backlash_value) VALUES %s "
                    "ON CONFLICT (geocheck_id, leaf_number) DO UPDATE SET backlash_value = EXCLUDED.backlash_value",
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
                          vertical_profile: Optional[Any] = None,
                          flood_image: Optional[np.ndarray] = None) -> Optional[Dict[str, str]]:
        
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
            
            if flood_image is not None:
                # Save RAW data as .npy to preserve bit depth for future gain map calculations
                npy_path = os.path.join(full_path, "floodImage_raw.npy")
                np.save(npy_path, flood_image)
                image_urls["floodImage_raw"] = f"{self.base_url}/{base_folder_path}/floodImage_raw.npy"
            
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

    def get_recent_flood_image_paths(self, machine_id: str, beam_type: str, 
                                     before_timestamp: Any, limit: int = 5) -> list:
        """
        Fetch the paths of the most recent flood images for a given machine and beam type
        that occurred BEFORE the provided timestamp.
        """
        if not self.connected or not self.conn:
            return []
            
        try:
            with self.conn.cursor() as cur:
                # Query the beams table for records matching machine_id and type
                # that are strictly older than before_timestamp.
                # Extract both 'floodImage' (PNG) and 'floodImage_raw' (NPY) paths.
                query = """
                    SELECT 
                        image_paths->>'floodImage',
                        image_paths->>'floodImage_raw'
                    FROM beams 
                    WHERE machine_id = %s 
                      AND type = %s 
                      AND timestamp < %s 
                      AND (image_paths->>'floodImage' IS NOT NULL OR image_paths->>'floodImage_raw' IS NOT NULL)
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """
                cur.execute(query, (machine_id, beam_type, before_timestamp, limit))
                rows = cur.fetchall()
                # Return a list of tuples (png_path, npy_path)
                return [(row[0], row[1]) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching recent flood image paths: {e}")
            return []

    def resolve_url_to_path(self, url: str) -> Optional[str]:
        """
        Resolve a stored URL/relative path to a local absolute filesystem path.
        Handles the storage_root and base_url conventions used by this adapter.
        """
        if not url:
            return None
        
        # Replace the base_url prefix if present
        # e.g., "/images/SN6543/..." -> "SN6543/..."
        clean_rel = url
        if self.base_url and clean_rel.startswith(self.base_url):
            clean_rel = clean_rel[len(self.base_url):]
        
        # Remove leading slash if any
        if clean_rel.startswith("/") or clean_rel.startswith("\\"):
            clean_rel = clean_rel[1:]
            
        # Normalize slashes for the current OS
        clean_rel = clean_rel.replace("/", os.sep).replace("\\", os.sep)
        
        # Join with storage_root
        return os.path.join(self.storage_root, clean_rel)

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.connected = False
            logger.info("PostgreSQL connection closed")
