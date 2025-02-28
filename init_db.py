"""
Database initialization script for traditional Flask deployments.
This script will create all necessary database tables.
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database by creating all tables"""
    try:
        # Import the Flask app and database models
        from app import app
        from models import db, User, Product, PriceHistory, URL
        
        with app.app_context():
            # Log database URI (without password)
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            if 'postgres' in db_uri:
                # Mask the password in the connection string for logging
                masked_uri = db_uri.replace('//', '//[username]:[password]@')
                logger.info(f"Database URI: {masked_uri}")
            else:
                logger.info(f"Database URI: {db_uri}")
                
            # Create all tables
            db.create_all()
            logger.info("All database tables created successfully")
            
            # Check if tables were created
            table_count = len(db.metadata.tables)
            logger.info(f"Created {table_count} tables")
            
            return {
                "success": True,
                "message": f"Database initialized with {table_count} tables"
            }
            
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        return {
            "success": False,
            "message": f"Error initializing database: {str(e)}"
        }

if __name__ == "__main__":
    result = init_database()
    print(result)
