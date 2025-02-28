#!/usr/bin/env python3
"""
Startup script for the E-commerce Price Monitor application.
This script handles setup and initialization before running the app.
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

def setup_logging(level):
    """Set up logging configuration"""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log")
        ]
    )
    return logging.getLogger(__name__)

def check_env_file():
    """Check if .env file exists and create it from .env.example if not"""
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            print("No .env file found. Creating from .env.example...")
            with open('.env.example', 'r') as example_file:
                example_content = example_file.read()
            
            with open('.env', 'w') as env_file:
                env_file.write(example_content)
            print(".env file created. Please update it with your configuration.")
        else:
            print("Warning: No .env or .env.example file found. Application may not function correctly.")

def init_db():
    """Initialize the database if it doesn't exist"""
    from app import app, db
    with app.app_context():
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            if not os.path.exists(db_path):
                print(f"Initializing database: {db_path}")
                db.create_all()
                print("Database initialized.")
            else:
                print(f"Database already exists: {db_path}")

def create_admin_user(username, email, password):
    """Create an admin user if none exists"""
    from app import app
    from models import db, User
    
    with app.app_context():
        # Check if any users exist
        user_count = User.query.count()
        
        if user_count == 0:
            print(f"Creating admin user: {username}")
            admin = User(username=username, email=email, is_admin=True)
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully.")
        else:
            print("Users already exist. Skipping admin creation.")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="E-commerce Price Monitor")
    parser.add_argument('-d', '--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('-p', '--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('-H', '--host', default='127.0.0.1', help='Host to run the server on')
    parser.add_argument('-l', '--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Logging level')
    parser.add_argument('--init-db', action='store_true', help='Initialize the database')
    parser.add_argument('--create-admin', action='store_true', help='Create an admin user if none exists')
    parser.add_argument('--admin-username', default='admin', help='Admin username (used with --create-admin)')
    parser.add_argument('--admin-email', default='admin@example.com', help='Admin email (used with --create-admin)')
    parser.add_argument('--admin-password', default='admin', help='Admin password (used with --create-admin)')
    return parser.parse_args()

def main():
    """Main entry point"""
    # Parse command-line arguments
    args = parse_args()
    
    # Setup logging
    logger = setup_logging(args.log_level)
    logger.info("Starting E-commerce Price Monitor")
    
    # Check and create .env file if needed
    check_env_file()
    
    # Load environment variables
    load_dotenv()
    
    # Initialize the database if requested
    if args.init_db:
        init_db()
    
    # Create admin user if requested
    if args.create_admin:
        create_admin_user(args.admin_username, args.admin_email, args.admin_password)
    
    # Import the Flask app
    from app import app
    from context_processors import register_context_processors
    
    # Register context processors
    register_context_processors(app)
    
    # Check if this is being run directly or imported
    if __name__ == "__main__":
        logger.info(f"Running server on {args.host}:{args.port}")
        app.run(host=args.host, port=args.port, debug=args.debug)
    
    return app

if __name__ == "__main__":
    app = main()
