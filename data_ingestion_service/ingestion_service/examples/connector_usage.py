import os
import logging
from dotenv import load_dotenv
from ..connectors.factory import ERPConnectorFactory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def connect_to_netsuite():
    """
    Example function to connect to NetSuite
    """
    # Configuration should come from environment variables or Key Vault in production
    netsuite_config = {
        'account_id': os.getenv('NETSUITE_ACCOUNT_ID'),
        'api_version': os.getenv('NETSUITE_API_VERSION', '2020_1'),
        'oauth': {
            'account_id': os.getenv('NETSUITE_ACCOUNT_ID'),
            'consumer_key': os.getenv('NETSUITE_CONSUMER_KEY'),
            'consumer_secret': os.getenv('NETSUITE_CONSUMER_SECRET'),
            'token_id': os.getenv('NETSUITE_TOKEN_ID'),
            'token_secret': os.getenv('NETSUITE_TOKEN_SECRET')
        }
    }
    
    try:
        # Create the connector
        connector = ERPConnectorFactory.create_connector('netsuite', netsuite_config)
        
        # Connect to NetSuite
        if connector.connect():
            logger.info("Successfully connected to NetSuite")
            
            # Get metadata
            metadata = connector.get_metadata()
            logger.info(f"Available records: {metadata['records']}")
            
            # Get schema for accounts
            account_schema = connector.get_schema('account')
            logger.info(f"Account schema: {account_schema}")
            
            # Get some account data (this would return real data in a complete implementation)
            accounts = connector.get_data('account', limit=10)
            logger.info(f"Retrieved {len(accounts)} accounts")
            
            # Disconnect
            connector.disconnect()
            logger.info("Disconnected from NetSuite")
        else:
            logger.error("Failed to connect to NetSuite")
    
    except Exception as e:
        logger.error(f"Error in NetSuite connector example: {str(e)}")

if __name__ == "__main__":
    connect_to_netsuite() 