# #!/usr/bin/env python3
# """
# Build script to create standalone executable for TCG Card Scraper Pro
# Supports Windows EXE and Linux ELF builds
# """

# import PyInstaller.__main__
# import os
# import sys
# import shutil
# import platform


# def clean_build():
#     """Clean previous build directories"""
#     dirs_to_remove = ['build', 'dist', '__pycache__']
#     files_to_remove = ['TCGCardScraper.spec', '*.pyc']
    
#     print("🧹 Cleaning previous builds...")
    
#     for dir_name in dirs_to_remove:
#         if os.path.exists(dir_name):
#             try:
#                 shutil.rmtree(dir_name)
#                 print(f"   ✓ Removed {dir_name}/")
#             except Exception as e:
#                 print(f"   ⚠ Could not remove {dir_name}/: {e}")
    
#     for pattern in files_to_remove:
#         import glob
#         for file in glob.glob(pattern):
#             try:
#                 os.remove(file)
#                 print(f"   ✓ Removed {file}")
#             except Exception as e:
#                 print(f"   ⚠ Could not remove {file}: {e}")


# def get_platform_config():
#     """Get platform-specific configuration"""
#     system = platform.system().lower()
    
#     if system == 'windows':
#         return {
#             'extension': '.exe',
#             'name_suffix': '',
#             'windowed': True,
#             'platform_name': 'Windows'
#         }
#     elif system == 'linux':
#         return {
#             'extension': '',
#             'name_suffix': '_Linux',
#             'windowed': False,  # Linux GUI apps typically run without console
#             'platform_name': 'Linux'
#         }
#     else:
#         # Fallback for other Unix-like systems
#         return {
#             'extension': '',
#             'name_suffix': '_Unix',
#             'windowed': False,
#             'platform_name': system.capitalize()
#         }


# def get_common_args():
#     """Get common PyInstaller arguments"""
#     args = [
#         'main-gui-tkinter.py',           # Main script
#         '--onefile',                      # Single executable file
#         '--noconfirm',                    # Overwrite without asking
#         '--clean',                        # Clean temporary files
        
#         # Hidden imports (add if PyInstaller misses any)
#         '--hidden-import=tkinter',
#         '--hidden-import=tkinter.ttk',
#         '--hidden-import=tkinter.filedialog',
#         '--hidden-import=tkinter.messagebox',
#         '--hidden-import=tkinter.scrolledtext',
#         '--hidden-import=tkinter.simpledialog',
#         '--hidden-import=product_keys',
#         '--hidden-import=product_keys_supabase',
#         '--hidden-import=json',
#         '--hidden-import=hashlib',
#         '--hidden-import=requests',
#         '--hidden-import=PIL',
#         '--hidden-import=openpyxl',
#         '--hidden-import=pandas',
        
#         # Hidden imports for web-upload-bulk modules
#         '--hidden-import=uploaders',
#         '--hidden-import=uploaders.playwright_uploader',
#         '--hidden-import=uploaders.selenium_uploader',
#         '--hidden-import=utils',
#         '--hidden-import=utils.config',
#         '--hidden-import=utils.excel_reader',
        
#         # Add web-upload-bulk directory and its contents
#         '--add-data=web-upload-bulk;web-upload-bulk',
        
#         # Collect all submodules from web-upload-bulk
#         '--collect-all=uploaders',
#         '--collect-all=utils',
#     ]
    
#     # Only add --strip on Linux (Windows doesn't have strip command by default)
#     system = platform.system().lower()
#     if system == 'linux':
#         args.append('--strip')
    
#     return args


# def build_exe():
#     """Build the standalone executable for the current platform"""
    
#     config = get_platform_config()
    
#     print("\n" + "=" * 60)
#     print(f"🔨 Building TCG Card Scraper Pro - {config['platform_name']} Application")
#     print("=" * 60 + "\n")
    
#     # Clean previous builds
#     clean_build()
    
#     # Base name
#     base_name = f"TCGCardScraper{config['name_suffix']}"
    
