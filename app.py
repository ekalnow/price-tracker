import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_required, current_user
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import logging
from datetime import datetime
import pytz

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

# Check if we're in a production environment (Render, Heroku, etc.)
is_production = os.environ.get('RENDER') is not None or os.environ.get('HEROKU_APP_ID') is not None or os.environ.get('VERCEL_ENV') is not None or os.environ.get('SERVERLESS') is not None or os.environ.get('FLASK_ENV') == 'production'

# Configure database URI based on environment
if is_production:
    # In production environment, use DATABASE_URL (for PostgreSQL or other external DB)
    # Note: Render automatically sets DATABASE_URL
    db_url = os.getenv('DATABASE_URL')
    if db_url and db_url.startswith('postgres://'):
        # Render uses postgres:// but SQLAlchemy requires postgresql://
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///:memory:')
    logger.info(f"Running in production mode with database: {app.config['SQLALCHEMY_DATABASE_URI']}")
else:
    # In development environment, use DATABASE_URI (local SQLite)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///price_monitor.db')
    logger.info(f"Running in development mode with database: {app.config['SQLALCHEMY_DATABASE_URI']}")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import models and database (will be created in a separate file)
from models import db, User, Product, PriceHistory, URL
from forms import LoginForm, RegisterForm, URLForm, URLBatchForm
import extractors
from tasks import update_all_prices

# Initialize database
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize scheduler only if not in a production environment
if not is_production:
    # Initialize scheduler
    scheduler = BackgroundScheduler()
    scheduler.start()

    # Add to app context for easier access in routes
    app.apscheduler = scheduler

    # Schedule the price update task
    interval_minutes = int(os.getenv('SCHEDULER_INTERVAL_MINUTES', 1440))  # Default: daily
    scheduler.add_job(
        update_all_prices,
        'interval',
        minutes=interval_minutes,
        args=[app],
        id='price_update_job'
    )
    logger.info(f"Scheduler initialized with interval of {interval_minutes} minutes")
else:
    logger.info("Running in production environment, scheduler disabled")
    # Create a dummy scheduler attribute for API compatibility
    app.apscheduler = None

# Register context processors
from context_processors import register_context_processors
register_context_processors(app)

# Import routes after initializing app to avoid circular imports
from routes import register_routes
register_routes(app)

# Create database tables (using with app.app_context instead of before_first_request)
with app.app_context():
    db.create_all()
    logger.info("Database tables created/verified")

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"Internal server error: {str(e)}")
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

if __name__ == '__main__':
    app.run(debug=True)
