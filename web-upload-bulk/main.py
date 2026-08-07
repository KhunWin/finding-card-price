#!/usr/bin/env python3
"""
Boutir Product Uploader
Upload products from Excel file to Boutir store using Selenium or Playwright
"""

import argparse
import logging
import sys
from pathlib import Path
from uploaders.selenium_uploader import SeleniumUploader
from uploaders.playwright_uploader import PlaywrightUploader
from utils.excel_reader import ExcelReader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_excel_file(file_path):
    """Validate that the Excel file exists and has required columns"""
    try:
        reader = ExcelReader()
        products = reader.read_products(file_path)
        if not products:
            logger.error("Excel file is empty or has no valid data")
            return False
        logger.info(f"Excel file validated: {len(products)} products found")
        return True
    except Exception as e:
        logger.error(f"Excel file validation failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Upload products to Boutir store')
    parser.add_argument(
        'excel_file',
        type=str,
        help='Path to Excel file containing product data'
    )
    parser.add_argument(
        '--method',
        choices=['selenium', 'playwright'],
        default='playwright',
        help='Upload method to use (default: playwright)'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        default=True,
        help='Run browser in headless mode (default: True)'
    )
    
    args = parser.parse_args()
    
    # Validate Excel file
    excel_path = Path(args.excel_file)
    if not excel_path.exists():
        logger.error(f"Excel file not found: {excel_path}")
        sys.exit(1)
    
    if not validate_excel_file(excel_path):
        sys.exit(1)
    
    # Select uploader
    logger.info(f"Using {args.method} uploader (headless: {args.headless})")
    
    try:
        if args.method == 'selenium':
            uploader = SeleniumUploader(headless=args.headless)
        else:
            uploader = PlaywrightUploader(headless=args.headless)
        
        success = uploader.run(str(excel_path))
        
        if success:
            logger.info("✅ Upload completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Upload failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Upload interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()