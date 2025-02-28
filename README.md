# E-commerce Price Monitor

A web application that monitors competitor pricing across Salla and Zid e-commerce platforms in Saudi Arabia.

## Features

- Track product prices by adding product URLs
- Consolidated dashboard for all tracked products
- Price history tracking and visualization
- Support for Salla and Zid platforms
- Handles Arabic content properly
- Scheduled price checks

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```
   cp .env.example .env
   ```
   Then edit `.env` with your configuration

4. Initialize the database:
   ```
   flask db init
   flask db migrate
   flask db upgrade
   ```

5. Run the application:
   ```
   flask run
   ```

## Usage

1. Add product URLs to track through the dashboard
2. View current prices and price history
3. Configure price check schedules
4. Export data as needed

## Technical Information

- Built with Flask
- Uses SQLAlchemy for database operations
- Async processing for batch URL processing
- Implements Arabic numeral conversion
- Handles rate limiting and proxy rotation
