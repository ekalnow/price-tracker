"""
Entry point for Vercel deployment of the E-commerce Price Monitor application.
This file configures the application for serverless deployment.
"""

import os
import sys

# Add the parent directory to the path so we can import our app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app
from app import app

# Vercel needs the app to be named 'app'
app.config.update(
    SERVER_NAME=None,
    APPLICATION_ROOT="/"
)

# For Vercel, we'll use SQLite in memory or a temporary file since we can't write to the filesystem
# You might want to consider using a managed database service in production
if os.environ.get('VERCEL_ENV') == 'production':
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///:memory:')

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
