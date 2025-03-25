from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import time
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("MYSQL_USER", "auth_user")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
DB_NAME = os.getenv("MYSQL_DATABASE", "auth_db")

# Create SQLAlchemy connection string
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Connection retry logic
def get_engine(max_retries=5, retry_interval=5):
    retries = 0
    last_exception = None
    
    while retries < max_retries:
        try:
            logger.info(f"Attempting to connect to database (attempt {retries+1}/{max_retries})")
            engine = create_engine(
                SQLALCHEMY_DATABASE_URL,
                pool_pre_ping=True,
                pool_recycle=3600,
                isolation_level="READ COMMITTED"
            )
            # Test the connection - use text() to make it executable
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to the database")
            return engine
        except Exception as e:
            last_exception = e
            retries += 1
            logger.warning(f"Failed to connect to database: {str(e)}. Retrying in {retry_interval} seconds...")
            time.sleep(retry_interval)
    
    logger.error(f"Failed to connect to database after {max_retries} attempts: {str(last_exception)}")
    raise last_exception

# Create engine with retry logic
engine = get_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 