#     # PyInstaller arguments
#     pyinstaller_args = get_common_args()
    
#     # Add platform-specific arguments
#     pyinstaller_args.append(f'--name={base_name}')
    
#     if config['windowed']:
#         pyinstaller_args.append('--windowed')  # No console (Windows GUI)
#     else:
#         # For Linux, we typically want the console output for debugging
#         # Remove '--windowed' to keep console
#         pass
    
#     # Platform-specific notes
#     if config['platform_name'] == 'Linux':
#         print("🐧 Linux build detected - creating ELF executable")
#         print("   Note: Linux GUI apps may need X11 or Wayland libraries")
#         print("   The executable will include console output for debugging\n")
    
#     print(f"📦 Running PyInstaller for {config['platform_name']}...")
#     print(f"   Output name: {base_name}{config['extension']}")
#     print(f"   Arguments: {' '.join(pyinstaller_args)}\n")
    
#     try:
#         PyInstaller.__main__.run(pyinstaller_args)
        
#         # Output location
#         output_path = os.path.abspath(f'dist/{base_name}{config["extension"]}')
        
#         print("\n" + "=" * 60)
#         print("✅ Build completed successfully!")
#         print("=" * 60)
#         print(f"\n📁 Output location: {output_path}")
        
#         # Make Linux executable executable
#         if config['platform_name'] == 'Linux':
#             try:
#                 os.chmod(output_path, 0o755)
#                 print("🔧 Made executable executable (chmod +x)")
#             except Exception as e:
#                 print(f"⚠ Could not set executable permission: {e}")
        
#         print(f"\n🚀 You can now distribute the {config['platform_name']} executable!")
#         print(f"   Run with: ./{base_name}{config['extension']}")
#         return True
        
#     except Exception as e:
#         print("\n" + "=" * 60)
#         print("❌ Build failed!")
#         print("=" * 60)
#         print(f"\nError: {str(e)}")
#         return False


# def build_debug():
#     """Build version with console for debugging"""
    
#     config = get_platform_config()
    
#     print("\n" + "=" * 60)
#     print(f"🔨 Building DEBUG version (with console) - {config['platform_name']}")
#     print("=" * 60 + "\n")
    
#     clean_build()
    
#     base_name = f"TCGCardScraper_Debug{config['name_suffix']}"
    
#     pyinstaller_args = get_common_args()
#     pyinstaller_args.append(f'--name={base_name}')
#     # Don't use --windowed - this keeps console visible for debugging
    
#     print(f"📦 Running PyInstaller (DEBUG mode) for {config['platform_name']}...")
    
#     try:
#         PyInstaller.__main__.run(pyinstaller_args)
        
#         output_path = os.path.abspath(f'dist/{base_name}{config["extension"]}')
#         print("\n✅ Debug build completed!")
#         print(f"📁 Output: {output_path}")
        
#         if config['platform_name'] == 'Linux':
#             try:
#                 os.chmod(output_path, 0o755)
#                 print("🔧 Made executable executable (chmod +x)")
#             except Exception as e:
#                 print(f"⚠ Could not set executable permission: {e}")
        
#         return True
#     except Exception as e:
#         print(f"\n❌ Build failed: {e}")
#         return False


# def build_for_platform(target_platform=None):
#     """Build for a specific platform (cross-compilation hint)"""
    
#     current_platform = platform.system().lower()
    
#     if target_platform and target_platform != current_platform:
#         print("⚠ Note: Cross-compilation is not directly supported by PyInstaller.")
#         print(f"   You're on {current_platform} but trying to build for {target_platform}.")
#         print("   For cross-platform builds, consider using Docker or a VM.")
#         print("   Or run this script on the target platform.\n")
#         return False
    
#     return build_exe()


# if __name__ == '__main__':
#     import argparse
    
