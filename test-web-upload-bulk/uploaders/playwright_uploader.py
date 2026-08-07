from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
import time
import logging
from pathlib import Path
import pandas as pd
from utils.config import Config
from utils.excel_reader import ExcelReader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlaywrightUploader:
    def __init__(self, headless=False):  # Changed default to False for debugging
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
    def setup_browser(self):
        """Initialize Playwright browser"""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox', 
                    '--disable-dev-shm-usage', 
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials'
                ]
            )
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['geolocation'],
                device_scale_factor=1,
                has_touch=False,
                is_mobile=False
            )
            self.page = self.context.new_page()
            self.page.set_default_timeout(Config.TIMEOUT * 1000)  # Convert to milliseconds
            logger.info("Playwright browser initialized")
            
        except PlaywrightError as e:
            logger.error(f"Failed to initialize Playwright: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in setup_browser: {e}")
            raise
    
    def login(self):
        """Login to Boutir with improved selectors"""
        try:
            logger.info("Attempting to login...")
            
            # Navigate to the correct login page
            login_url = f"{Config.BOUTIR_URL}/business/en/login"
            logger.info(f"Navigating to login page: {login_url}")
            self.page.goto(login_url, wait_until='networkidle')
            logger.info(f"Navigated to login page, current URL: {self.page.url}")
            
            # Wait for page to fully load and take screenshot for debugging
            time.sleep(2)
            self.page.screenshot(path='login_page_debug.png')
            logger.info("Debug screenshot saved as 'login_page_debug.png'")
            
            # Log the page title and URL for debugging
            page_title = self.page.title()
            page_url = self.page.url
            logger.info(f"Page Title: {page_title}")
            logger.info(f"Page URL: {page_url}")
            
            # Try multiple login form selectors
            selectors = [
                # Email/Username field selectors
                'input[type="email"]',
                'input[name="email"]',
                'input[name="username"]',
                'input[id*="email" i]',
                'input[placeholder*="email" i]',
                'input[placeholder*="電郵" i]',
                'input[autocomplete="email"]',
                'input[autocomplete="username"]',
                'input[type="text"][placeholder*="email" i]',
                'input[type="text"][placeholder*="帳號" i]',
                'input[placeholder="Email"]',
                'input[placeholder="電子郵件"]',
                # Catch-all for text inputs that might be email
                'input[type="text"]:first-of-type',
                'input:not([type="hidden"]):first-of-type'
            ]
            
            # Try each selector for email field
            email_input = None
            for selector in selectors:
                try:
                    email_input = self.page.locator(selector).first
                    if email_input.count() > 0 and email_input.is_visible():
                        logger.info(f"Found email input with selector: {selector}")
                        break
                except:
                    continue
            
            if email_input is None:
                # Try to find any visible text input
                all_inputs = self.page.locator('input[type="text"], input[type="email"], input:not([type])').all()
                for inp in all_inputs:
                    if inp.is_visible():
                        email_input = inp
                        logger.info("Found visible text input as fallback")
                        break
            
            if email_input is None:
                # If still not found, try to find any input on the page
                all_inputs = self.page.locator('input').all()
                if all_inputs:
                    email_input = all_inputs[0]
                    logger.info("Using first input on page as fallback")
                else:
                    raise Exception("No input fields found on page")
            
            # Fill email
            email_input.fill(Config.BOUTIR_EMAIL)
            logger.info("Email filled")
            
            # Wait a moment
            time.sleep(1)
            
            # Find password field
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[placeholder*="password" i]',
                'input[placeholder*="密碼" i]',
                'input[autocomplete="current-password"]',
                'input:not([type="text"]):not([type="email"]):not([type="hidden"])'
            ]
            
            password_input = None
            for selector in password_selectors:
                try:
                    password_input = self.page.locator(selector).first
                    if password_input.count() > 0 and password_input.is_visible():
                        logger.info(f"Found password input with selector: {selector}")
                        break
                except:
                    continue
            
            if password_input is None:
                # Find any input after email
                all_inputs = self.page.locator('input').all()
                for inp in all_inputs:
                    if inp.is_visible() and inp != email_input:
                        password_input = inp
                        logger.info("Using second visible input as password field")
                        break
            
            if password_input is None:
                raise Exception("No password field found")
            
            # Fill password
            password_input.fill(Config.BOUTIR_PASSWORD)
            logger.info("Password filled")
            
            # Take screenshot after filling credentials
            self.page.screenshot(path='login_filled.png')
            logger.info("Screenshot saved as 'login_filled.png'")
            
            # Wait a moment
            time.sleep(1)
            
            # Find login button
            login_button_selectors = [
                'button[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign in")',
                'button:has-text("登入")',
                'button:has-text("Sign In")',
                'input[type="submit"]',
                'button[class*="login" i]',
                'button[class*="signin" i]',
                'button[class*="submit" i]',
                'button:has-text("Log in")',
                'button:has-text("Sign In")',
                'a:has-text("Login")',
                'a:has-text("Sign in")'
            ]
            
            login_button = None
            for selector in login_button_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.count() > 0 and btn.is_visible():
                        login_button = btn
                        logger.info(f"Found login button with selector: {selector}")
                        break
                except:
                    continue
            
            if login_button is None:
                # Try to find any button on the page
                buttons = self.page.locator('button').all()
                for btn in buttons:
                    if btn.is_visible() and btn.inner_text().strip():
                        login_button = btn
                        logger.info(f"Using fallback button with text: {btn.inner_text().strip()}")
                        break
            
            if login_button is None:
                raise Exception("No login button found")
            
            # Click login button
            login_button.click()
            logger.info("Login button clicked")
            
            # Wait for navigation to complete
            time.sleep(3)
            
            # Check if login was successful
            current_url = self.page.url
            logger.info(f"Current URL after login: {current_url}")
            
            # Take screenshot after login attempt
            self.page.screenshot(path='login_attempt.png')
            logger.info("Screenshot saved as 'login_attempt.png'")
            
            # Check for error messages
            error_selectors = [
                'div[class*="error" i]',
                'span[class*="error" i]',
                'div[class*="alert" i]',
                'div:has-text("Invalid")',
                'div:has-text("incorrect")',
                'div:has-text("wrong")'
            ]
            
            for selector in error_selectors:
                try:
                    error_element = self.page.locator(selector).first
                    if error_element.count() > 0 and error_element.is_visible():
                        error_text = error_element.inner_text()
                        logger.error(f"Login error detected: {error_text}")
                        raise Exception(f"Login failed: {error_text}")
                except:
                    continue
            
            # Check if we're on dashboard or got redirected
            if 'dashboard' in current_url.lower() or 'admin' in current_url.lower():
                logger.info("Successfully logged in - redirected to dashboard")
            else:
                # Check for success indicators
                success_indicators = [
                    'div[class*="dashboard" i]',
                    'div[class*="admin" i]',
                    'div[class*="welcome" i]',
                    'div:has-text("Dashboard")',
                    'div:has-text("Products")'
                ]
                
                for indicator in success_indicators:
                    try:
                        elem = self.page.locator(indicator).first
                        if elem.count() > 0 and elem.is_visible():
                            logger.info("Found dashboard indicator, login successful")
                            return
                    except:
                        continue
                
                # If we're still on login page, check for logged-in state
                if 'login' in current_url.lower():
                    # Try to find user menu or logout button
                    logged_in_indicators = [
                        'button:has-text("Logout")',
                        'button:has-text("Sign out")',
                        'div[class*="user" i]',
                        'img[alt*="user" i]'
                    ]
                    
                    for indicator in logged_in_indicators:
                        try:
                            elem = self.page.locator(indicator).first
                            if elem.count() > 0 and elem.is_visible():
                                logger.info("Found user indicator, login likely successful")
                                return
                        except:
                            continue
                    
                    # If we can't confirm login but no error, assume it might have worked
                    logger.warning("Could not confirm login status, but no errors detected")
            
            # Additional check for verification
            time.sleep(2)
            final_url = self.page.url
            logger.info(f"Final URL after login: {final_url}")
            
            if 'login' not in final_url.lower():
                logger.info("Login appears successful - redirected away from login page")
            else:
                # Check if we're on the business dashboard
                if '/business/en' in final_url:
                    logger.info("Successfully logged in - on business dashboard")
                else:
                    raise Exception(f"Login failed - unexpected URL: {final_url}")
            
            logger.info("Login process completed")
            
        except PlaywrightTimeoutError as e:
            logger.error(f"Login timeout: {e}")
            self.page.screenshot(path='login_timeout.png')
            raise
        except Exception as e:
            logger.error(f"Login failed: {e}")
            self.page.screenshot(path='login_error.png')
            raise
    
    def navigate_to_products(self):
        """Navigate to product list page and start import process"""
        try:
            # Navigate directly to the correct products page URL
            products_url = f"{Config.BOUTIR_URL}/business/en/products"
            logger.info(f"Navigating to products page: {products_url}")
            self.page.goto(products_url, wait_until='networkidle')
            time.sleep(3)
            
            # Log current URL to track navigation
            current_url = self.page.url
            logger.info(f"Current URL after navigation: {current_url}")
            
            # Check if we were redirected to login
            if 'login' in current_url.lower():
                logger.warning("Redirected to login page, attempting login...")
                self.login()
                # Try navigating to products page again
                logger.info(f"Navigating to products page again: {products_url}")
                self.page.goto(products_url, wait_until='networkidle')
                time.sleep(3)
                current_url = self.page.url
                logger.info(f"Current URL after re-navigation: {current_url}")
            
            # Take screenshot of products page
            self.page.screenshot(path='products_page.png')
            logger.info("Screenshot saved as 'products_page.png'")
            
            # DEBUG: List all buttons on the page
            logger.info("=== DEBUGGING: Listing all buttons on the page ===")
            try:
                all_buttons = self.page.locator('button').all()
                logger.info(f"Found {len(all_buttons)} buttons on the page")
                for i, btn in enumerate(all_buttons):
                    try:
                        if btn.is_visible():
                            text = btn.inner_text().strip()
                            classes = btn.get_attribute('class') or ''
                            aria_label = btn.get_attribute('aria-label') or ''
                            logger.info(f"Button {i+1}: text='{text}', class='{classes}', aria-label='{aria_label}'")
                    except Exception as e:
                        logger.debug(f"Could not get info for button {i+1}: {e}")
            except Exception as e:
                logger.error(f"Error listing buttons: {e}")
            
            # DEBUG: List all links/anchors
            logger.info("=== DEBUGGING: Listing all links/anchors ===")
            try:
                all_links = self.page.locator('a').all()
                logger.info(f"Found {len(all_links)} links on the page")
                for i, link in enumerate(all_links):
                    try:
                        if link.is_visible():
                            text = link.inner_text().strip()
                            href = link.get_attribute('href') or ''
                            classes = link.get_attribute('class') or ''
                            if text or 'import' in href.lower() or 'export' in href.lower():
                                logger.info(f"Link {i+1}: text='{text}', href='{href}', class='{classes}'")
                    except Exception as e:
                        logger.debug(f"Could not get info for link {i+1}: {e}")
            except Exception as e:
                logger.error(f"Error listing links: {e}")
            
            # DEBUG: List all divs with text containing 'import' or 'export'
            logger.info("=== DEBUGGING: Listing elements with 'import' or 'export' text ===")
            try:
                import_export_elements = self.page.locator('*:has-text("Import"), *:has-text("Export"), *:has-text("匯入"), *:has-text("匯出")').all()
                logger.info(f"Found {len(import_export_elements)} elements with import/export text")
                for i, elem in enumerate(import_export_elements[:20]):  # Limit to first 20
                    try:
                        if elem.is_visible():
                            tag = elem.evaluate('el => el.tagName')
                            text = elem.inner_text().strip()[:100]  # Limit text length
                            classes = elem.get_attribute('class') or ''
                            logger.info(f"Element {i+1}: tag='{tag}', text='{text}', class='{classes}'")
                    except Exception as e:
                        logger.debug(f"Could not get info for element {i+1}: {e}")
            except Exception as e:
                logger.error(f"Error listing import/export elements: {e}")
            
            logger.info("=== END DEBUGGING ===")
            
            # Step 1: Click 'Import / Export' button
            logger.info("Looking for 'Import / Export' button...")
            import_export_selectors = [
                'button:has-text("Import / Export")',
                'button:has-text("Import/Export")',
                'button:has-text("Import")',
                'button:has-text("匯入 / 匯出")',
                'button:has-text("匯入/匯出")',
                'button:has-text("匯入")'
            ]
            
            import_export_clicked = False
            for selector in import_export_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.count() > 0 and btn.is_visible():
                        btn.click()
                        logger.info(f"Clicked 'Import / Export' button using selector: {selector}")
                        import_export_clicked = True
                        time.sleep(1)
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not import_export_clicked:
                raise Exception("Could not find 'Import / Export' button")
            
            # Take screenshot after clicking Import/Export
            self.page.screenshot(path='import_export_clicked.png')
            logger.info("Screenshot saved as 'import_export_clicked.png'")
            
            # Step 2: Click 'Import / Update Excel' button
            logger.info("Looking for 'Import / Update Excel' button...")
            import_excel_selectors = [
                'button:has-text("Import / Update Excel")',
                'button:has-text("Import/Update Excel")',
                'button:has-text("Import Excel")',
                'button:has-text("Update Excel")',
                'text="Import / Update Excel"',
                'text="Import/Update Excel"',
                'text="Import Excel"',
                ':text("Import / Update Excel")',
                ':text("Import Excel")'
            ]
            
            import_excel_clicked = False
            for selector in import_excel_selectors:
                try:
                    elem = self.page.locator(selector).first
                    if elem.count() > 0 and elem.is_visible():
                        elem.click()
                        logger.info(f"Clicked 'Import / Update Excel' using selector: {selector}")
                        import_excel_clicked = True
                        time.sleep(2)
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not import_excel_clicked:
                raise Exception("Could not find 'Import / Update Excel' button")
            
            # Take screenshot after clicking Import/Update Excel
            self.page.screenshot(path='import_excel_clicked.png')
            logger.info("Screenshot saved as 'import_excel_clicked.png'")
            
            # Wait for navigation to batch upload page
            time.sleep(2)
            
            # Verify we're on the batch upload page
            current_url = self.page.url
            logger.info(f"Current URL: {current_url}")
            
            if 'batchUpload' not in current_url:
                logger.warning(f"Expected to be on batchUpload page, but URL is: {current_url}")
            else:
                logger.info("Successfully navigated to batch upload page")
            
            # Take screenshot of batch upload page
            self.page.screenshot(path='batch_upload_page.png')
            logger.info("Screenshot saved as 'batch_upload_page.png'")
            
        except Exception as e:
            logger.error(f"Navigation to products failed: {e}")
            self.page.screenshot(path='navigation_error.png')
            raise
    
    
    def upload_excel_file(self, file_path):
        """Upload Excel file with product data following the exact steps"""
        try:
            # Convert file_path to Path object if it's a string
            if isinstance(file_path, str):
                file_path = Path(file_path)
            
            # Verify the file exists
            if not file_path.exists():
                raise Exception(f"Excel file not found: {file_path}")
            
            logger.info(f"Using Excel file: {file_path}")
            logger.info(f"File size: {file_path.stat().st_size} bytes")
            
            # Step 3: Click first 'Next' button
            logger.info("Looking for first 'Next' button...")
            next_button_selectors = [
                'button:has-text("Next")',
                'button:has-text("下一步")',
                'button[type="button"]:has-text("Next")',
                'button[type="submit"]:has-text("Next")'
            ]
            
            next_clicked = False
            for selector in next_button_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.count() > 0 and btn.is_visible():
                        btn.click()
                        logger.info(f"Clicked first 'Next' button using selector: {selector}")
                        next_clicked = True
                        time.sleep(2)
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not next_clicked:
                raise Exception("Could not find first 'Next' button")
            
            # Take screenshot after clicking first Next
            # self.page.screenshot(path='first_next_clicked.png')
            logger.info("Screenshot saved as 'first_next_clicked.png'")
            
            # Step 4: Upload the Excel file directly
            logger.info("Looking for file upload area...")
            
            # Handle file upload
            try:
                # Wait for file input to be ready
                file_input = self.page.locator('input[type="file"]').first
                if file_input.count() == 0:
                    # Try to find file input with other selectors
                    file_input = self.page.locator('input[type="file"], input[accept*="xlsx"], input[accept*="xls"]').first
                
                if file_input.count() == 0:
                    raise Exception("File input element not found")
                
                # Upload the original file directly
                file_input.set_input_files(str(file_path))
                logger.info(f"Uploaded file: {file_path}")
                
            except PlaywrightError as e:
                logger.error(f"File upload failed: {e}")
                self.page.screenshot(path='upload_error.png')
                raise
            
            # Wait for file to be processed
            time.sleep(3)
            
            # Take screenshot after file upload
            # self.page.screenshot(path='file_uploaded.png')
            logger.info("Screenshot saved as 'file_uploaded.png'")
            
            # Step 5: Click second 'Next' button (after file upload)
            logger.info("Looking for second 'Next' button...")
            
            # Wait for the Next button to become enabled
            time.sleep(2)
            
            second_next_clicked = False
            for selector in next_button_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.count() > 0 and btn.is_visible() and btn.is_enabled():
                        btn.click()
                        logger.info(f"Clicked second 'Next' button using selector: {selector}")
                        second_next_clicked = True
                        time.sleep(2)
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not second_next_clicked:
                logger.warning("Could not find second 'Next' button, upload might complete automatically")
            
            # Take screenshot after clicking second Next
            # self.page.screenshot(path='second_next_clicked.png')
            logger.info("Screenshot saved as 'second_next_clicked.png'")
            
            # DEBUG: Check if there's a third 'Next' button
            logger.info("=== DEBUGGING: Checking for third 'Next' button ===")
            time.sleep(2)
            try:
                all_buttons = self.page.locator('button').all()
                logger.info(f"Found {len(all_buttons)} buttons on the page")
                for i, btn in enumerate(all_buttons):
                    try:
                        if btn.is_visible():
                            text = btn.inner_text().strip()
                            is_enabled = btn.is_enabled()
                            classes = btn.get_attribute('class') or ''
                            logger.info(f"Button {i+1}: text='{text}', enabled={is_enabled}, class='{classes[:100]}'")
                    except Exception as e:
                        logger.debug(f"Could not get info for button {i+1}: {e}")
            except Exception as e:
                logger.error(f"Error listing buttons: {e}")
            
            # Check for third Next button
            logger.info("Looking for third 'Next' button...")
            third_next_clicked = False
            for selector in next_button_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.count() > 0 and btn.is_visible() and btn.is_enabled():
                        logger.info(f"Found third 'Next' button with selector: {selector}")
                        btn.click()
                        logger.info("Clicked third 'Next' button")
                        third_next_clicked = True
                        time.sleep(3)
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if third_next_clicked:
                # Take screenshot after clicking third Next
                # self.page.screenshot(path='third_next_clicked.png')
                logger.info("Screenshot saved as 'third_next_clicked.png'")
                return True
            else:
                logger.info("No third 'Next' button found or it's disabled")
            
            # # Wait for completion
            # self.wait_for_upload_completion()
            
            logger.info(f"Excel file uploaded successfully: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            self.page.screenshot(path='upload_error.png')
            return False


    def create_formatted_excel(self, products):
        """Create properly formatted Excel file for Boutir"""
        try:
            temp_file = Config.UPLOAD_DIR / f'formatted_upload_{int(time.time())}.xlsx'
            
            # Convert products to DataFrame
            df = pd.DataFrame(products)
            
            # Ensure all columns exist
            for col, default_val in ExcelReader.DEFAULT_COLUMNS.items():
                if col not in df.columns:
                    df[col] = default_val
            
            # Reorder columns to match Boutir's expected format
            expected_columns = list(ExcelReader.DEFAULT_COLUMNS.keys())
            df = df[expected_columns]
            
            # Save to Excel
            df.to_excel(temp_file, index=False)
            logger.info(f"Created formatted Excel file with {len(df)} products")
            
            return temp_file
            
        except Exception as e:
            logger.error(f"Error creating formatted Excel: {e}")
            raise
    
    def wait_for_upload_completion(self):
        """Wait for upload process to complete"""
        try:
            # Wait for success message
            success_selectors = [
                'div:has-text("Success"), div:has-text("Complete"), div:has-text("成功")',
                'span:has-text("Success"), span:has-text("Complete"), span:has-text("成功")',
                '.success',
                '.complete',
                'div[class*="success" i]'
            ]
            
            for selector in success_selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=10000)
                    logger.info("Upload completed successfully")
                    return
                except PlaywrightTimeoutError:
                    continue
            
            # If no success message found, check for progress indicator
            try:
                progress_indicator = self.page.locator('progress, [class*="progress" i], [role="progressbar"]').first
                if progress_indicator.count() > 0:
                    # Wait for progress to complete
                    time.sleep(5)
                    logger.info("Upload process completed")
                    return
            except:
                pass
            
            # Wait for some time and assume it's done
            time.sleep(5)
            logger.info("Upload process completed (no confirmation message detected)")
            
        except Exception as e:
            logger.warning(f"Error waiting for completion: {e}")

    def run(self, excel_file):
        """`Main execution method"""
        try:
            # Validate Excel file exists
            excel_path = Path(excel_file)
            if not excel_path.exists():
                logger.error(f"Excel file not found: {excel_file}")
                return False
            
            logger.info(f"Starting upload of Excel file: {excel_file}")
            
            # Setup and execute upload
            self.setup_browser()
            
            # Step 1: Login to Boutir
            logger.info("=== STEP 1: Login ===")
            self.login()
            
            # Step 2: Navigate to products page
            logger.info("=== STEP 2: Navigate to Products Page ===")
            self.navigate_to_products()
            
            # Step 3: Upload the Excel file
            logger.info("=== STEP 3: Upload Excel File ===")
            success = self.upload_excel_file(excel_path)
            
            if success:
                logger.info("✅ Excel file uploaded successfully")
            else:
                logger.error("❌ Upload failed")
                
            return success
            
        except Exception as e:
            logger.error(f"Upload process failed: {e}")
            if self.page:
                try:
                    self.page.screenshot(path='process_error.png')
                except:
                    pass
            return False
            
        finally:
            try:
                if self.browser:
                    self.browser.close()
                if self.playwright:
                    self.playwright.stop()
                logger.info("Browser closed")
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")




