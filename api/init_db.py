"""
Database initialization script for Vercel deployment.
This script will create all necessary database tables in Supabase.
"""

import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the path so we can import our app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Set serverless environment flag
os.environ['VERCEL_ENV'] = 'production'
os.environ['SERVERLESS'] = 'true'

# Import the Flask app and database models
from app import app
from models import db, User, Product, PriceHistory, URL

def init_database():
    """Initialize the database by creating all tables"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully")
        
        # List all tables
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Tables in database: {', '.join(tables)}")

if __name__ == "__main__":
    init_database()
