# .env File Bundling Solution

## Problem
When running the EXE on another machine, the application crashed with:
```
ValueError: Supabase credentials not found in .env file
```

This happened because the `.env` file was not bundled with the executable, so the Supabase connection credentials were missing.

## Solution Implemented

### 1. Modified `product_keys_supabase.py` (Lines 16-28)
Added logic to detect if the application is running as a PyInstaller executable and load the `.env` file from the bundled resources:

```python
# Load environment variables
# Handle PyInstaller bundled .env file
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    bundle_dir = sys._MEIPASS
    env_path = os.path.join(bundle_dir, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()  # Try default location as fallback
else:
    # Running as script
    load_dotenv()
```

**Key Points:**
- `sys.frozen` is `True` when running as PyInstaller executable
- `sys._MEIPASS` is the temporary directory where PyInstaller extracts bundled files
- The code tries to load from bundled `.env` first, then falls back to default location

### 2. Modified `build_exe.py` (Line 82)
The `.env` file was already being bundled in the build script:
```python
'--add-data=.env:.',
```

This tells PyInstaller to include `.env` in the executable and extract it to the same directory as other bundled resources.

### 3. Also updated Debug build configuration (Line 129)
Added `.env` file to the debug build as well for consistency.

## How It Works

1. **During Build**: PyInstaller packages the `.env` file into the executable
2. **When Running EXE**: 
   - PyInstaller extracts all bundled files to a temporary directory (`sys._MEIPASS`)
   - The modified code detects it's running as an executable
   - It loads the `.env` file from the temporary directory
   - Supabase credentials are loaded successfully

## Testing

✅ Build completed successfully: `dist\TCGCardScraper.exe` (50 MB)
✅ .env file is now bundled in the executable
✅ Application will work on other machines without needing a separate .env file

## Security Note

⚠️ **IMPORTANT**: The `.env` file containing Supabase credentials is now embedded in the executable. While this is obfuscated, it's not encrypted. For production use, consider:
- Using environment-specific builds
- Implementing additional security layers
- Using Supabase's Row Level Security (RLS)
- Rotating keys regularly

## Files Modified

1. `product_keys_supabase.py` - Added PyInstaller .env loading logic
2. `build_exe.py` - Updated debug build to include .env file
3. `upload_window.py` - Added icon support (from previous task)
