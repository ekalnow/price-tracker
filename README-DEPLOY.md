# Deployment Guide for E-commerce Price Monitor

This guide provides instructions for deploying the E-commerce Price Monitor application to various platforms.

## Prerequisites

- Python 3.13.0 or compatible version
- PostgreSQL database (or SQLite for local development)
- All dependencies listed in `requirements.txt`

## Environment Variables

The following environment variables need to be set:

- `SECRET_KEY`: A secure random string for session security
- `DATABASE_URL`: Connection string for PostgreSQL (for production)
- `DATABASE_URI`: Connection string for local SQLite (for development)
- `FLASK_ENV`: Set to `production` for production deployment
- `LOG_LEVEL`: Set to `INFO` or `DEBUG` as needed
- `SCHEDULER_INTERVAL_MINUTES`: How often to update prices (default: 1440 minutes/daily)
- `API_KEY`: A secure API key for authenticating scheduled updates

## Deployment Options

### Option 1: Heroku

1. Create a Heroku account and install the Heroku CLI
2. Create a new Heroku app:
   ```
   heroku create your-app-name
   ```
3. Add a PostgreSQL database:
   ```
   heroku addons:create heroku-postgresql:hobby-dev
   ```
4. Set environment variables:
   ```
   heroku config:set SECRET_KEY=your-secure-key
   heroku config:set FLASK_ENV=production
   heroku config:set LOG_LEVEL=INFO
   heroku config:set API_KEY=your-secure-api-key
   heroku config:set SCHEDULER_INTERVAL_MINUTES=1440
   ```
5. Deploy your application:
   ```
   git push heroku main
   ```
6. Initialize the database:
   ```
   heroku run python -c "from app import app; from models import db; app.app_context().push(); db.create_all()"
   ```
7. Set up the Heroku Scheduler add-on for regular price updates

### Option 2: Render

1. Create a Render account and connect your GitHub repository
2. Create a new Web Service
3. Select your repository and use the following settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn wsgi:app`
4. Add environment variables in the Render dashboard
5. Set up a Cron Job for regular price updates

### Option 3: PythonAnywhere

1. Create a PythonAnywhere account
2. Create a new web app with Flask
3. Set up a virtual environment and install dependencies
4. Configure the WSGI file to point to your app
5. Set up environment variables in the `.env` file
6. Use the PythonAnywhere task scheduler for regular price updates

### Option 4: DigitalOcean App Platform

1. Create a DigitalOcean account
2. Create a new App
3. Connect your GitHub repository
4. Configure the app with the following settings:
   - Build Command: None (or `pip install -r requirements.txt` if needed)
   - Run Command: `gunicorn wsgi:app`
5. Add environment variables in the App settings
6. Set up a DigitalOcean function or cron job for regular price updates

## Testing Your Deployment

After deploying, visit your application URL to verify that it's working correctly. You should be able to:

1. Register a new user account
2. Log in with the new account
3. Add product URLs to track
4. View price history and charts

## Troubleshooting

If you encounter issues:

1. Check the application logs for error messages
2. Verify that all environment variables are set correctly
3. Ensure the database is properly initialized
4. Check that the scheduler is running for price updates
