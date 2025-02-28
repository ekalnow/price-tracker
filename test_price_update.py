from app import app, db
from models import URL, Product, PriceHistory
from tasks import update_product_price
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_price_update():
    """Test updating the price of an existing product"""
    with app.app_context():
        # Get the first URL
        url = URL.query.first()
        if not url:
            logger.error("No URLs found in database")
            return
            
        logger.info(f"Testing price update for URL: {url.url}")
        
        # Get the product before update
        product = Product.query.get(url.product_id)
        if not product:
            logger.error(f"Product not found for URL ID {url.id}")
            return
            
        logger.info(f"Current product: {product.name}, Price: {product.current_price}")
        
        # Count price history entries before update
        history_count_before = PriceHistory.query.filter_by(product_id=product.id).count()
        logger.info(f"Price history entries before update: {history_count_before}")
        
        # Simulate a price change by manually updating the product price
        # This is just for testing - in real usage, the price would change on the website
        original_price = product.current_price
        simulated_price = original_price + 10  # Increase price by 10
        
        # Create a mock function to simulate different price extraction
        original_get_product_info = __import__('extractors').get_product_info
        
        def mock_get_product_info(url):
            # Get the real product info
            product_data = original_get_product_info(url)
            if product_data:
                # Modify the price
                product_data['price'] = simulated_price
                logger.info(f"Simulated price change: {original_price} -> {simulated_price}")
            return product_data
        
        # Replace the real function with our mock
        __import__('extractors').get_product_info = mock_get_product_info
        
        try:
            # Update the price
            success = update_product_price(url.id)
            
            if success:
                logger.info("Successfully updated product price")
                
                # Reload the product to get the latest data
                db.session.expire_all()
                product = Product.query.get(product.id)
                logger.info(f"Updated product: {product.name}, Price: {product.current_price}")
                
                # Count price history entries after update
                history_count_after = PriceHistory.query.filter_by(product_id=product.id).count()
                logger.info(f"Price history entries after update: {history_count_after}")
                
                # Verify price history was updated correctly
                if history_count_after > history_count_before:
                    logger.info("Price history was updated correctly")
                    
                    # Get the latest price history entry
                    latest_history = PriceHistory.query.filter_by(product_id=product.id).order_by(PriceHistory.timestamp.desc()).first()
                    logger.info(f"Latest price history: {latest_history.price}")
                else:
                    logger.warning("No new price history entry was created")
            else:
                logger.error("Failed to update product price")
        finally:
            # Restore the original function
            __import__('extractors').get_product_info = original_get_product_info

if __name__ == "__main__":
    test_price_update()
