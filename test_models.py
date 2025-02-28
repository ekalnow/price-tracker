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
from models import URL, Product, User

def test_model_relationships():
    """Test the relationship between URL and Product models"""
    with app.app_context():
        # Clean up existing data
        URL.query.delete()
        Product.query.delete()
        db.session.commit()
        
        # Create a test user
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            test_user = User(username='testuser', email='test@example.com')
            test_user.set_password('password')
            db.session.add(test_user)
            db.session.commit()
            logger.info("Created test user")
        
        # Create a product
        product = Product(
            name='Test Product',
            current_price=100.0,
            currency='SAR',
            description='Test description'
        )
        db.session.add(product)
        db.session.commit()
        logger.info(f"Created product with ID {product.id}")
        
        # Create a URL and link it to the product
        url = URL(
            url='https://example.com/test',
            platform='salla',
            user=test_user,
            product_id=product.id
        )
        db.session.add(url)
        db.session.commit()
        logger.info(f"Created URL with ID {url.id} and product_id {url.product_id}")
        
        # Reload the URL from the database
        url = URL.query.get(url.id)
        logger.info(f"Reloaded URL product_id: {url.product_id}")
        
        # Test the relationship
        if url.product:
            logger.info(f"URL.product relationship works: {url.product.name}")
        else:
            logger.error("URL.product relationship does not work")
            
        # Test the reverse relationship
        if product.urls:
            logger.info(f"Product.urls relationship works: {product.urls[0].url}")
        else:
            logger.error("Product.urls relationship does not work")
            
        # Clean up
        URL.query.delete()
        Product.query.delete()
        db.session.commit()
        logger.info("Cleaned up test data")

if __name__ == "__main__":
    test_model_relationships()
