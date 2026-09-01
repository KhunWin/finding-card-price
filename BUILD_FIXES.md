# Build Fixes for PyInstaller Errors

## Issues Found and Fixed

### 1. **ModuleNotFoundError: No module named 'scarp_yuyu_v4'**

**Problem:**
The error occurred because:
- `yuyutei_gui.py` was trying to import from `yuyu-tei` directory (with hyphen)
- The actual directory is named `yuyu_tei` (with underscore)
- PyInstaller couldn't find the module during the build process

**Fix Applied:**
1. **Fixed directory reference in `yuyutei_gui.py`** (line 13):
   ```python
   # Before:
   yuyu_tei_path = os.path.join(os.path.dirname(__file__), 'yuyu-tei')
   
   # After:
   yuyu_tei_path = os.path.join(os.path.dirname(__file__), 'yuyu_tei')
   ```

2. **Created `yuyu_tei/__init__.py`** to make it a proper Python package:
   ```python
   """
   Yuyu-Tei module for card scraping
   """
   from .scarp_yuyu_v4 import YuyuteiScraper, CardInfo
   from .yuyu_tei_wrapper import YuyuTeiWrapper
   
   __all__ = ['YuyuteiScraper', 'CardInfo', 'YuyuTeiWrapper']
   ```

3. **Updated `build_exe.py`** to include the yuyu_tei module:
   - Added hidden imports for yuyu_tei modules (lines 81-83):
     ```python
     '--hidden-import=yuyu_tei.yuyu_tei_wrapper',
     '--hidden-import=yuyu_tei.scarp_yuyu_v4',
     '--hidden-import=scarp_yuyu_v4',
     ```
   
   - Added yuyu_tei directory as data (line 60):
     ```python
     '--add-data=yuyu_tei:yuyu_tei',
     ```

4. **Updated debug build section** in `build_exe.py` with same fixes (lines 142-145)

### 2. **FileNotFoundError: strip tool not found**

**Problem:**
The `--strip` option in PyInstaller was trying to use a Unix/Linux `strip` tool that doesn't exist on Windows by default.

**Fix Applied:**
Commented out the `--strip` option in `build_exe.py` (line 89):
```python
# Before:
'--strip',                         # Strip symbols

# After:
# '--strip',                       # Strip symbols - removed due to missing strip tool on Windows
```

## Files Modified

1. **yuyutei_gui.py** - Fixed directory path reference
2. **build_exe.py** - Added hidden imports, data files, and removed --strip option
3. **yuyu_tei/__init__.py** - Created new file to make yuyu_tei a proper Python package

## Testing

After applying these fixes, the build should complete successfully. To build:

```bash
# Normal build (no console)
python build_exe.py

# Debug build (with console for troubleshooting)
python build_exe.py --debug
```

## Notes

- The yuyu_tei directory structure is now:
  ```
  yuyu_tei/
  ├── __init__.py           (NEW)
  ├── scarp_yuyu_v4.py
  └── yuyu_tei_wrapper.py
  ```

- If you still encounter issues, try the debug build first to see any runtime errors:
  ```bash
  python build_exe.py --debug
  ```

- Make sure to close any running instances of TCGCardScraper.exe before building, as the build script couldn't remove the old exe file (Access Denied error)
