import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the app
from app import app, db
from models import URL, Product, PriceHistory, User
from tasks import update_product_price

def test_add_url_and_update_price(url_to_test):
    """Test adding a URL and updating its price"""
    from extractors import detect_platform
    
    with app.app_context():
        # Check if URL already exists
        existing_url = URL.query.filter_by(url=url_to_test).first()
        if existing_url:
            logger.info(f"URL already exists: {url_to_test}")
            # Delete it for testing
            if existing_url.product:
                # Delete price history
                PriceHistory.query.filter_by(product_id=existing_url.product.id).delete()
                # Delete product
                db.session.delete(existing_url.product)
            db.session.delete(existing_url)
            db.session.commit()
            logger.info("Deleted existing URL and product for testing")
        
        # Get or create test user
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            test_user = User(username='testuser', email='test@example.com')
            test_user.set_password('password')
            db.session.add(test_user)
            db.session.commit()
            logger.info("Created test user")
        
        # Detect platform
        platform = detect_platform(url_to_test)
        if not platform:
            logger.error(f"Unsupported platform for URL: {url_to_test}")
            return
        
        logger.info(f"Detected platform: {platform}")
        
        # Add URL to database
        new_url = URL(
            url=url_to_test,
            platform=platform,
            user=test_user
        )
        db.session.add(new_url)
        db.session.commit()
        logger.info(f"Added URL with ID {new_url.id}")
        
        # Now update the product info
        success = update_product_price(new_url.id)
        
        if success:
            logger.info("Successfully updated product price")
            
            # Reload the URL from the database to get fresh data
            db.session.expire_all()  # Clear the session cache
            url = URL.query.filter_by(id=new_url.id).first()
            
            # Check if any products exist in the database
            products = Product.query.all()
            logger.info(f"Total products in database: {len(products)}")
            for p in products:
                logger.info(f"Product in DB: ID={p.id}, Name={p.name}, Price={p.current_price}")
            
            # Check if price history exists
            history = PriceHistory.query.all()
            logger.info(f"Total price history entries: {len(history)}")
            for h in history:
                logger.info(f"Price history: Product ID={h.product_id}, Price={h.price}")
            
            logger.info(f"URL product_id: {url.product_id}")
            
            if url.product_id:
                logger.info(f"URL has product_id set to {url.product_id}")
                if url.product:
                    logger.info(f"Product relationship working: {url.product.name}")
                else:
                    logger.error("Product relationship not working despite product_id being set")
            else:
                logger.error("URL product_id is not set")
        else:
            logger.error("Failed to update product price")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url_to_test = sys.argv[1]
    else:
        url_to_test = "https://sauditissues.com/products/saudi-tissues-500-sheets"
    
    logger.info(f"Testing URL: {url_to_test}")
    test_add_url_and_update_price(url_to_test)
