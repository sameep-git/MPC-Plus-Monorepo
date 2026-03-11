"""
Database Adapter (Abstract Interface)
--------------------------------------
Defines the abstract interface for database operations.
Implementations should provide concrete methods for connecting and uploading data.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


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
    def upload_beam_images(
        self, 
        bucket_name: str, 
        base_folder_path: str, 
        beam_image: Any = None,
        horizontal_profile: Any = None,
        vertical_profile: Any = None,
        flood_image: Any = None
    ) -> Dict[str, str]:
        """Upload images associated with a beam."""
        pass

    @abstractmethod
    def get_recent_flood_image_paths(
        self, 
        machine_id: str, 
        beam_type: str, 
        before_timestamp: Any, 
        limit: int = 5
    ) -> list:
        """Fetch paths of recent flood images from the database."""
        pass

    @abstractmethod
    def close(self):
        """Close the database connection."""
        pass