#     parser = argparse.ArgumentParser(
#         description='Build TCG Card Scraper executable for current platform',
#         epilog='Supported platforms: Windows, Linux (auto-detected)'
#     )
#     parser.add_argument('--debug', action='store_true', 
#                        help='Build with console for debugging')
#     parser.add_argument('--clean-only', action='store_true',
#                        help='Only clean build directories')
#     parser.add_argument('--platform', choices=['windows', 'linux'],
#                        help='Target platform (default: auto-detect)')
#     parser.add_argument('--info', action='store_true',
#                        help='Show current platform information')
    
#     args = parser.parse_args()
    
#     # Show platform info
#     if args.info:
#         print(f"Current Platform: {platform.system()}")
#         print(f"Platform Details: {platform.platform()}")
#         print(f"Python Version: {sys.version}")
#         print(f"Architecture: {platform.architecture()}")
#         print(f"Machine: {platform.machine()}")
#         sys.exit(0)
    
#     # Handle actions
#     if args.clean_only:
#         clean_build()
#     elif args.platform:
#         # Try to build for specified platform
#         current = platform.system().lower()
#         if args.platform != current:
#             print(f"⚠ Warning: Building for {args.platform} while running on {current}")
#             print("   This may not work correctly. Running anyway...\n")
        
#         # Override platform for build
#         original_system = platform.system
        
#         def mock_system():
#             return args.platform.capitalize()
        
#         if args.platform != current:
#             # Monkey patch platform.system() for the build
#             import platform as plt
#             plt.system = mock_system
        
#         if args.debug:
#             success = build_debug()
#         else:
#             success = build_exe()
        
#         # Restore original if it was monkey-patched
#         if args.platform != current:
#             import platform as plt
#             plt.system = original_system
            
#         sys.exit(0 if success else 1)
#     else:
#         # Auto-detect and build for current platform
#         if args.debug:
#             success = build_debug()
#         else:
#             success = build_exe()
#         sys.exit(0 if success else 1)



#!/usr/bin/env python3
"""
Build script to create standalone executable for TCG Card Scraper Pro
Supports Windows EXE and Linux ELF builds
"""

import PyInstaller.__main__
import os
import sys
import shutil
import platform
import glob


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
        for file in glob.glob(pattern):
            try:
                os.remove(file)
                print(f"   ✓ Removed {file}")
            except Exception as e:
                print(f"   ⚠ Could not remove {file}: {e}")


def check_icon():
    """Check if icon file exists and is valid"""
    icon_path = 'icon.png'
    if os.path.exists(icon_path):
        print(f"   ✓ Found icon: {icon_path}")
        return icon_path
    else:
        print(f"   ⚠ Warning: icon.png not found in root directory")
        return None


def get_platform_config():
    """Get platform-specific configuration"""
    system = platform.system().lower()
    
    if system == 'windows':
        return {
            'extension': '.exe',
            'name_suffix': '',
            'windowed': True,
            'platform_name': 'Windows',
            'icon_arg': '--icon=icon.png'  # PyInstaller supports PNG on Windows
        }
    elif system == 'linux':
        return {
            'extension': '',
            'name_suffix': '_Linux',
            'windowed': False,
            'platform_name': 'Linux',
            'icon_arg': ''  # Linux doesn't use icon in the same way
        }
    else:
        return {
            'extension': '',
            'name_suffix': '_Unix',
            'windowed': False,
            'platform_name': system.capitalize(),
            'icon_arg': ''
        }


