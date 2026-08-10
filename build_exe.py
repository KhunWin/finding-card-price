#!/usr/bin/env python3
"""
Build script to create standalone EXE for TCG Card Scraper Pro
"""

import PyInstaller.__main__
import os
import sys
import shutil


def clean_build():
    """Clean previous build directories"""
    dirs_to_remove = ['build', 'dist', '__pycache__']
    files_to_remove = ['TCGCardScraper.spec', '*.pyc']
    
    print("🧹 Cleaning previous builds...")
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"   ✓ Removed {dir_name}/")
            except Exception as e:
                print(f"   ⚠ Could not remove {dir_name}/: {e}")
    
    for pattern in files_to_remove:
        import glob
        for file in glob.glob(pattern):
            try:
                os.remove(file)
                print(f"   ✓ Removed {file}")
            except Exception as e:
                print(f"   ⚠ Could not remove {file}: {e}")


def build_exe():
    """Build the standalone EXE"""
    
    print("\n" + "=" * 60)
    print("🔨 Building TCG Card Scraper Pro - Standalone EXE")
    print("=" * 60 + "\n")
    
    # Clean previous builds
    clean_build()
    
    # PyInstaller arguments
    pyinstaller_args = [
        'main-gui-tkinter.py',           # Main script
        '--name=TCGCardScraper',          # EXE name
        '--onefile',                       # Single EXE file
        '--windowed',                      # No console window (GUI app)
        '--noconfirm',                     # Overwrite without asking
        
        # Icon
        '--icon=icon.ico',
        
        # Add data files
        '--add-data=icon.ico:.',
        
        # Add data files if needed
        # '--add-data=main_tcg_extract.py;.',
        
        # Hidden imports (add if PyInstaller misses any)
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=tkinter.filedialog',
        '--hidden-import=tkinter.messagebox',
        '--hidden-import=tkinter.scrolledtext',
        '--hidden-import=tkinter.simpledialog',
        '--hidden-import=product_keys',
        '--hidden-import=product_keys_supabase',
        '--hidden-import=supabase',
        '--hidden-import=dotenv',
        '--hidden-import=json',
        '--hidden-import=hashlib',
        '--hidden-import=uuid',
        '--hidden-import=platform',
        '--hidden-import=datetime',
        
        # Add .env file as data
        '--add-data=.env:.',
        
        # Optimize
        '--strip',                         # Strip symbols
        '--noupx',                         # Don't use UPX (can cause issues)
        
        # Clean temporary files
        '--clean',
    ]
    
    print("📦 Running PyInstaller...")
    print(f"   Arguments: {' '.join(pyinstaller_args)}\n")
    
    try:
        PyInstaller.__main__.run(pyinstaller_args)
        print("\n" + "=" * 60)
        print("✅ Build completed successfully!")
        print("=" * 60)
        print(f"\n📁 Output location: {os.path.abspath('dist/TCGCardScraper.exe')}")
        print("\n🚀 You can now distribute the EXE file!")
        return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ Build failed!")
        print("=" * 60)
        print(f"\nError: {str(e)}")
        return False


def build_with_console():
    """Build version with console for debugging"""
    
    print("\n" + "=" * 60)
    print("🔨 Building DEBUG version (with console)")
    print("=" * 60 + "\n")
    
    clean_build()
    
    pyinstaller_args = [
        'main-gui-tkinter.py',
        '--name=TCGCardScraper_Debug',
        '--onefile',
        # '--windowed',  # REMOVED - shows console for debugging
        '--noconfirm',
        '--icon=icon.ico',
        '--add-data=icon.ico:.',
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=tkinter.filedialog',
        '--hidden-import=tkinter.messagebox',
        '--hidden-import=tkinter.scrolledtext',
        '--clean',
    ]
    
    print("📦 Running PyInstaller (DEBUG mode)...")
    
    try:
        PyInstaller.__main__.run(pyinstaller_args)
        print("\n✅ Debug build completed!")
        print(f"📁 Output: {os.path.abspath('dist/TCGCardScraper_Debug.exe')}")
        return True
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Build TCG Card Scraper EXE')
    parser.add_argument('--debug', action='store_true', help='Build with console for debugging')
    parser.add_argument('--clean-only', action='store_true', help='Only clean build directories')
    
    args = parser.parse_args()
    
    if args.clean_only:
        clean_build()
    elif args.debug:
        build_with_console()
    else:
        build_exe()