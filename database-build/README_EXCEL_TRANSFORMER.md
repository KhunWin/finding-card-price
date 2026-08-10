# Excel Transformer for Boutir Upload

## Overview
This tool transforms Excel files from the TCG Player format to the Boutir upload format, making it easy to prepare product data for bulk upload.

## Features

### 1. **Transform Excel File Button**
- Converts input Excel files to Boutir-compatible format
- Automatically detects column names (flexible naming support)
- Generates timestamped output files

### 2. **Stop Button**
- Allows you to stop the upload process at any time
- Safely interrupts ongoing operations

### 3. **Run Upload Button**
- Uploads the transformed Excel file to Boutir
- Automatically uses the transformed file after transformation

## How to Use

### Step 1: Prepare Your Input File
Your input Excel file should contain these columns (with flexible naming):
- **imageUrl** or **imageURL** → Image URLs
- **productName** or **name** → Title
- **marketPrice** → Price
- **groupName** or **categoryId** → Categories

### Step 2: Transform the File
1. Click the **"Transform Excel File"** button
2. Select your input Excel file (e.g., `BaseSetProductsAndPrices.xlsx`)
3. The tool will validate and transform the file
4. A new file will be created with the suffix `_transformed_YYYYMMDD_HHMMSS.xlsx`

### Step 3: Upload to Boutir
1. The transformed file is automatically selected for upload
2. Click **"Run Upload"** to start the upload process
3. Use **"Stop"** button if you need to interrupt the upload

## Output Format

The transformed Excel file will have all required Boutir columns:
- URL, Product ID, Title, Description
- Product Options (1-3)
- Categories, Cost, Price, Discounted Price, Member Price
- Volume pricing tiers
- Stock settings (Unlimited stock = 1 by default)
- Backorder settings (Unlimited backorder = 0, Backorder limit = 0)
- Pre-order settings (Enable Pre Order = 0)
- Publishing settings (Publish Status = 1, Listing status = 0)
- And many more...

## Default Values

The following fields are automatically set:
- **Unlimited stock**: 1
- **Unlimited backorder**: 0
- **Backorder limit**: 0
- **Enable Pre Order**: 0
- **Publish Status**: 1
- **Listing status**: 0

All other columns not mapped from the input file will be empty.

## Files

- **excel_transformer.py**: Core transformation logic
- **upload_window.py**: GUI application with Transform, Stop, and Upload buttons
- **test_transformer.py**: Test script to verify transformation

## Testing

Run the test script to verify the transformation:
```bash
python test_transformer.py
```

This will:
1. Validate the input file
2. Transform it to Boutir format
3. Display the results

## Example

**Input file** (`BaseSetProductsAndPrices.xlsx`):
```
productId | name     | imageUrl                    | marketPrice | categoryId
42346     | Alakazam | https://tcgplayer.com/...   | 71.43       | 3
```

**Output file** (`BaseSetProductsAndPrices_transformed_20260807_170725.xlsx`):
```
Title    | Categories | Price | Image URLs                  | Unlimited stock | ...
Alakazam | 3          | 71.43 | https://tcgplayer.com/...   | 1               | ...
```

## Notes

- The transformation preserves all data from mapped columns
- Output files are saved in the same directory as the input file
- Filenames include timestamps to prevent overwriting
- The tool supports flexible column naming for compatibility
