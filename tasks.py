import logging
import time
from datetime import datetime
from flask import current_app
import traceback

# This needs to be imported within functions to avoid circular imports
# from models import db, URL, Product, PriceHistory
# from extractors import get_product_info, batch_extract_product_data

logger = logging.getLogger(__name__)

def update_product_price(url_id):
    """Update price for a single product URL"""
    from models import db, URL, PriceHistory
    from extractors import get_product_info
    
    try:
        # Create app context
        with current_app.app_context():
            url_obj = URL.query.get(url_id)
            
            if not url_obj:
                logger.error(f"URL with ID {url_id} not found")
                return False
                
            product_data = get_product_info(url_obj.url)
            
            if not product_data or 'price' not in product_data or product_data['price'] is None:
                logger.error(f"Failed to extract price for URL: {url_obj.url}")
                url_obj.is_valid = False
                url_obj.last_checked = datetime.utcnow()
                db.session.commit()
                return False
                
            # Get or create product
            product = url_obj.product
            
            if not product:
                logger.error(f"Product not found for URL ID {url_id}")
                return False
                
            # Check if price has changed
            old_price = product.current_price
            new_price = product_data['price']
            
            if old_price != new_price:
                # Create price history entry
                price_history = PriceHistory(
                    product_id=product.id,
                    price=new_price
                )
                db.session.add(price_history)
                
                # Update product
                product.current_price = new_price
                product.updated_at = datetime.utcnow()
                
                # If we have additional data, update it
                if 'name' in product_data and product_data['name']:
                    product.name = product_data['name']
                if 'image_url' in product_data and product_data['image_url']:
                    product.image_url = product_data['image_url']
                if 'description' in product_data and product_data['description']:
                    product.description = product_data['description']
                if 'availability' in product_data and product_data['availability']:
                    product.availability = product_data['availability']
                
                logger.info(f"Price updated for {product.name}: {old_price} -> {new_price}")
            
            # Update last checked timestamp
            url_obj.last_checked = datetime.utcnow()
            db.session.commit()
            
            return True
            
    except Exception as e:
        logger.error(f"Error updating product price for URL ID {url_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def update_all_prices(app):
    """Update prices for all valid URLs"""
    from models import db, URL, Product, PriceHistory
    
    logger.info("Starting price update for all products")
    start_time = time.time()
    updated_count = 0
    
    # Use app context to ensure database operations work correctly
    with app.app_context():
        # Get all valid URLs
        valid_urls = URL.query.filter_by(is_valid=True).all()
        
        if not valid_urls:
            logger.info("No valid URLs found to update")
            return 0
            
        logger.info(f"Found {len(valid_urls)} valid URLs to update")
        
        # Create a list of URL IDs
        url_ids = [url.id for url in valid_urls]
        
        # Check if we're in a production environment
        is_production = bool(app.config.get('SERVERLESS', False)) or \
                      bool(app.config.get('VERCEL_ENV', False)) or \
                      bool(app.config.get('RENDER', False)) or \
                      bool(app.config.get('HEROKU_APP_ID', False)) or \
                      app.config.get('FLASK_ENV') == 'production'
        
        # Process URLs synchronously
        logger.info("Processing URLs synchronously")
        for url_id in url_ids:
            try:
                success = update_product_price(url_id)
                if success:
                    updated_count += 1
                # Small delay to avoid overloading servers
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error updating URL ID {url_id}: {str(e)}")
                continue
        
    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Price update completed in {duration:.2f} seconds. Updated {updated_count} products.")
    
    return updated_count

# For standalone execution (e.g., from a cron job)
if __name__ == "__main__":
    import os
    import sys
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Configure logging
    logging_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))
    logging.basicConfig(
        level=logging_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Try to import the serverless app first (for production environments)
        try:
            from app_serverless import app
            logger.info("Using serverless app for scheduled task")
        except ImportError:
            # Fall back to regular app
            from app import app
            logger.info("Using regular app for scheduled task")
        
        # Run the update
        updated_count = update_all_prices(app)
        logger.info(f"Scheduled task completed: Updated {updated_count} products")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error in scheduled task: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)
