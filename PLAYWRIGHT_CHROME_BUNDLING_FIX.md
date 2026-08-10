# Playwright Chrome Browser Bundling Fix

## Problem

When running the bundled EXE on another machine, Playwright failed with:

```
ERROR: Executable doesn't exist at C:\Users\vboxuser\AppData\Local\Temp\_MEI100242\playwright\driver\package\.local-browsers\chromium_headless_shell-1234\chrome-headless-shell.exe
```

## Root Cause

1. **Playwright's Default Behavior**: Expects its own bundled Chromium from `playwright install`
2. **PyInstaller Limitation**: Browser binaries NOT automatically included in EXE
3. **User Burden**: Would require manual `playwright install`, defeating standalone EXE purpose

## Solution: Use System Chrome Instead

Instead of bundling Chromium (would make EXE huge), we use **Google Chrome already on user's system**.

## Code Changes in `playwright_uploader.py`

### 1. Enhanced Chrome Detection with Registry Support

- Checks common file locations
- Reads Windows registry for Chrome installation path
- Searches multiple registry keys (HKLM and HKCU)

### 2. Use System Chrome with Playwright

```python
self.browser = self.playwright.chromium.launch(
    headless=self.headless,
    executable_path=chrome_path,  # KEY FIX: Use system Chrome
    args=[...]
)
```

### 3. Clear Error Messages

When Chrome not found, provides installation instructions instead of cryptic Chromium error.

## Benefits

✅ **No Playwright install needed**: Uses Chrome already on system
✅ **Truly standalone**: Works immediately after distribution
✅ **Smaller executable**: No 100+ MB browser binaries bundled
✅ **Better error messages**: Clear instructions if Chrome missing
✅ **Registry support**: Finds Chrome in non-standard locations
✅ **Better compatibility**: Uses user's Chrome version

## User Requirements

**What users NEED:**
- ✅ Google Chrome browser (free from google.com/chrome)
- ✅ TCGCardScraper.exe

**What users DON'T need:**
- ❌ Python, `playwright install`, browser downloads, manual setup

## Files Modified

1. ✅ `web-upload-bulk/uploaders/playwright_uploader.py` - Enhanced Chrome detection
2. ✅ `build_exe_linux_window.py` - Added `.env` and Playwright dependencies
3. ✅ `build_exe.py` - Already had Playwright dependencies
