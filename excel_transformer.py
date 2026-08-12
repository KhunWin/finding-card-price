"""
Excel Transformer for Boutir Upload
Transforms input Excel file to Boutir template format
"""

import pandas as pd
import os
from datetime import datetime


class ExcelTransformer:
    """Handles transformation of Excel files to Boutir format"""
    
    # Define the output columns in the exact order required
    OUTPUT_COLUMNS = [
        'URL', 'Product ID', 'Title', 'Description', 
        'Product Option 1 - Type', 'Product Option 1 - Name', 
        'Product Option 2 - Type', 'Product Option 2 - Name', 
        'Product Option 3 - Type', 'Product Option 3 - Name', 
        'Product Option Image URLs', 'Product Option Video URLs', 
        'Categories', 'Cost', 'Price', 'Discounted Price', 'Member Price', 
        'Enable volume price', 
        'Volume price tier 1 - quantity', 'Volume price tier 1 - unit price', 
        'Volume price tier 2 - quantity', 'Volume price tier 2 - unit price', 
        'Volume price tier 3 - quantity', 'Volume price tier 3 - unit price', 
        'Unlimited stock', 'Stock', 'Unlimited backorder', 'Backorder limit', 
        'Backorder remark', 'Purchase Limit', 'Minimum order quantity', 
        'Weight (kg)', 'SKU', 'Image URLs', 'Video URLs', 'Hashtags', 
        'Enable Pre Order', 'Pre Order Est. Shipping Date (date-YYYY-MM-DD)', 
        'Pre Order Remark', 'Purchase start time', 'Purchase end time', 
        'Auto-unpublish when purchase ended', 'Publish Status', 'Listing status', 
        'Barcode', 'All campaigns (except free shipping)', 'Free shipping campaign', 
        'Promo code', 'Supplier', 'Merchant Remark', 'Meta keywords', 
        'Meta title', 'Meta description'
    ]
    
    # Column mapping from input to output (with flexible naming)
    COLUMN_MAPPING = {
        'Image URLs': ['imageUrl', 'imageURL'],
        'Title': ['productName', 'name'],
        'Price': ['marketPrice'],
        'Categories': ['groupName']
    }
    
    # Default values for required fields
    DEFAULT_VALUES = {
        'Unlimited stock': 1,
        'Unlimited backorder': 0,
        'Backorder limit': 0,
        'Enable Pre Order': 0,
        'Publish Status': 1,
        'Listing status': 0,
        'All campaigns (except free shipping)': 0,
        'Free shipping campaign': 0,
        'Promo code': '0'
    }
    
    def __init__(self):
        pass
    
    def _find_column(self, df_columns, possible_names):
        """Find the first matching column name from a list of possibilities"""
        for name in possible_names:
            if name in df_columns:
                return name
        return None
    
    def transform(self, input_file_path, output_dir=None, usd_to_hkd_rate=1.0):
        """
        Transform input Excel file to Boutir format
        
        Args:
            input_file_path: Path to input Excel file
            output_dir: Directory to save output file (defaults to same as input)
            usd_to_hkd_rate: Exchange rate from USD to HKD
        Returns:
            Path to transformed Excel file
        """
        try:
            # Read input Excel file
            df_input = pd.read_excel(input_file_path)
            input_columns = df_input.columns.tolist()

            # Remove rows with FALSE in image_download_success column
            if 'image_download_success' in input_columns:
                initial_count = len(df_input)
                df_input = df_input[df_input['image_download_success'] != False]
                df_input = df_input[df_input['image_download_success'] != 'FALSE']
                df_input = df_input[df_input['image_download_success'] != 'False']
                removed_count = initial_count - len(df_input)
                if removed_count > 0:
                    print(f"Removed {removed_count} rows with failed image downloads")
            
            
            # Create empty DataFrame with output columns
            df_output = pd.DataFrame(columns=self.OUTPUT_COLUMNS)
            
            # Map columns from input to output
            for output_col, possible_input_cols in self.COLUMN_MAPPING.items():
                input_col = self._find_column(input_columns, possible_input_cols)
                if input_col:
                    df_output[output_col] = df_input[input_col]

             # Apply USD to HKD conversion to Price column
            if 'Price' in df_output.columns and not df_output['Price'].isna().all():
                df_output['Price'] = pd.to_numeric(df_output['Price'], errors='coerce') * usd_to_hkd_rate
                print(f"Applied USD to HKD conversion rate: {usd_to_hkd_rate}")
            
            # Set default values for required fields
            for col, value in self.DEFAULT_VALUES.items():
                df_output[col] = value
            
            # Fill remaining columns with empty strings
            for col in self.OUTPUT_COLUMNS:
                if col not in df_output.columns:
                    df_output[col] = ''
                elif df_output[col].isna().all():
                    df_output[col] = ''
            
            # Ensure columns are in correct order
            df_output = df_output[self.OUTPUT_COLUMNS]
            
            # Generate output filename
            if output_dir is None:
                output_dir = os.path.dirname(input_file_path)
            
            input_filename = os.path.basename(input_file_path)
            name_without_ext = os.path.splitext(input_filename)[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{name_without_ext}_transformed_{timestamp}.xlsx"
            output_path = os.path.join(output_dir, output_filename)
            
            # Save to Excel
            df_output.to_excel(output_path, index=False, sheet_name='result')
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Error transforming Excel file: {str(e)}")
    
    def validate_input_file(self, file_path):
        """
        Validate that input file has required columns
        
        Args:
            file_path: Path to input Excel file
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            df = pd.read_excel(file_path)
            columns = df.columns.tolist()
            
            # Check for required input columns (with flexible naming)
            missing_cols = []
            for output_col, possible_names in self.COLUMN_MAPPING.items():
                if not any(name in columns for name in possible_names):
                    missing_cols.append(output_col)
            
            if missing_cols:
                return False, f"Missing required columns: {', '.join(missing_cols)}"
            
            return True, "File is valid"
            
        except Exception as e:
            return False, f"Error reading file: {str(e)}"



