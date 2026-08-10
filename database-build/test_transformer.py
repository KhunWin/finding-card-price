"""
Test script for Excel Transformer
"""

from excel_transformer import ExcelTransformer
import os

def test_transformer():
    """Test the Excel transformer with sample data"""
    
    transformer = ExcelTransformer()
    
    # Test file path
    test_file = "excel-files/tcg_data-original-download.xlsx"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    print("=" * 70)
    print("Testing Excel Transformer")
    print("=" * 70)
    print()
    
    # Validate input file
    print("1. Validating input file...")
    is_valid, message = transformer.validate_input_file(test_file)
    print(f"   Result: {message}")
    
    if not is_valid:
        print("❌ Validation failed!")
        return
    
    print("✅ Validation passed!")
    print()
    
    # Transform the file
    print("2. Transforming file...")
    try:
        output_file = transformer.transform(test_file, "excel-files")
        print(f"✅ Transformation successful!")
        print(f"   Output file: {output_file}")
        print()
        
        # Check if file exists
        if os.path.exists(output_file):
            print(f"✅ Output file created successfully!")
            print(f"   File size: {os.path.getsize(output_file)} bytes")
        else:
            print(f"❌ Output file not found!")
            
    except Exception as e:
        print(f"❌ Transformation failed: {str(e)}")
    
    print()
    print("=" * 70)
    print("Test completed!")
    print("=" * 70)

if __name__ == "__main__":
    test_transformer()
