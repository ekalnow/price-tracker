import logging
import asyncio
from datetime import datetime
import time
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
                db.session.commit()
                return False
            
            # If the URL doesn't have a product associated, create a new one
            if not url_obj.product:
                from models import Product
                new_product = Product(
                    name=product_data.get('name', 'Unknown Product'),
                    current_price=product_data['price'],
                    currency=product_data.get('currency', 'SAR'),
                    image_url=product_data.get('image_url'),
                    availability=product_data.get('availability')
                )
                db.session.add(new_product)
                url_obj.product = new_product
            else:
                # If product exists, update its details
                url_obj.product.name = product_data.get('name', url_obj.product.name)
                url_obj.product.current_price = product_data['price']
                url_obj.product.image_url = product_data.get('image_url', url_obj.product.image_url)
                url_obj.product.availability = product_data.get('availability', url_obj.product.availability)
            
            # Add price history entry
            price_history = PriceHistory(
                product=url_obj.product,
                price=product_data['price'],
                timestamp=datetime.utcnow()
            )
            db.session.add(price_history)
            
            # Update URL metadata
            url_obj.last_checked = datetime.utcnow()
            url_obj.is_valid = True
            url_obj.platform = product_data.get('platform', url_obj.platform)
            
            db.session.commit()
            logger.info(f"Updated price for {url_obj.url}: {product_data['price']} {product_data.get('currency', 'SAR')}")
            return True
            
    except Exception as e:
        logger.error(f"Error updating product price: {e}")
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
        
        # Check if we're in a serverless environment
        is_serverless = bool(app.config.get('SERVERLESS', False)) or \
                        bool(app.config.get('VERCEL_ENV', False)) or \
                        'VERCEL' in app.config
        
        # In serverless environments, process synchronously to avoid timing out
        if is_serverless:
            logger.info("Running in serverless mode - processing URLs synchronously")
            for url_id in url_ids:
                try:
                    success = update_product_price(url_id)
                    if success:
                        updated_count += 1
                except Exception as e:
                    logger.error(f"Error updating URL ID {url_id}: {str(e)}")
                    continue
        else:
            # In regular environments, use async processing
            try:
                # Run the async update
                asyncio.run(async_update_prices(app, url_ids))
                
                # Count how many were updated
                updated_count = len(url_ids)
            except Exception as e:
                logger.error(f"Error in async update: {str(e)}")
                logger.error(traceback.format_exc())
        
    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Price update completed in {duration:.2f} seconds. Updated {updated_count} products.")
    
    return updated_count

async def async_update_prices(app, url_ids=None):
    """Update prices for URLs asynchronously"""
    from models import db, URL, Product, PriceHistory
    from extractors import batch_extract_product_data
    
    try:
        with app.app_context():
            if url_ids:
                urls = URL.query.filter(URL.id.in_(url_ids)).filter_by(is_valid=True).all()
            else:
                urls = URL.query.filter_by(is_valid=True).all()
                
            if not urls:
                logger.info("No valid URLs to update")
                return
                
            logger.info(f"Starting async price update for {len(urls)} URLs")
            start_time = time.time()
            
            # Extract URLs as strings
            url_strings = [url.url for url in urls]
            
            # Create a dictionary mapping URL strings to URL objects for fast lookup
            url_map = {url.url: url for url in urls}
            
            # Perform batch extraction
            results = await batch_extract_product_data(url_strings)
            
            # Update database with results
            for url_string, product_data in results.items():
                url_obj = url_map.get(url_string)
                
                if not url_obj:
                    continue
                    
                if not product_data or 'price' not in product_data or product_data['price'] is None:
                    url_obj.is_valid = False
                    continue
                
                # If URL doesn't have a product associated, create a new one
                if not url_obj.product:
                    new_product = Product(
                        name=product_data.get('name', 'Unknown Product'),
                        current_price=product_data['price'],
                        currency=product_data.get('currency', 'SAR'),
                        image_url=product_data.get('image_url'),
                        availability=product_data.get('availability')
                    )
                    db.session.add(new_product)
                    url_obj.product = new_product
                else:
                    # If product exists, update its details
                    url_obj.product.name = product_data.get('name', url_obj.product.name)
                    url_obj.product.current_price = product_data['price']
                    url_obj.product.image_url = product_data.get('image_url', url_obj.product.image_url)
                    url_obj.product.availability = product_data.get('availability', url_obj.product.availability)
                
                # Add price history entry
                price_history = PriceHistory(
                    product=url_obj.product,
                    price=product_data['price'],
                    timestamp=datetime.utcnow()
                )
                db.session.add(price_history)
                
                # Update URL metadata
                url_obj.last_checked = datetime.utcnow()
                url_obj.is_valid = True
                url_obj.platform = product_data.get('platform', url_obj.platform)
            
            # Commit all changes
            db.session.commit()
            
            elapsed_time = time.time() - start_time
            success_count = len(results)
            logger.info(f"Completed async price update. Success: {success_count}/{len(urls)}. Time elapsed: {elapsed_time:.2f}s")
            
    except Exception as e:
        logger.error(f"Error in async_update_prices: {e}")
        logger.error(traceback.format_exc())
