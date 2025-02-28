from app import app, db
from models import URL, Product, PriceHistory, User
from extractors import detect_platform, get_product_info
from tasks import update_product_price
import logging
from werkzeug.security import generate_password_hash
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_full_workflow(url_to_test):
    """Test the full workflow: add URL, create product, update price"""
    with app.app_context():
        # Step 1: Create a test user if none exists
        user = User.query.filter_by(email='test@example.com').first()
        if not user:
            user = User(
                email='test@example.com',
                password_hash=generate_password_hash('password'),
                name='Test User'
            )
            db.session.add(user)
            db.session.commit()
            logger.info(f"Created test user: {user.email}")
        
        # Step 2: Check if URL already exists and delete it
        existing_url = URL.query.filter_by(url=url_to_test).first()
        if existing_url:
            logger.info(f"URL already exists: {url_to_test}")
            # Delete it to test adding it again
            db.session.delete(existing_url)
            db.session.commit()
            logger.info("Deleted existing URL")
        
        # Step 3: Detect platform
        platform = detect_platform(url_to_test)
        if not platform:
            logger.error(f"Unsupported platform for URL: {url_to_test}")
            return False
        
        logger.info(f"Detected platform: {platform}")
        
        # Step 4: Add URL to database
        new_url = URL(
            url=url_to_test,
            platform=platform,
            user=user
        )
        db.session.add(new_url)
        db.session.commit()
        logger.info(f"Added URL with ID {new_url.id}")
        
        # Step 5: Update the product info for the first time
        logger.info("STEP 1: Initial product creation")
        success = update_product_price(new_url.id)
        
        if not success:
            logger.error("Could not retrieve product info")
            return False
            
        # Reload the URL to get the latest data
        db.session.expire_all()
        url = URL.query.get(new_url.id)
        
        # Check if product was created and linked
        if not url.product_id:
            logger.error("Product was not linked to URL")
            return False
            
        product = Product.query.get(url.product_id)
        logger.info(f"Product created: {product.name}, Price: {product.current_price}")
        
        # Check price history
        price_history = PriceHistory.query.filter_by(product_id=product.id).all()
        logger.info(f"Price history entries: {len(price_history)}")
        for ph in price_history:
            logger.info(f"Price history: {ph.price} at {ph.timestamp}")
        
        # Step 6: Simulate a price change
        logger.info("\nSTEP 2: Simulating price change")
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
            # Step 7: Update the price again
            logger.info("STEP 3: Updating product price")
            success = update_product_price(url.id)
            
            if not success:
                logger.error("Failed to update product price")
                return False
                
            # Reload the product to get the latest data
            db.session.expire_all()
            product = Product.query.get(product.id)
            logger.info(f"Updated product: {product.name}, Price: {product.current_price}")
            
            # Check price history again
            price_history = PriceHistory.query.filter_by(product_id=product.id).all()
            logger.info(f"Price history entries after update: {len(price_history)}")
            for ph in price_history:
                logger.info(f"Price history: {ph.price} at {ph.timestamp}")
            
            return True
        finally:
            # Restore the original function
            __import__('extractors').get_product_info = original_get_product_info

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python test_full_workflow.py <url>")
        sys.exit(1)
    
    url_to_test = sys.argv[1]
    test_full_workflow(url_to_test)
