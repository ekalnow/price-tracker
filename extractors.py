import requests
import json
import re
import logging
from bs4 import BeautifulSoup
import random
import time
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# User agent rotation for request headers
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
]

# Proxy configuration
USE_PROXIES = os.getenv('USE_PROXIES', 'False').lower() == 'true'
PROXY_LIST = os.getenv('PROXY_LIST', '').split(',') if os.getenv('PROXY_LIST') else []

def get_random_user_agent():
    """Return a random user agent from the list"""
    return random.choice(USER_AGENTS)

def get_random_proxy():
    """Return a random proxy from the list if enabled"""
    if USE_PROXIES and PROXY_LIST:
        return random.choice(PROXY_LIST)
    return None

def detect_platform(url):
    """Detect the e-commerce platform based on the URL"""
    domain = urlparse(url).netloc.lower()
    
    if 'salla.sa' in domain or 'salla.com' in domain:
        return 'salla'
    elif 'zid.store' in domain or 'zid.sa' in domain:
        return 'zid'
    else:
        return None

def arabic_to_english_numerals(text):
    """Convert Arabic numerals to English numerals"""
    if not text:
        return text
        
    arabic_numerals = '٠١٢٣٤٥٦٧٨٩'
    english_numerals = '0123456789'
    
    translation_table = str.maketrans(arabic_numerals, english_numerals)
    return text.translate(translation_table)

def clean_price(price_str):
    """Clean price string and convert to float"""
    if not price_str:
        return None
        
    # Convert Arabic numerals to English
    price_str = arabic_to_english_numerals(price_str)
    
    # Remove currency symbols and non-numeric characters except decimal point
    price_str = re.sub(r'[^\d.,]', '', price_str)
    
    # Replace comma with dot for decimal point if needed
    price_str = price_str.replace(',', '.')
    
    try:
        return float(price_str)
    except ValueError:
        logger.error(f"Could not convert price: {price_str}")
        return None

class BaseExtractor:
    """Base class for price extractors"""
    
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
    def get_product_data(self, url):
        """Get product data from URL - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement this method")
        
    def get_page_content(self, url):
        """Get page content with retry mechanism"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                proxy = get_random_proxy()
                proxies = {'http': proxy, 'https': proxy} if proxy else None
                
                # Update user agent for each request
                self.headers['User-Agent'] = get_random_user_agent()
                
                response = self.session.get(
                    url, 
                    headers=self.headers, 
                    proxies=proxies,
                    timeout=10
                )
                
                if response.status_code == 200:
                    return response.text
                    
                logger.warning(f"Request failed with status code {response.status_code}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {e}")
            
            # Wait before retrying
            time.sleep(retry_delay * (attempt + 1))
        
        logger.error(f"Failed to retrieve page content after {max_retries} attempts")
        return None

class SallaExtractor(BaseExtractor):
    """Extractor for Salla platform"""
    
    def get_product_data(self, url):
        """Extract product data from Salla product page"""
        page_content = self.get_page_content(url)
        if not page_content:
            return None
            
        soup = BeautifulSoup(page_content, 'lxml')
        product_data = {}
        
        # Method 1: Extract from meta tags
        try:
            product_data['name'] = soup.find('meta', property='og:title')['content']
        except (TypeError, KeyError):
            product_data['name'] = None
            
        try:
            # Try to get price from meta tags
            price = None
            price_meta = soup.find('meta', property='product:price:amount')
            sale_price_meta = soup.find('meta', property='product:sale_price:amount')
            
            if sale_price_meta and sale_price_meta.get('content'):
                price = clean_price(sale_price_meta['content'])
            elif price_meta and price_meta.get('content'):
                price = clean_price(price_meta['content'])
                
            product_data['price'] = price
        except (TypeError, KeyError):
            product_data['price'] = None
            
        # Method 2: Extract from JSON-LD
        if not product_data['price']:
            try:
                json_ld = soup.find('script', type='application/ld+json')
                if json_ld:
                    json_data = json.loads(json_ld.string)
                    
                    if isinstance(json_data, list):
                        json_data = next((item for item in json_data if item.get('@type') == 'Product'), None)
                    
                    if json_data and json_data.get('@type') == 'Product':
                        if not product_data['name'] and json_data.get('name'):
                            product_data['name'] = json_data['name']
                            
                        if json_data.get('offers'):
                            offers = json_data['offers']
                            if isinstance(offers, list):
                                offers = offers[0]
                                
                            if offers.get('price'):
                                product_data['price'] = clean_price(str(offers['price']))
            except Exception as e:
                logger.error(f"Error extracting JSON-LD data: {e}")
        
        # Method 3: Extract from HTML elements
        if not product_data['price']:
            try:
                # Common price selectors in Salla templates
                price_selectors = [
                    '.product-price', 
                    '.price', 
                    '.product-details__price',
                    '[data-price]'
                ]
                
                for selector in price_selectors:
                    price_element = soup.select_one(selector)
                    if price_element:
                        price_text = price_element.get_text().strip()
                        product_data['price'] = clean_price(price_text)
                        break
            except Exception as e:
                logger.error(f"Error extracting price from HTML: {e}")
        
        # Get product image
        try:
            product_data['image_url'] = soup.find('meta', property='og:image')['content']
        except (TypeError, KeyError):
            product_data['image_url'] = None
            
        # Get currency
        try:
            currency_meta = soup.find('meta', property='product:price:currency')
            if currency_meta:
                product_data['currency'] = currency_meta['content']
            else:
                product_data['currency'] = 'SAR'  # Default currency
        except (TypeError, KeyError):
            product_data['currency'] = 'SAR'
            
        # Get availability
        try:
            availability_meta = soup.find('meta', property='product:availability')
            if availability_meta:
                product_data['availability'] = availability_meta['content']
            else:
                product_data['availability'] = 'in stock'  # Default
        except (TypeError, KeyError):
            product_data['availability'] = 'in stock'
            
        return product_data

