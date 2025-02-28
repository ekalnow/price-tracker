"""
Test file for Vercel deployment.
This file can be run locally to simulate how the app will behave on Vercel.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up Vercel environment simulation
os.environ['VERCEL_ENV'] = 'development'
os.environ['SERVERLESS'] = 'true'

# Import the app (which will initialize with serverless settings)
from app import app

if __name__ == "__main__":
    print("✅ Running in Vercel simulation mode")
    print(f"✅ Scheduler active: {app.apscheduler is not None}")
    print(f"✅ Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("✅ Starting Flask server for testing...")
    app.run(host="0.0.0.0", port=8000, debug=True)
