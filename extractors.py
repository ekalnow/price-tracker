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

def get_page_content(url):
    """Get page content with retry mechanism"""
    max_retries = 3
    retry_delay = 2
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    for attempt in range(max_retries):
        try:
            proxy = get_random_proxy()
            proxies = {'http': proxy, 'https': proxy} if proxy else None
            
            response = requests.get(
                url, 
                headers=headers, 
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

def detect_platform(url, html_content=None):
    """
    Detect the e-commerce platform based on the URL and page content.
    This improved version focuses more on page content indicators than URL patterns.
    """
    # If HTML content wasn't provided, try to fetch it
    if not html_content:
        html_content = get_page_content(url)
        if not html_content:
            logger.error(f"Could not fetch content from URL: {url}")
            return None
    
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html_content, 'lxml')
    
    # Check for Salla platform indicators in the page content
    salla_indicators = [
        soup.find('meta', property='product:retailer_item_id'),
        soup.find('meta', property='product:price:currency', content='SAR'),
        soup.find('link', {'rel': 'canonical', 'href': lambda x: x and 'salla.sa' in x}),
        soup.find('link', href=lambda x: x and 'salla.network' in x),
        soup.find('script', src=lambda x: x and 'salla.network' in x),
        soup.find('link', href=lambda x: x and 'assets.salla' in x),
        'window.Salla' in html_content,
        'salla.sa' in html_content,
        'salla.com' in html_content
    ]
    
    if any(salla_indicators):
        logger.info(f"Detected Salla platform for URL: {url}")
        return 'salla'
    
    # Check for Zid platform indicators in the page content
    zid_indicators = [
        soup.find('script', string=lambda t: t and ('zid.store' in str(t) or 'application/ld+json' in str(t))),
        'zid.store' in html_content,
        'zid.sa' in html_content,
        'zidapi' in html_content,
        'window.Zid' in html_content
    ]
    
    if any(zid_indicators):
        logger.info(f"Detected Zid platform for URL: {url}")
        return 'zid'
    
    # If all checks fail, try fallback to domain-based detection
    domain = urlparse(url).netloc.lower()
    if 'salla.sa' in domain or 'salla.com' in domain:
        logger.info(f"Detected Salla platform based on domain for URL: {url}")
        return 'salla'
    elif 'zid.store' in domain or 'zid.sa' in domain:
        logger.info(f"Detected Zid platform based on domain for URL: {url}")
        return 'zid'
    
    # If all checks fail, return None
    logger.warning(f"Could not determine platform for URL: {url}")
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
            # Get product name
            meta_title = soup.find('meta', property='og:title')
            if meta_title and meta_title.get('content'):
                product_data['name'] = meta_title['content'].strip()
            
            # Try to get price from meta tags
            price = None
            price_meta = soup.find('meta', property='product:price:amount')
            sale_price_meta = soup.find('meta', property='product:sale_price:amount')
            pretax_price_meta = soup.find('meta', property='product:pretax_price:amount')
            
            if sale_price_meta and sale_price_meta.get('content'):
                price = clean_price(sale_price_meta['content'])
            elif price_meta and price_meta.get('content'):
                price = clean_price(price_meta['content'])
            elif pretax_price_meta and pretax_price_meta.get('content'):
                # Add VAT estimation if only pretax price is available
                pretax_price = clean_price(pretax_price_meta['content'])
                if pretax_price:
                    price = pretax_price * 1.15  # 15% VAT
                
            if price:
                product_data['price'] = price
                
            # Get store name
            store_meta = soup.find('meta', property='og:site_name')
            if store_meta and store_meta.get('content'):
                product_data['store_name'] = store_meta['content']
                
            # Get product description
            desc_meta = soup.find('meta', property='og:description')
            if desc_meta and desc_meta.get('content'):
                product_data['description'] = desc_meta['content']
                
            # Get SKU/Product ID
            sku_meta = soup.find('meta', property='product:retailer_item_id')
            if sku_meta and sku_meta.get('content'):
                product_data['sku'] = sku_meta['content']
                
            # Get brand
            brand_meta = soup.find('meta', property='product:brand')
            if brand_meta and brand_meta.get('content'):
                product_data['brand'] = brand_meta['content']
                
            # Get category
            category_meta = soup.find('meta', property='product:category')
            if category_meta and category_meta.get('content'):
                product_data['category'] = category_meta['content']
        except (TypeError, KeyError, Exception) as e:
            logger.error(f"Error extracting metadata: {e}")
            
        # Method 2: Extract from JSON-LD
        if not product_data.get('price'):
            try:
                for script in soup.find_all('script', type='application/ld+json'):
                    if not script.string:
                        continue
                    try:
                        json_data = json.loads(script.string)
                        
                        if isinstance(json_data, list):
                            for item in json_data:
                                if item.get('@type') == 'Product':
                                    json_data = item
                                    break
                        
                        if json_data and json_data.get('@type') == 'Product':
                            if not product_data.get('name') and json_data.get('name'):
                                product_data['name'] = json_data['name']
                                
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
                                    
                            if json_data.get('brand') and isinstance(json_data['brand'], dict):
                                product_data['brand'] = json_data['brand'].get('name')
                                
                            if json_data.get('description'):
                                product_data['description'] = json_data['description']
                                
                            if json_data.get('sku'):
                                product_data['sku'] = json_data['sku']
                    except (json.JSONDecodeError, ValueError, TypeError):
                        continue
            except Exception as e:
                logger.error(f"Error extracting JSON-LD data: {e}")
        
        # Method 3: Extract from HTML elements
        if not product_data.get('price'):
            try:
                # Common price selectors in Salla templates
                price_selectors = [
                    '.product-price', 
                    '.price', 
                    '.product-details__price',
                    '.product-details-price',
                    '.product-details .amount',
                    '.entry-summary .amount',
                    '[data-price]',
                    '.price-box',
                    '.price-wrapper',
                    '.product-price-regular'
                ]
                
                for selector in price_selectors:
                    price_elements = soup.select(selector)
                    for price_element in price_elements:
                        price_text = price_element.get_text().strip()
                        price = clean_price(price_text)
                        if price:
                            product_data['price'] = price
                            break
                    if product_data.get('price'):
                        break
            except Exception as e:
                logger.error(f"Error extracting price from HTML: {e}")
        
        # If name wasn't found, try title tag
        if not product_data.get('name'):
            try:
                title_tag = soup.find('title')
                if title_tag:
                    product_data['name'] = title_tag.get_text().split('-')[0].strip()
            except Exception as e:
                logger.error(f"Error extracting title: {e}")
                
        # Get product image
        if not product_data.get('image_url'):
            try:
                image_meta = soup.find('meta', property='og:image')
                if image_meta and image_meta.get('content'):
                    product_data['image_url'] = image_meta['content']
            except (TypeError, KeyError):
                pass
                
        # Set defaults if not found
        if not product_data.get('currency'):
            product_data['currency'] = 'SAR'  # Default currency
            
        if not product_data.get('availability'):
            product_data['availability'] = 'in stock'  # Default
            
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
            for script in soup.find_all('script', type='application/ld+json'):
                if not script.string:
                    continue
                    
                try:
                    json_data = json.loads(script.string)
                    
                    if isinstance(json_data, list):
                        for item in json_data:
                            if item.get('@type') == 'Product':
                                json_data = item
                                break
                    
                    if json_data and json_data.get('@type') == 'Product':
                        product_data['name'] = json_data.get('name')
                        
                        if json_data.get('brand'):
                            if isinstance(json_data['brand'], dict):
                                product_data['brand'] = json_data['brand'].get('name')
                            else:
                                product_data['brand'] = json_data['brand']
                                
                        if json_data.get('description'):
                            product_data['description'] = json_data['description']
                            
                        if json_data.get('sku'):
                            product_data['sku'] = json_data['sku']
                            
                        if json_data.get('category'):
                            product_data['category'] = json_data['category']
                            
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
                        
                        # Extract store name
                        if json_data.get('seller') and isinstance(json_data['seller'], dict):
                            product_data['store_name'] = json_data['seller'].get('name')
                            
                        if json_data.get('image'):
                            if isinstance(json_data['image'], list):
                                product_data['image_url'] = json_data['image'][0]
                            else:
                                product_data['image_url'] = json_data['image']
                                
                        if product_data.get('name') and product_data.get('price'):
                            break
                except (json.JSONDecodeError, ValueError, TypeError):
                    continue
        except Exception as e:
            logger.error(f"Error extracting JSON-LD data: {e}")
            
        # Method 2: Extract from meta tags
        try:
            # Get product name
            if not product_data.get('name'):
                meta_title = soup.find('meta', property='og:title')
                if meta_title and meta_title.get('content'):
                    product_data['name'] = meta_title['content'].strip()
                    
            # Get store name    
            if not product_data.get('store_name'):
                store_meta = soup.find('meta', property='og:site_name')
                if store_meta and store_meta.get('content'):
                    product_data['store_name'] = store_meta['content']
                    
            # Get product description
            if not product_data.get('description'):
                desc_meta = soup.find('meta', property='og:description')
                if desc_meta and desc_meta.get('content'):
                    product_data['description'] = desc_meta['content']
                    
            # Get product image    
            if not product_data.get('image_url'):
                image_meta = soup.find('meta', property='og:image')
                if image_meta and image_meta.get('content'):
                    product_data['image_url'] = image_meta['content']
        except (TypeError, KeyError, Exception) as e:
            logger.error(f"Error extracting metadata: {e}")
        
        # Method 3: Extract from HTML elements
        if not product_data.get('price'):
            try:
                # Common price selectors in Zid templates
                price_selectors = [
                    '.product-details-price', 
                    '.product__price', 
                    '.price-box',
                    '.product-price',
                    '.zid-product-price',
                    '.product-single__price',
                    '.price__sale',
                    '.product-template__price',
                    '[data-product-price]',
                    '.price',
                    '.amount'
                ]
                
                for selector in price_selectors:
                    price_elements = soup.select(selector)
                    for price_element in price_elements:
                        price_text = price_element.get_text().strip()
                        price = clean_price(price_text)
                        if price:
                            product_data['price'] = price
                            break
                    if product_data.get('price'):
                        break
            except Exception as e:
                logger.error(f"Error extracting price from HTML: {e}")
                
        # If name wasn't found, try title tag
        if not product_data.get('name'):
            try:
                title_tag = soup.find('title')
                if title_tag:
                    title_text = title_tag.get_text()
                    if ' - ' in title_text:
                        product_data['name'] = title_text.split(' - ')[0].strip()
                    else:
                        product_data['name'] = title_text.strip()
            except Exception as e:
                logger.error(f"Error extracting title: {e}")
                
        # Set defaults if not found
        if not product_data.get('currency'):
            product_data['currency'] = 'SAR'
            
        if not product_data.get('availability'):
            product_data['availability'] = 'in stock'
            
        return product_data

