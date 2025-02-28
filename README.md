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

## Scraping Functionality

The scraper supports extracting product information from any website built with Salla or Zid platforms, regardless of the domain. The functionality includes:

- **Robust Platform Detection**: The system can identify Salla and Zid powered websites based on page content rather than just domain names.
- **Enhanced Extraction**: Multiple extraction methods are used to reliably get product information:
  - Meta tags
  - JSON-LD structured data
  - HTML elements
- **Fallback Mechanisms**: If one extraction method fails, the system automatically tries alternatives.
- **Product-Specific URLs**: For best results, always use product detail page URLs rather than homepage or category URLs. This ensures accurate price tracking and product information extraction.

### Testing the Scraper

You can test the scraper with any product URL using the included test script:

```bash
python test_extractor.py <product_url>
```

For example:
```bash
python test_extractor.py https://sauditissues.com/products/saudi-tissues-500-sheets
```

### Troubleshooting

If you encounter issues with product tracking:

1. **URL Validity**: Ensure you're using a direct product URL, not a category or homepage URL
2. **Platform Support**: Verify the store is built with either Salla or Zid
3. **Product Creation**: If you see "Product not found" errors, try removing and re-adding the URL
4. **Database Relationships**: The system automatically creates product records when URLs are added

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

5. Run the application:
   ```
   flask run
   ```
