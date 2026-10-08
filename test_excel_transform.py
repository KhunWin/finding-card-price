#!/usr/bin/env python3
"""Test script to verify Excel transformation with empty field filtering"""

import pandas as pd
import os
from excel_transformer import ExcelTransformer

# Create test data
test_data = {
    'imageUrl': [
        'https://example.com/image1.jpg',
        '',  # Empty image URL - should be removed
        'https://example.com/image3.jpg',
        'https://example.com/image4.jpg',
        'https://example.com/image5.jpg'
    ],
    'productName': [
        'Product 1',
        'Product 2',
        '',  # Empty title - should be removed
        'Product 4',
        'Product 5'
    ],
    'marketPrice': [
        10.50,
        25.00,
        15.75,
        0,  # Zero price - should be removed
        30.00
    ],
    'groupName': [
        'Category A',
        'Category B',
        'Category C',
        'Category D',
        ''  # Empty category - should be removed
    ]
}

print("Creating test Excel file...")
test_file = 'test_input.xlsx'
df_test = pd.DataFrame(test_data)
df_test.to_excel(test_file, index=False)
print(f"✓ Created {test_file} with {len(df_test)} rows")
print("\nTest data:")
print(df_test)
print("\n" + "="*60)

# Transform the file
print("\nTransforming file...")
transformer = ExcelTransformer(source='tcg')
output_file = transformer.transform(test_file, usd_to_hkd_rate=7.8)

print(f"\n✓ Transformation complete!")
print(f"Output file: {output_file}")

# Read and display output
print("\n" + "="*60)
print("Output data (only valid rows):")
df_output = pd.read_excel(output_file)
print(f"\nTotal rows in output: {len(df_output)}")
print("\nKey columns:")
print(df_output[['Image URLs', 'Title', 'Price', 'Categories']].to_string())

# Expected: Only 1 row should remain (row 0: Product 1)
# Row 1: Empty Image URL - REMOVED
# Row 2: Empty Title - REMOVED  
# Row 3: Zero Price - REMOVED
# Row 4: Empty Category - REMOVED

print("\n" + "="*60)
print("\nExpected behavior:")
print("- Row 0 (Product 1): KEPT (all fields valid)")
print("- Row 1 (Product 2): REMOVED (empty Image URL)")
print("- Row 2 (Product 3): REMOVED (empty Title)")
print("- Row 3 (Product 4): REMOVED (zero Price)")
print("- Row 4 (Product 5): REMOVED (empty Category)")
print(f"\nExpected final count: 1 row")
print(f"Actual final count: {len(df_output)} rows")

if len(df_output) == 1:
    print("\n✅ TEST PASSED: Filtering works correctly!")
else:
    print(f"\n❌ TEST FAILED: Expected 1 row, got {len(df_output)} rows")

# Cleanup
print("\nCleaning up test files...")
if os.path.exists(test_file):
    os.remove(test_file)
    print(f"✓ Removed {test_file}")
if os.path.exists(output_file):
    os.remove(output_file)
    print(f"✓ Removed {output_file}")

print("\n=== Test Complete ===")