def get_common_args(use_icon=True, version_file='version.txt'):
    """Get common PyInstaller arguments"""
    args = [
        'main-gui-tkinter.py',           # Main script
        '--onefile',                      # Single executable file
        '--noconfirm',                    # Overwrite without asking
        '--clean',                        # Clean temporary files
        
        # Add web-upload-bulk to Python path so PyInstaller can find the modules
        '--paths=web-upload-bulk',
        
        # Hidden imports (add if PyInstaller misses any)
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=tkinter.filedialog',
        '--hidden-import=tkinter.messagebox',
        '--hidden-import=tkinter.scrolledtext',
        '--hidden-import=tkinter.simpledialog',
        '--hidden-import=product_keys',
        '--hidden-import=product_keys_supabase',
        '--hidden-import=json',
        '--hidden-import=hashlib',
        '--hidden-import=requests',
        '--hidden-import=PIL',
        '--hidden-import=openpyxl',
        '--hidden-import=pandas',
        
        # Hidden imports for web-upload-bulk modules
        # Now PyInstaller can find them because we added web-upload-bulk to paths
        '--hidden-import=uploaders',
        '--hidden-import=uploaders.playwright_uploader',
        '--hidden-import=uploaders.selenium_uploader',
        '--hidden-import=uploaders.__init__',
        '--hidden-import=utils',
        '--hidden-import=utils.config',
        '--hidden-import=utils.excel_reader',
        '--hidden-import=utils.__init__',
        
        # Hidden imports for Selenium and Playwright dependencies
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
        
        # Add web-upload-bulk directory and its contents
        '--add-data=web-upload-bulk;web-upload-bulk',
        
        # Collect all submodules from web-upload-bulk and dependencies
        '--collect-all=uploaders',
        '--collect-all=utils',
        '--collect-all=selenium',
        '--collect-all=playwright',
    ]
    
    # Add icon if available and on Windows
    if use_icon and platform.system().lower() == 'windows':
        icon_path = check_icon()
        if icon_path:
            args.append(f'--icon={icon_path}')
            print(f"   ✓ Added icon: {icon_path}")
    
    # Add version file if it exists
    if os.path.exists(version_file):
        args.append(f'--version-file={version_file}')
        print(f"   ✓ Added version info: {version_file}")
    else:
        print(f"   ⚠ Warning: {version_file} not found - skipping version info")
    
    # Only add --strip on Linux (Windows doesn't have strip command by default)
    system = platform.system().lower()
    if system == 'linux':
        args.append('--strip')
    
    return args


def build_exe():
    """Build the standalone executable for the current platform"""
    
    config = get_platform_config()
    
    print("\n" + "=" * 60)
    print(f"🔨 Building TCG Card Scraper Pro - {config['platform_name']} Application")
    print("=" * 60 + "\n")
    
    # Clean previous builds
    clean_build()
    
    # Base name
    base_name = f"TCGCardScraper{config['name_suffix']}"
    
    # PyInstaller arguments
    pyinstaller_args = get_common_args()
    
    # Add platform-specific arguments
    pyinstaller_args.append(f'--name={base_name}')
    
    if config['windowed']:
        pyinstaller_args.append('--windowed')  # No console (Windows GUI)
    else:
        # For Linux, we typically want the console output for debugging
        # Remove '--windowed' to keep console
        pass
    
    # Platform-specific notes
    if config['platform_name'] == 'Linux':
        print("\n🐧 Linux build detected - creating ELF executable")
        print("   Note: Linux GUI apps may need X11 or Wayland libraries")
        print("   The executable will include console output for debugging\n")
    
    print(f"\n📦 Running PyInstaller for {config['platform_name']}...")
    print(f"   Output name: {base_name}{config['extension']}")
    print(f"   Arguments: {' '.join(pyinstaller_args)}\n")
    
    try:
        PyInstaller.__main__.run(pyinstaller_args)
        
        # Output location
        output_path = os.path.abspath(f'dist/{base_name}{config["extension"]}')
        
        print("\n" + "=" * 60)
        print("✅ Build completed successfully!")
        print("=" * 60)
        print(f"\n📁 Output location: {output_path}")
        
        # Make Linux executable executable
        if config['platform_name'] == 'Linux':
            try:
                os.chmod(output_path, 0o755)
                print("🔧 Made executable executable (chmod +x)")
            except Exception as e:
                print(f"⚠ Could not set executable permission: {e}")
        
        # Additional info for Windows
        if config['platform_name'] == 'Windows':
            print("\n💡 Windows Build Info:")
            print("   - Icon embedded: icon.png")
            print("   - Version info embedded: version.txt")
            print("   - The executable should now have proper file properties")
            print("   - Right-click the .exe → Properties → Details to verify")
        
        print(f"\n🚀 You can now distribute the {config['platform_name']} executable!")
        print(f"   Run with: ./{base_name}{config['extension']}")
        return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ Build failed!")
        print("=" * 60)
        print(f"\nError: {str(e)}")
        return False


