# Icon Implementation Summary

## Overview
Successfully added `icon.ico` support to the TCG Card Scraper application. The icon will now appear on:
- The application window title bar
- The taskbar when running
- The executable file itself

## Changes Made

### 1. Application Code (`main-gui-tkinter.py`)
Added icon support in the `main()` function with dual-mode handling:

```python
def main():
    root = tk.Tk()
    
    # Set application icon
    try:
        # Try to load from script directory (development mode)
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
        else:
            # When running as PyInstaller executable, try temp directory
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
                if os.path.exists(icon_path):
                    root.iconbitmap(icon_path)
    except Exception as e:
        # Icon setting failed, continue without icon
        print(f"Could not set icon: {e}")
    
    app = TCGScraperGUI(root)
    root.mainloop()
```

**Key Features:**
- ✅ Works in development mode (running from source)
- ✅ Works in compiled executable (PyInstaller)
- ✅ Gracefully handles missing icon files
- ✅ No crash if icon is not found

### 2. Build Script (`build_exe.py`)
Updated both the release and debug build configurations:

**Release Build:**
```python
'--icon=icon.ico',           # Embed icon in EXE
'--add-data=icon.ico:.',     # Include icon file in bundle
```

**Debug Build:**
```python
'--icon=icon.ico',           # Embed icon in EXE
'--add-data=icon.ico:.',     # Include icon file in bundle
```

### 3. Cross-Platform Build Script (`build_exe_linux_window.py`)
Updated to conditionally add icon for Windows builds:

```python
# Add icon if available and on Windows
if use_icon and platform.system().lower() == 'windows':
    icon_path = check_icon()
    if icon_path:
        args.append(f'--icon={icon_path}')
        args.append(f'--add-data={icon_path}:.')
        print(f"   ✓ Added icon: {icon_path}")
```

## How It Works

### Development Mode
When running `python main-gui-tkinter.py`:
1. Code looks for `icon.ico` in the script directory
2. If found, sets it as window icon using `root.iconbitmap()`

### Compiled Executable Mode
When running the built EXE:
1. PyInstaller embeds `icon.ico` in the EXE file (visible in Windows Explorer)
2. At runtime, PyInstaller extracts `icon.ico` to `sys._MEIPASS` (temp directory)
3. Code detects frozen state and loads icon from `sys._MEIPASS`
4. Window displays the icon

## PyInstaller Flags Explained

### `--icon=icon.ico`
- Embeds the icon **in the executable file itself**
- Makes the EXE display the icon in Windows Explorer, Desktop, etc.
- This is what you see before running the application

### `--add-data=icon.ico:.`
- Bundles the icon file **inside the executable**
- Extracted to temp directory at runtime
- Used by tkinter's `root.iconbitmap()` to set window icon
- This is what you see when the application is running

### Why Both Are Needed?
- `--icon`: For the **file** icon (Explorer, Desktop)
- `--add-data`: For the **window** icon (title bar, taskbar)

## File Location
Icon file must be at: `C:\Users\Win Khun Myint\Desktop\card-scrap\icon.ico`

## Testing

### Test Development Mode
```bash
python main-gui-tkinter.py
```
✅ Icon should appear in window title bar and taskbar

### Test Compiled EXE
```bash
python build_exe.py
```
Then run `dist/TCGCardScraper.exe`
✅ Icon should appear on:
- The EXE file in Windows Explorer
- Window title bar when running
- Taskbar when running

### Test Debug Build
```bash
python build_exe.py --debug
```
✅ Same as release build

## Troubleshooting

### Icon doesn't appear on window
- Check that `icon.ico` exists in the project root
- Verify the icon is a valid `.ico` file format
- Check console for error messages

### Icon doesn't appear on EXE file
- Verify `--icon=icon.ico` is in PyInstaller arguments
- Rebuild the executable
- Clear the `build/` and `dist/` folders first

### Error: "Could not set icon"
- Application will still run normally without the icon
- Check the error message in console (debug build)
- Verify icon file format and size

## Icon Requirements
- **Format:** Windows Icon (.ico)
- **Recommended sizes:** 16x16, 32x32, 48x48, 256x256 (multi-resolution ICO)
- **Location:** Project root directory
- **Name:** `icon.ico` (exactly)

## Cross-Platform Notes
- Icon support is **Windows-only** in current implementation
- Linux builds will skip icon embedding (as per platform detection)
- The application code handles missing icons gracefully on all platforms
