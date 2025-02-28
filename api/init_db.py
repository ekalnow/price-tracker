"""
Database initialization script for Vercel deployment.
This script will create all necessary database tables in Supabase.
"""

import os
import sys
import logging
import traceback

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Add the parent directory to the path so we can import our app modules
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Set serverless environment flag
    os.environ['VERCEL_ENV'] = 'production'
    os.environ['SERVERLESS'] = 'true'
    
    logger.info("Starting database initialization")
    
    # Log environment variables (without sensitive values)
    logger.info(f"Environment variables:")
    logger.info(f"FLASK_ENV: {os.environ.get('FLASK_ENV')}")
    logger.info(f"LOG_LEVEL: {os.environ.get('LOG_LEVEL')}")
    logger.info(f"DATABASE_URL set: {'Yes' if 'DATABASE_URL' in os.environ else 'No'}")
    
    # Import the Flask app and database models
    logger.info("Importing Flask app and models")
    
    # First try to import the serverless version of the app
    try:
        # Import the serverless version of the Flask app
        from api.app_serverless import app
        logger.info("Successfully imported serverless app version")
    except ImportError:
        # Fall back to the regular app if serverless version is not available
        logger.warning("Serverless app version not found, falling back to regular app")
        from app import app
    
    from models import db, User, Product, PriceHistory, URL
    
    def init_database():
        """Initialize the database by creating all tables"""
        try:
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
                logger.info("Creating database tables...")
                db.create_all()
                logger.info("✅ Database tables created successfully")
                
                # List all tables
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                tables = inspector.get_table_names()
                logger.info(f"Tables in database: {', '.join(tables)}")
                
                return {"status": "success", "message": "Database initialized successfully", "tables": tables}
        except Exception as e:
            error_msg = f"Error creating database tables: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"status": "error", "message": error_msg}
    
except Exception as e:
    logger.error(f"Error in setup: {str(e)}")
    logger.error(traceback.format_exc())
    # Re-raise the exception to ensure Vercel sees the error
    raise

def handler(event, context):
    try:
        result = init_database()
        return {
            "statusCode": 200 if result["status"] == "success" else 500,
            "body": result
        }
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "statusCode": 500,
            "body": {"status": "error", "message": str(e)}
        }

if __name__ == "__main__":
    result = init_database()
    print(result)
