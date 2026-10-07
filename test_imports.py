#!/usr/bin/env python3
"""Test script to verify imports work correctly"""

import sys
import os

# Main directory is where uploaders and utils are located
main_dir = os.path.dirname(__file__)
if main_dir not in sys.path:
    sys.path.insert(0, main_dir)
    print(f"✓ Added main directory to path: {main_dir}")
else:
    print(f"✓ Main directory already in path: {main_dir}")

print("\nTesting imports...")

try:
    from uploaders.playwright_uploader import PlaywrightUploader
    print("✓ Successfully imported PlaywrightUploader")
except Exception as e:
    print(f"✗ Failed to import PlaywrightUploader: {e}")

try:
    from uploaders.selenium_uploader import SeleniumUploader
    print("✓ Successfully imported SeleniumUploader")
except Exception as e:
    print(f"✗ Failed to import SeleniumUploader: {e}")

try:
    from utils.config import Config
    print("✓ Successfully imported Config")
except Exception as e:
    print(f"✗ Failed to import Config: {e}")

try:
    from utils.excel_reader import ExcelReader
    print("✓ Successfully imported ExcelReader")
except Exception as e:
    print(f"✗ Failed to import ExcelReader: {e}")

print("\n=== Test Complete ===")
