# PyInstaller Upload Module Fix - Complete Solution

## Problem Overview

The TCG Card Scraper Pro executable was failing to run the upload functionality with errors:

### Initial Error (Build-time)
```
ERROR: Hidden import 'uploaders.playwright_uploader' not found
ERROR: Hidden import 'uploaders.selenium_uploader' not found
```

### Runtime Error After First Fix
```
No module named 'selenium.webdriver.chrome.webdriver'
Upload failed with both methods
```

## Root Causes

1. **Module Path Issue**: The `uploaders` and `utils` modules are in `web-upload-bulk/` subdirectory
2. **Missing Dependencies**: Selenium and Playwright packages were not explicitly included
3. **Incomplete Import Detection**: PyInstaller missed the browser automation libraries

## Complete Solution - Changes to `build_exe_linux_window.py`

Added the following configuration to the `get_common_args()` function:

```python
# KEY FIX #1: Add web-upload-bulk to Python path
'--paths=web-upload-bulk',

# KEY FIX #2: Explicitly import web-upload-bulk modules
'--hidden-import=uploaders',
'--hidden-import=uploaders.playwright_uploader',
'--hidden-import=uploaders.selenium_uploader',
'--hidden-import=uploaders.__init__',
'--hidden-import=utils',
'--hidden-import=utils.config',
'--hidden-import=utils.excel_reader',
'--hidden-import=utils.__init__',

# KEY FIX #3: Explicitly import Selenium and Playwright
'--hidden-import=selenium',
'--hidden-import=selenium.webdriver',
'--hidden-import=selenium.webdriver.chrome',
'--hidden-import=selenium.webdriver.chrome.webdriver',
'--hidden-import=selenium.webdriver.chrome.options',
'--hidden-import=selenium.webdriver.chrome.service',
'--hidden-import=selenium.webdriver.common',
'--hidden-import=selenium.webdriver.common.by',
'--hidden-import=selenium.webdriver.common.keys',
'--hidden-import=selenium.webdriver.support',
'--hidden-import=selenium.webdriver.support.ui',
'--hidden-import=selenium.webdriver.support.expected_conditions',
'--hidden-import=selenium.common',
'--hidden-import=selenium.common.exceptions',
'--hidden-import=playwright',
'--hidden-import=playwright.sync_api',

# KEY FIX #4: Bundle the web-upload-bulk directory
'--add-data=web-upload-bulk;web-upload-bulk',

# KEY FIX #5: Collect all submodules and data files
'--collect-all=uploaders',
'--collect-all=utils',
'--collect-all=selenium',
'--collect-all=playwright',
```

## Explanation of Each Fix

1. **`--paths=web-upload-bulk`**: Adds directory to PyInstaller's module search path
2. **Hidden imports for custom modules**: Explicitly includes uploader and utility modules
3. **Hidden imports for Selenium & Playwright**: Includes all necessary browser automation components
4. **`--add-data`**: Copies the entire web-upload-bulk directory into the executable
5. **`--collect-all`**: Collects all submodules, data files, and binary dependencies

## Build Results

- ✅ Build completed successfully
- ✅ Executable size: 88.84 MB
- ✅ No module import errors
- ✅ All dependencies bundled

## Do Users Need to Install Selenium/Playwright?

**No!** With this fix, Selenium and Playwright are bundled inside the executable.

However, users **will still need**:
1. **Chrome Browser** installed (the libraries use Chrome for automation)
2. **Internet connection on first run** (for Selenium Manager to download ChromeDriver if needed)

## Build Commands

```bash
# Clean and rebuild
python build_exe_linux_window.py --clean-only
python build_exe_linux_window.py

# If exe is in use
taskkill /F /IM TCGCardScraper.exe
python build_exe_linux_window.py
```

## Summary

The executable is now fully functional and self-contained. Users only need Chrome browser installed - no Python, Selenium, or Playwright installation required!
