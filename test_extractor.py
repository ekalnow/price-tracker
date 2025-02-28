#!/usr/bin/env python3
import sys
import json
import logging
from extractors import get_product_info

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_extractor.py <product_url>")
        sys.exit(1)
    
    url = sys.argv[1]
    logger.info(f"Testing extraction for URL: {url}")
    
    product_data = get_product_info(url)
    
    if product_data:
        print("\n===== EXTRACTED PRODUCT DATA =====")
        print(json.dumps(product_data, indent=2, ensure_ascii=False))
        print(f"\nPlatform: {product_data.get('platform', 'Unknown')}")
        print(f"Product Name: {product_data.get('name', 'Unknown')}")
        print(f"Price: {product_data.get('price', 'Unknown')} {product_data.get('currency', '')}")
        print(f"Store: {product_data.get('store_name', 'Unknown')}")
        print("==============================\n")
    else:
        print("\n⛔ Failed to extract product data.")
        print("Please check the logs for more details.\n")

if __name__ == "__main__":
    main()
