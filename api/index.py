"""
Entry point for Vercel deployment of the E-commerce Price Monitor application.
This file configures the application for serverless deployment.
"""

import os
import sys

# Add the parent directory to the path so we can import our app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set serverless environment flag
os.environ['VERCEL_ENV'] = 'production'
os.environ['SERVERLESS'] = 'true'

# Import the Flask app
from app import app

# Vercel needs the app to be named 'app'
app.config.update(
    SERVER_NAME=None,
    APPLICATION_ROOT="/",
    SERVERLESS=True
)

# For Vercel, we'll use the configured DATABASE_URL (Supabase PostgreSQL)
# If DATABASE_URL is not set, fallback to in-memory SQLite
if 'DATABASE_URL' not in os.environ:
    app.logger.warning("DATABASE_URL not set. Using in-memory SQLite database.")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
else:
    app.logger.info(f"Using external database: {os.environ.get('DATABASE_URL')}")

# Disable scheduler in serverless environment
# For Vercel, you would use a separate service for scheduled tasks
if hasattr(app, 'apscheduler'):
    app.apscheduler.shutdown()

# This is needed for Vercel
def handler(event, context):
    return app(event, context)

# This allows local testing
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
