from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ERPConnector(ABC):
    """
    Abstract base class for all ERP connectors.
    Defines the common interface that all ERP connectors must implement.
    """
    
    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the connector with configuration parameters.
        
        Args:
            config: Dictionary containing connection parameters and credentials
        """
        self.config = config
        self.connection = None
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the ERP system.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        Close connection to the ERP system.
        
        Returns:
            bool: True if disconnection was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test the connection to the ERP system.
        
        Returns:
            bool: True if connection is working, False otherwise
        """
        pass
    
    @abstractmethod
    def get_metadata(self, entity_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve metadata about available entities/tables in the ERP.
        
        Args:
            entity_type: Optional type of entity to get metadata for
            
        Returns:
            Dict containing metadata information
        """
        pass
    
    @abstractmethod
    def get_data(self, entity: str, filters: Optional[Dict[str, Any]] = None, 
                fields: Optional[List[str]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve data from the ERP system.
        
        Args:
            entity: Entity/table name to retrieve data from
            filters: Optional filters to apply
            fields: Optional list of fields to retrieve
            limit: Optional maximum number of records to retrieve
            
        Returns:
            List of dictionaries containing the retrieved data
        """
        pass
    
    @abstractmethod
    def get_schema(self, entity: str) -> Dict[str, Any]:
        """
        Get the schema definition for a specific entity.
        
        Args:
            entity: Entity/table name
            
        Returns:
            Dict containing schema information
        """
        pass


class ERPAuthHandler(ABC):
    """
    Abstract base class for ERP authentication handlers.
    """
    
    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the auth handler with configuration.
        
        Args:
            config: Dictionary containing authentication parameters
        """
        self.config = config
    
    @abstractmethod
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Dict of header name/value pairs
        """
        pass
    
    @abstractmethod
    def refresh_credentials(self) -> bool:
        """
        Refresh authentication credentials if needed.
        
        Returns:
            bool: True if refresh was successful, False otherwise
        """
        pass 