from app import app, db
from models import URL, Product, PriceHistory, User
from extractors import detect_platform
from tasks import update_product_price
import logging
from werkzeug.security import generate_password_hash
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_add_url(url_to_test):
    """Test adding a URL and updating its price"""
    with app.app_context():
        # Create a test user if none exists
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
        
        # Check if URL already exists
        existing_url = URL.query.filter_by(url=url_to_test).first()
        if existing_url:
            logger.info(f"URL already exists: {url_to_test}")
            # Delete it to test adding it again
            db.session.delete(existing_url)
            db.session.commit()
            logger.info("Deleted existing URL")
        
        # Detect platform
        platform = detect_platform(url_to_test)
        if not platform:
            logger.error(f"Unsupported platform for URL: {url_to_test}")
            return False
        
        logger.info(f"Detected platform: {platform}")
        
        # Add URL to database
        new_url = URL(
            url=url_to_test,
            platform=platform,
            user=user
        )
        db.session.add(new_url)
        db.session.commit()
        logger.info(f"Added URL with ID {new_url.id}")
        
        # Now update the product info
        success = update_product_price(new_url.id)
        
        if success:
            logger.info("URL added successfully and product info retrieved")
            
            # Reload the URL to get the latest data
            db.session.expire_all()
            url = URL.query.get(new_url.id)
            
            # Check if product was created and linked
            if url.product_id:
                product = Product.query.get(url.product_id)
                logger.info(f"Product created: {product.name}, Price: {product.current_price}")
                
                # Check price history
                price_history = PriceHistory.query.filter_by(product_id=product.id).all()
                logger.info(f"Price history entries: {len(price_history)}")
                for ph in price_history:
                    logger.info(f"Price history: {ph.price} at {ph.timestamp}")
                
                return True
            else:
                logger.error("Product was not linked to URL")
                return False
        else:
            logger.error("Could not retrieve product info")
            return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python test_add_url.py <url>")
        sys.exit(1)
    
    url_to_test = sys.argv[1]
    test_add_url(url_to_test)
