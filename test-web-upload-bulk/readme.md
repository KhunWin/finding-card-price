#!/bin/bash

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install playwright
pip install openpyxl
pip install pandas
pip install selenium
pip install webdriver-manager

# Install Playwright browsers
playwright install chromium

# Create necessary directories
mkdir -p downloads uploads

echo "Setup complete!"
echo "Create .env file with your credentials"
echo "Run: python main.py products.xlsx --method playwright"

# Boutir Credentials
BOUTIR_EMAIL=your_email@example.com
BOUTIR_PASSWORD=your_password

# Directories
DOWNLOAD_DIR=./downloads
UPLOAD_DIR=./uploads

# Using Playwright (recommended)
python main.py products.xlsx --method playwright

# Using Selenium
python main.py products.xlsx --method selenium

# Run in non-headless mode (visible browser)
python main.py products.xlsx --method playwright --no-headless

# Using with custom Excel file
python main.py /path/to/your/products.xlsx --method playwright