class ZidExtractor(BaseExtractor):
    """Extractor for Zid platform"""
    
    def get_product_data(self, url):
        """Extract product data from Zid product page"""
        page_content = self.get_page_content(url)
        if not page_content:
            return None
            
        soup = BeautifulSoup(page_content, 'lxml')
        product_data = {}
        
        # Method 1: Extract from JSON-LD (schema.org data)
        try:
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld:
                json_data = json.loads(json_ld.string)
                
                if isinstance(json_data, list):
                    json_data = next((item for item in json_data if item.get('@type') == 'Product'), None)
                
                if json_data and json_data.get('@type') == 'Product':
                    product_data['name'] = json_data.get('name')
                    
                    if json_data.get('offers'):
                        offers = json_data['offers']
                        if isinstance(offers, list):
                            offers = offers[0]
                            
                        if offers.get('price'):
                            product_data['price'] = clean_price(str(offers['price']))
                        
                        if offers.get('priceCurrency'):
                            product_data['currency'] = offers['priceCurrency']
                            
                        if offers.get('availability'):
                            product_data['availability'] = offers['availability'].split('/')[-1]
                    
                    if json_data.get('image'):
                        if isinstance(json_data['image'], list):
                            product_data['image_url'] = json_data['image'][0]
                        else:
                            product_data['image_url'] = json_data['image']
        except Exception as e:
            logger.error(f"Error extracting JSON-LD data: {e}")
            
        # Method 2: Extract from meta tags
        if not product_data.get('name'):
            try:
                product_data['name'] = soup.find('meta', property='og:title')['content']
            except (TypeError, KeyError):
                pass
                
        if not product_data.get('image_url'):
            try:
                product_data['image_url'] = soup.find('meta', property='og:image')['content']
            except (TypeError, KeyError):
                pass
        
        # Method 3: Extract from HTML elements
        if not product_data.get('price'):
            try:
                # Common price selectors in Zid templates
                price_selectors = [
                    '.product-details-price', 
                    '.product__price', 
                    '.price-box',
                    '[data-product-price]'
                ]
                
                for selector in price_selectors:
                    price_element = soup.select_one(selector)
                    if price_element:
                        price_text = price_element.get_text().strip()
                        product_data['price'] = clean_price(price_text)
                        break
            except Exception as e:
                logger.error(f"Error extracting price from HTML: {e}")
                
        # Set defaults if not found
        if not product_data.get('currency'):
            product_data['currency'] = 'SAR'
            
        if not product_data.get('availability'):
            product_data['availability'] = 'in stock'
            
        return product_data

# Function to extract data for multiple URLs (synchronous version)
def batch_extract_product_data(urls, concurrency=5):
    """Extract product data for multiple URLs (synchronous version)"""
    results = {}
    for url in urls:
        try:
            results[url] = get_product_info(url)
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Error extracting data from {url}: {str(e)}")
            results[url] = None
    return results

# Function to be used by external code
def get_product_info(url):
    """Get product information for a single URL"""
    platform = detect_platform(url)
    
    if not platform:
        logger.error(f"Unsupported platform for URL: {url}")
        return None
        
    if platform == 'salla':
        extractor = SallaExtractor()
    elif platform == 'zid':
        extractor = ZidExtractor()
    else:
        return None
        
    product_data = extractor.get_product_data(url)
    
    if product_data:
        product_data['url'] = url
        product_data['platform'] = platform
        
    return product_data
