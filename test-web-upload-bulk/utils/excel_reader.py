import pandas as pd
from pathlib import Path
import logging
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExcelReader:
    # Define all possible columns with their default values
    DEFAULT_COLUMNS = {
        'URL': '',
        'Product ID': '',
        'Title': '',
        'Description': '',
        'Product Option 1 - Type': '',
        'Product Option 1 - Name': '',
        'Product Option 2 - Type': '',
        'Product Option 2 - Name': '',
        'Product Option 3 - Type': '',
        'Product Option 3 - Name': '',
        'Product Option Image URLs': '',
        'Product Option Video URLs': '',
        'Categories': '',
        'Cost': 0.0,
        'Price': 0.0,
        'Discounted Price': 0.0,
        'Member Price': 0.0,
        'Enable volume price': 'FALSE',
        'Volume price tier 1 - quantity': 0,
        'Volume price tier 1 - unit price': 0.0,
        'Volume price tier 2 - quantity': 0,
        'Volume price tier 2 - unit price': 0.0,
        'Volume price tier 3 - quantity': 0,
        'Volume price tier 3 - unit price': 0.0,
        'Unlimited stock': 'TRUE',
        'Stock': 0,
        'Unlimited backorder': 'TRUE',
        'Backorder limit': 0,
        'Backorder remark': '',
        'Purchase Limit': 0,
        'Minimum order quantity': 1,
        'Weight (kg)': 0.0,
        'SKU': '',
        'Image URLs': '',
        'Video URLs': '',
        'Hashtags': '',
        'Enable Pre Order': 'FALSE',
        'Pre Order Est. Shipping Date (date-YYYY-MM-DD)': '',
        'Pre Order Remark': '',
        'Purchase start time': '',
        'Purchase end time': '',
        'Auto-unpublish when purchase ended': 'FALSE',
        'Publish Status': 'draft',
        'Listing status': 'available',
        'Barcode': '',
        'All campaigns (except free shipping)': '',
        'Free shipping campaign': '',
        'Promo code': '',
        'Supplier': '',
        'Merchant Remark': '',
        'Meta keywords': '',
        'Meta title': '',
        'Meta description': ''
    }
    
    # Required columns that must exist
    REQUIRED_COLUMNS = ['Title', 'Price']
    
    @staticmethod
    def read_products(file_path: str) -> List[Dict[str, Any]]:
        """
        Read product data from Excel file with flexible column support.
        Handles files with minimum columns (Title, Price) to full format.
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Excel file not found: {file_path}")
            
            # Read Excel file
            df = pd.read_excel(file_path)
            logger.info(f"Loaded Excel file with {len(df)} rows and {len(df.columns)} columns")
            
            # Check for required columns
            missing_required = [col for col in ExcelReader.REQUIRED_COLUMNS if col not in df.columns]
            if missing_required:
                raise ValueError(f"Missing required columns: {', '.join(missing_required)}")
            
            # Log what columns are present
            present_columns = set(df.columns)
            logger.info(f"Found columns: {', '.join(present_columns)}")
            
            # Add missing columns with default values
            for col, default_val in ExcelReader.DEFAULT_COLUMNS.items():
                if col not in df.columns:
                    df[col] = default_val
                    logger.debug(f"Added missing column '{col}' with default value")
            
            # Clean and convert data types
            df = ExcelReader.clean_dataframe(df)
            
            # Convert to dictionary records
            records = df.to_dict('records')
            logger.info(f"Successfully processed {len(records)} products")
            
            return records
            
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            raise
    
    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Clean and convert data types in the dataframe"""
        try:
            # Handle numeric columns
            numeric_columns = ['Cost', 'Price', 'Discounted Price', 'Member Price', 
                             'Stock', 'Weight (kg)', 'Minimum order quantity', 
                             'Purchase Limit', 'Backorder limit']
            
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Handle quantity columns for volume pricing
            volume_quantity_cols = ['Volume price tier 1 - quantity', 
                                   'Volume price tier 2 - quantity',
                                   'Volume price tier 3 - quantity']
            for col in volume_quantity_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            
            # Handle price columns for volume pricing
            volume_price_cols = ['Volume price tier 1 - unit price',
                                'Volume price tier 2 - unit price',
                                'Volume price tier 3 - unit price']
            for col in volume_price_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
            # Handle boolean/flag columns
            boolean_columns = ['Enable volume price', 'Unlimited stock', 
                             'Unlimited backorder', 'Enable Pre Order',
                             'Auto-unpublish when purchase ended']
            
            for col in boolean_columns:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: 'TRUE' if x in [True, 'TRUE', 'true', 'Yes', 'yes', 1, '1'] else 'FALSE')
            
            # Fill NaN in string columns
            string_columns = ['Title', 'Description', 'Categories', 'SKU', 'Barcode', 
                            'Image URLs', 'Video URLs', 'Hashtags', 'Supplier',
                            'Publish Status', 'Listing status']
            
            for col in string_columns:
                if col in df.columns:
                    df[col] = df[col].fillna('')
            
            # Ensure Title is not empty
            df['Title'] = df['Title'].fillna('Untitled Product')
            
            # Set default publish status if empty
            df['Publish Status'] = df['Publish Status'].apply(
                lambda x: 'draft' if pd.isna(x) or x == '' else x
            )
            
            # Set default listing status if empty
            df['Listing status'] = df['Listing status'].apply(
                lambda x: 'available' if pd.isna(x) or x == '' else x
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Error cleaning dataframe: {e}")
            raise
    
    @staticmethod
    def validate_product_data(products: List[Dict[str, Any]]) -> bool:
        """Validate product data before upload"""
        try:
            if not products:
                logger.error("No products to validate")
                return False
            
            invalid_products = []
            for idx, product in enumerate(products):
                errors = []
                
                # Check Title
                if not product.get('Title') or str(product.get('Title')).strip() == '':
                    errors.append("Title is empty")
                
                # Check Price (must be >= 0)
                try:
                    price = float(product.get('Price', 0))
                    if price < 0:
                        errors.append(f"Price cannot be negative: {price}")
                except (ValueError, TypeError):
                    errors.append(f"Invalid price format: {product.get('Price')}")
                
                # Check Stock
                try:
                    stock = int(product.get('Stock', 0))
                    if stock < 0:
                        errors.append(f"Stock cannot be negative: {stock}")
                except (ValueError, TypeError):
                    errors.append(f"Invalid stock format: {product.get('Stock')}")
                
                if errors:
                    invalid_products.append({
                        'index': idx,
                        'title': product.get('Title', 'Unknown'),
                        'errors': errors
                    })
            
            if invalid_products:
                logger.warning(f"Found {len(invalid_products)} products with validation issues:")
                for invalid in invalid_products:
                    logger.warning(f"  Row {invalid['index'] + 1} - {invalid['title']}: {', '.join(invalid['errors'])}")
                return False
            
            logger.info("All products validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error validating products: {e}")
            return False
    
    @staticmethod
    def get_column_mapping(df: pd.DataFrame) -> Dict[str, str]:
        """Get mapping of Excel columns to Boutir system columns"""
        try:
            # Standard mapping for Boutir
            mapping = {
                'Title': 'Product Name',
                'Description': 'Description',
                'Categories': 'Category',
                'Price': 'Price',
                'Cost': 'Cost',
                'Discounted Price': 'Discounted Price',
                'Member Price': 'Member Price',
                'Stock': 'Stock',
                'SKU': 'SKU',
                'Barcode': 'Barcode',
                'Image URLs': 'Image URLs',
                'Video URLs': 'Video URLs',
                'Hashtags': 'Hashtags',
                'Supplier': 'Supplier',
                'Weight (kg)': 'Weight',
                'Publish Status': 'Publish Status',
                'Listing status': 'Listing Status',
                'URL': 'Product URL',
                'Product ID': 'Product ID'
            }
            
            # Return only columns that exist in the dataframe
            existing_mapping = {k: v for k, v in mapping.items() if k in df.columns}
            logger.info(f"Column mapping: {existing_mapping}")
            return existing_mapping
            
        except Exception as e:
            logger.error(f"Error creating column mapping: {e}")
            return {}