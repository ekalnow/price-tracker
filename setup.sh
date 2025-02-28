#!/bin/bash
# Setup script for E-commerce Price Monitor

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Don't forget to update your .env file with appropriate values!"
fi

# Initialize the database
echo "Initializing database..."
python run.py --init-db

# Instructions
echo "Setup complete!"
echo ""
echo "To start the application, run:"
echo "  source venv/bin/activate  # If not already activated"
echo "  python run.py"
echo ""
echo "To create an admin user:"
echo "  python run.py --create-admin --admin-username=admin --admin-email=admin@example.com --admin-password=yourpassword"
echo ""
