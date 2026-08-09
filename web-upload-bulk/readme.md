#!/bin/bash

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt   

# Install dependencies
pip install -r requirements.txt
pip install playwright
pip install openpyxl
pip install pandas
pip install selenium
pip install webdriver-manager

pip install playwright openpyxl pandas selenium webdriver-manager




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


###this is for creating .exe file
# Auto-detect and build for current platform
python build.py

# Build debug version with console
python build.py --debug

# Show platform information
python build.py --info

# Clean only
python build.py --clean-only

# Attempt to build for specific platform (with warning)
python build.py --platform linux
python build.py --platform windows


create a product key to access the application. 
two types of key:
key 1: when 'Start Scraping" is clicked, if a product key is not provided before, then, ask a user to provide the key. then, this key is only for running 'Start Scarping'. when 'upload, ask the user to provide another product key too. 
key 2: after providing this key, the user will be able to click 'Start scraping' and 'Upload' buttons. 
there should be only 50 for key 1 and 50 for key 2. so in total, there should be only 100. i will change this python program to an executable program (.exe). so the code must work when the program is exported to exe program. so modify build_exe py to be able to run exe file. 
give me the 100 keys too. i will run testing to see if these keys work. 
