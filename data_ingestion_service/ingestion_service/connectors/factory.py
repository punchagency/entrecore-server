from typing import Dict, Any
import logging
from .base import ERPConnector
from .netsuite.connector import NetSuiteConnector

logger = logging.getLogger(__name__)

class ERPConnectorFactory:
    """
    Factory for creating ERP connectors based on type.
    """
    
    @staticmethod
    def create_connector(erp_type: str, config: Dict[str, Any]) -> ERPConnector:
        """
        Create and return a connector for the specified ERP type.
        
        Args:
            erp_type: Type of ERP ('netsuite', 'sap', 'oracle', etc.)
            config: Configuration parameters for the connector
            
        Returns:
            An initialized ERPConnector instance
            
        Raises:
            ValueError: If erp_type is not supported
        """
        erp_type = erp_type.lower()
        
        if erp_type == 'netsuite':
            logger.info(f"Creating NetSuite connector")
            return NetSuiteConnector(config)
        # Add additional ERP types here as they are implemented
        # elif erp_type == 'sap':
        #     return SAPConnector(config)
        # elif erp_type == 'oracle':
        #     return OracleERPConnector(config)
        else:
            logger.error(f"Unsupported ERP type: {erp_type}")
            raise ValueError(f"Unsupported ERP type: {erp_type}") 