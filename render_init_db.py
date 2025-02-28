"""
Database initialization script specifically for Render deployments.
This script will create all necessary database tables.
"""

import os
import sys
import logging
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))
logging.basicConfig(
    level=logging_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database by creating all tables"""
    try:
        logger.info("Starting database initialization for Render deployment")
        
        # Log environment variables (without sensitive values)
        logger.info("Environment variables:")
        logger.info(f"FLASK_ENV: {os.getenv('FLASK_ENV', 'not set')}")
        logger.info(f"LOG_LEVEL: {os.getenv('LOG_LEVEL', 'not set')}")
        logger.info(f"DATABASE_URL set: {'Yes' if os.getenv('DATABASE_URL') else 'No'}")
        logger.info(f"RENDER set: {'Yes' if os.getenv('RENDER') else 'No'}")
        
        # Try to import the serverless app first
        try:
            logger.info("Importing serverless Flask app")
            from app_serverless import app
            logger.info("Successfully imported serverless app")
        except ImportError as e:
            logger.warning(f"Could not import serverless app: {str(e)}")
            logger.info("Falling back to regular app")
            from app import app
            logger.info("Successfully imported regular app")
        
        # Import models
        logger.info("Importing database models")
        from models import db, User, Product, PriceHistory, URL
        logger.info("Successfully imported models")
        
        # Create all tables
        with app.app_context():
            logger.info("Creating database tables")
            db.create_all()
            logger.info("All database tables created successfully")
            
            # Check if tables were created
            table_count = len(db.metadata.tables)
            logger.info(f"Created {table_count} tables")
            
            # List the tables that were created
            table_names = list(db.metadata.tables.keys())
            logger.info(f"Tables created: {', '.join(table_names)}")
            
            return {
                "success": True,
                "message": f"Database initialized with {table_count} tables: {', '.join(table_names)}"
            }
            
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {
            "success": False,
            "message": f"Error initializing database: {str(e)}"
        }

if __name__ == "__main__":
    result = init_database()
    print(result)
    
    if result["success"]:
        logger.info("Database initialization completed successfully")
        sys.exit(0)
    else:
        logger.error("Database initialization failed")
        sys.exit(1)
