"""
WSGI entry point for the E-commerce Price Monitor application.
This file serves as the entry point for traditional Flask deployments.
"""

from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