# Function to be used by external code
def get_product_info(url):
    """
    Get product information for a single URL.
    This improved version tries to detect the platform from page content
    and will attempt both extractors if platform detection is ambiguous.
    """
    # Step 1: Get the page content (do this once to avoid multiple requests)
    page_content = get_page_content(url)
    if not page_content:
        logger.error(f"Could not fetch content from URL: {url}")
        return None
    
    # Step 2: Try to detect the platform using the page content
    platform = detect_platform(url, page_content)
    
    # If platform detection succeeded, use the appropriate extractor
    if platform == 'salla':
        extractor = SallaExtractor()
        product_data = extractor.get_product_data(url)
        if product_data:
            product_data['url'] = url
            product_data['platform'] = platform
            return product_data
    
    elif platform == 'zid':
        extractor = ZidExtractor()
        product_data = extractor.get_product_data(url)
        if product_data:
            product_data['url'] = url
            product_data['platform'] = platform
            return product_data
    
    # If platform detection failed or extractor failed, try both extractors
    logger.info(f"Trying both extractors for URL: {url}")
    
    # Try Salla extractor first
    extractor = SallaExtractor()
    product_data = extractor.get_product_data(url)
    if product_data and product_data.get('price'):
        product_data['url'] = url
        product_data['platform'] = 'salla'
        return product_data
    
    # Try Zid extractor next
    extractor = ZidExtractor()
    product_data = extractor.get_product_data(url)
    if product_data and product_data.get('price'):
        product_data['url'] = url
        product_data['platform'] = 'zid'
        return product_data
    
    logger.error(f"Could not extract product data from URL: {url}")
    return None

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