def build_debug():
    """Build version with console for debugging"""
    
    config = get_platform_config()
    
    print("\n" + "=" * 60)
    print(f"🔨 Building DEBUG version (with console) - {config['platform_name']}")
    print("=" * 60 + "\n")
    
    clean_build()
    
    base_name = f"TCGCardScraper_Debug{config['name_suffix']}"
    
    pyinstaller_args = get_common_args()
    pyinstaller_args.append(f'--name={base_name}')
    # Don't use --windowed - this keeps console visible for debugging
    
    print(f"📦 Running PyInstaller (DEBUG mode) for {config['platform_name']}...")
    
    try:
        PyInstaller.__main__.run(pyinstaller_args)
        
        output_path = os.path.abspath(f'dist/{base_name}{config["extension"]}')
        print("\n✅ Debug build completed!")
        print(f"📁 Output: {output_path}")
        
        if config['platform_name'] == 'Linux':
            try:
                os.chmod(output_path, 0o755)
                print("🔧 Made executable executable (chmod +x)")
            except Exception as e:
                print(f"⚠ Could not set executable permission: {e}")
        
        return True
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        return False


def build_for_platform(target_platform=None):
    """Build for a specific platform (cross-compilation hint)"""
    
    current_platform = platform.system().lower()
    
    if target_platform and target_platform != current_platform:
        print("⚠ Note: Cross-compilation is not directly supported by PyInstaller.")
        print(f"   You're on {current_platform} but trying to build for {target_platform}.")
        print("   For cross-platform builds, consider using Docker or a VM.")
        print("   Or run this script on the target platform.\n")
        return False
    
    return build_exe()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Build TCG Card Scraper executable for current platform',
        epilog='Supported platforms: Windows, Linux (auto-detected)'
    )
    parser.add_argument('--debug', action='store_true', 
                       help='Build with console for debugging')
    parser.add_argument('--clean-only', action='store_true',
                       help='Only clean build directories')
    parser.add_argument('--platform', choices=['windows', 'linux'],
                       help='Target platform (default: auto-detect)')
    parser.add_argument('--info', action='store_true',
                       help='Show current platform information')
    parser.add_argument('--no-icon', action='store_true',
                       help='Build without icon (overrides default)')
    
    args = parser.parse_args()
    
    # Show platform info
    if args.info:
        print(f"Current Platform: {platform.system()}")
        print(f"Platform Details: {platform.platform()}")
        print(f"Python Version: {sys.version}")
        print(f"Architecture: {platform.architecture()}")
        print(f"Machine: {platform.machine()}")
        sys.exit(0)
    
    # Handle actions
    if args.clean_only:
        clean_build()
    elif args.platform:
        # Try to build for specified platform
        current = platform.system().lower()
        if args.platform != current:
            print(f"⚠ Warning: Building for {args.platform} while running on {current}")
            print("   This may not work correctly. Running anyway...\n")
        
        # Override platform for build
        original_system = platform.system
        
        def mock_system():
            return args.platform.capitalize()
        
        if args.platform != current:
            # Monkey patch platform.system() for the build
            import platform as plt
            plt.system = mock_system
        
        if args.debug:
            success = build_debug()
        else:
            success = build_exe()
        
        # Restore original if it was monkey-patched
        if args.platform != current:
            import platform as plt
            plt.system = original_system
            
        sys.exit(0 if success else 1)
    else:
        # Auto-detect and build for current platform
        if args.debug:
            success = build_debug()
        else:
            success = build_exe()
        sys.exit(0 if success else 1)