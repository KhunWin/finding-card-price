from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import logging
import tempfile
from pathlib import Path
import pandas as pd
import os
import platform
from utils.config import Config
from utils.excel_reader import ExcelReader
import subprocess
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SeleniumUploader:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Initialize Chrome driver with proper error handling"""
        try:
            options = Options()
            if self.headless:
                options.add_argument('--headless=new')
                options.add_argument('--window-size=1920,1080')
            
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Add user-agent to avoid detection
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Try to use Selenium Manager (built-in from Selenium 4.6+)
            try:
                self.driver = webdriver.Chrome(options=options)
                logger.info("Chrome driver initialized successfully using Selenium Manager")
            except WebDriverException as e:
                logger.warning(f"Selenium Manager failed, trying webdriver-manager: {e}")
                
                # Fallback to webdriver-manager
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=options)
                    logger.info("Chrome driver initialized using webdriver-manager")
                except Exception as wdm_error:
                    logger.error(f"webdriver-manager failed: {wdm_error}")
                    raise Exception(
                        "Failed to initialize ChromeDriver. Please install webdriver-manager:\n"
                        "pip install webdriver-manager\n"
                        "Or download ChromeDriver manually from https://chromedriver.chromium.org/"
                    )
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, Config.TIMEOUT)
            logger.info("Chrome driver setup completed")
            
        except Exception as e:
            logger.error(f"Chrome driver initialization failed: {e}")
            self.handle_driver_failure()
            raise
    
    def handle_driver_failure(self):
        """Provide user-friendly error message and instructions"""
        logger.error("=" * 80)
        logger.error("CHROMEDRIVER SETUP FAILED")
        logger.error("=" * 80)
        logger.error("")
        logger.error("Please try one of the following solutions:")
        logger.error("")
        logger.error("1. Install webdriver-manager (RECOMMENDED):")
        logger.error("   pip install webdriver-manager")
        logger.error("")
        logger.error("2. Install ChromeDriver manually:")
        logger.error("   - Visit: https://googlechromelabs.github.io/chrome-for-testing/")
        logger.error("   - Download the version matching your Chrome browser")
        logger.error("   - Place chromedriver in your PATH or the project directory")
        logger.error("")
        logger.error("3. Try using Playwright instead:")
        logger.error("   python main.py productTemplate-full.xlsx --method playwright")
        logger.error("")
        logger.error("=" * 80)
    
    def login(self):
        """Login to Boutir with improved selectors"""
        try:
            logger.info("Attempting to login...")
            
            # Navigate to the correct login page
            login_url = f"{Config.BOUTIR_URL}/business/en/login"
            logger.info(f"Navigating to login page: {login_url}")
            self.driver.get(login_url)
            time.sleep(2)
            
            
            # Log page info
            logger.info(f"Page Title: {self.driver.title}")
            logger.info(f"Page URL: {self.driver.current_url}")
            
            # Find email input with multiple selectors
            email_input = None
            email_selectors = [
                (By.CSS_SELECTOR, 'input[type="email"]'),
                (By.CSS_SELECTOR, 'input[name="email"]'),
                (By.CSS_SELECTOR, 'input[name="username"]'),
                (By.XPATH, '//input[@type="email" or @name="email" or @autocomplete="email"]'),
                (By.CSS_SELECTOR, 'input[type="text"]')
            ]
            
            for by, selector in email_selectors:
                try:
                    email_input = self.wait.until(EC.presence_of_element_located((by, selector)))
                    if email_input.is_displayed():
                        logger.info(f"Found email input with selector: {selector}")
                        break
                except (TimeoutException, NoSuchElementException):
                    continue
            
            if email_input is None:
                raise Exception("Email input field not found")
            
            # Fill email
            email_input.clear()
            email_input.send_keys(Config.BOUTIR_EMAIL)
            logger.info("Email filled")
            time.sleep(1)
            
            # Find password input
            password_input = None
            password_selectors = [
                (By.CSS_SELECTOR, 'input[type="password"]'),
                (By.CSS_SELECTOR, 'input[name="password"]'),
                (By.XPATH, '//input[@type="password"]')
            ]
            
            for by, selector in password_selectors:
                try:
                    password_input = self.driver.find_element(by, selector)
                    if password_input.is_displayed():
                        logger.info(f"Found password input with selector: {selector}")
                        break
                except NoSuchElementException:
                    continue
            
            if password_input is None:
                raise Exception("Password input field not found")
            
            # Fill password
            password_input.clear()
            password_input.send_keys(Config.BOUTIR_PASSWORD)
            logger.info("Password filled")
            
            time.sleep(1)
            
            # Find and click login button
            login_button = None
            login_button_selectors = [
                (By.XPATH, '//button[contains(text(), "Login") or contains(text(), "Sign in") or contains(text(), "登入")]'),
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.XPATH, '//button[@type="submit"]'),
                (By.XPATH, '//input[@type="submit"]')
            ]
            
            for by, selector in login_button_selectors:
                try:
                    login_button = self.driver.find_element(by, selector)
                    if login_button.is_displayed():
                        logger.info(f"Found login button with selector: {selector}")
                        break
                except NoSuchElementException:
                    continue
            
            if login_button is None:
                raise Exception("Login button not found")
            
            # Click login button
            login_button.click()
            logger.info("Login button clicked")
            time.sleep(3)
            
            # Check login success
            current_url = self.driver.current_url
            logger.info(f"Current URL after login: {current_url}")
            
            
            # Check for errors
            try:
                error_element = self.driver.find_element(By.XPATH, '//div[contains(@class, "error") or contains(text(), "Invalid") or contains(text(), "incorrect")]')
                if error_element.is_displayed():
                    error_text = error_element.text
                    logger.error(f"Login error detected: {error_text}")
                    raise Exception(f"Login failed: {error_text}")
            except NoSuchElementException:
                pass
            
            # Verify login success
            if 'dashboard' in current_url.lower() or 'admin' in current_url.lower():
                logger.info("Successfully logged in - redirected to dashboard")
            elif 'login' not in current_url.lower():
                logger.info("Login appears successful - redirected away from login page")
            else:
                logger.warning("Still on login page, but proceeding")
            
            logger.info("Login process completed")
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise
    
    def navigate_to_products(self):
        """Navigate to product list page and start import process"""
        try:
            # Navigate directly to products page
            products_url = f"{Config.BOUTIR_URL}/business/en/products"
            logger.info(f"Navigating to products page: {products_url}")
            self.driver.get(products_url)
            time.sleep(3)
            
            current_url = self.driver.current_url
            logger.info(f"Current URL after navigation: {current_url}")
            
            # Check if redirected to login
            if 'login' in current_url.lower():
                logger.warning("Redirected to login page, attempting login...")
                self.login()
                logger.info(f"Navigating to products page again: {products_url}")
                self.driver.get(products_url)
                time.sleep(3)
                current_url = self.driver.current_url
                logger.info(f"Current URL after re-navigation: {current_url}")
            
            
            # DEBUG: Log all buttons
            logger.info("=== DEBUGGING: Listing all buttons on the page ===")
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, 'button')
                logger.info(f"Found {len(buttons)} buttons on the page")
                for i, btn in enumerate(buttons):
                    try:
                        if btn.is_displayed():
                            text = btn.text.strip()
                            classes = btn.get_attribute('class') or ''
                            aria_label = btn.get_attribute('aria-label') or ''
                            logger.info(f"Button {i+1}: text='{text}', class='{classes[:50]}', aria-label='{aria_label}'")
                    except Exception as e:
                        logger.debug(f"Could not get info for button {i+1}: {e}")
            except Exception as e:
                logger.error(f"Error listing buttons: {e}")
            logger.info("=== END DEBUGGING ===")
            
            # Step 1: Click 'Import / Export' button
            logger.info("Looking for 'Import / Export' button...")
            import_export_clicked = False
            import_export_selectors = [
                (By.XPATH, '//button[contains(text(), "Import / Export")]'),
                (By.XPATH, '//button[contains(text(), "Import/Export")]'),
                (By.XPATH, '//button[contains(text(), "Import")]'),
                (By.XPATH, '//button[contains(text(), "匯入 / 匯出")]')
            ]
            
            for by, selector in import_export_selectors:
                try:
                    btn = self.driver.find_element(by, selector)
                    if btn.is_displayed():
                        btn.click()
                        logger.info(f"Clicked 'Import / Export' button using selector: {selector}")
                        import_export_clicked = True
                        time.sleep(1)
                        break
                except NoSuchElementException:
                    continue
            
            if not import_export_clicked:
                raise Exception("Could not find 'Import / Export' button")
            
            
            # Step 2: Click 'Import / Update Excel' button
            logger.info("Looking for 'Import / Update Excel' button...")
            import_excel_clicked = False
            import_excel_selectors = [
                (By.XPATH, '//button[contains(text(), "Import / Update Excel")]'),
                (By.XPATH, '//button[contains(text(), "Import/Update Excel")]'),
                (By.XPATH, '//button[contains(text(), "Import Excel")]'),
                (By.XPATH, '//*[contains(text(), "Import / Update Excel")]'),
                (By.XPATH, '//*[contains(text(), "Import Excel")]')
            ]
            
            for by, selector in import_excel_selectors:
                try:
                    elem = self.driver.find_element(by, selector)
                    if elem.is_displayed():
                        elem.click()
                        logger.info(f"Clicked 'Import / Update Excel' using selector: {selector}")
                        import_excel_clicked = True
                        time.sleep(2)
                        break
                except NoSuchElementException:
                    continue
            
            if not import_excel_clicked:
                raise Exception("Could not find 'Import / Update Excel' button")
            
            
            # Wait for navigation to batch upload page
            time.sleep(2)
            
            # Verify we're on batch upload page
            current_url = self.driver.current_url
            logger.info(f"Current URL: {current_url}")
            
            if 'batchUpload' not in current_url:
                logger.warning(f"Expected to be on batchUpload page, but URL is: {current_url}")
            else:
                logger.info("Successfully navigated to batch upload page")
            
            
        except Exception as e:
            logger.error(f"Navigation to products failed: {e}")
            raise
    
    def upload_excel_file(self, file_path):
        """Upload Excel file following the exact steps"""
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
                (By.XPATH, '//button[contains(text(), "Next")]'),
                (By.XPATH, '//button[contains(text(), "下一步")]'),
                (By.CSS_SELECTOR, 'button[type="button"]'),
                (By.CSS_SELECTOR, 'button[type="submit"]')
            ]
            
            next_clicked = False
            for by, selector in next_button_selectors:
                try:
                    btn = self.driver.find_element(by, selector)
                    if btn.is_displayed() and btn.is_enabled():
                        btn.click()
                        logger.info(f"Clicked first 'Next' button using selector: {selector}")
                        next_clicked = True
                        time.sleep(2)
                        break
                except NoSuchElementException:
                    continue
            
            if not next_clicked:
                raise Exception("Could not find first 'Next' button")
            
            
            # Step 4: Upload the Excel file
            logger.info("Looking for file upload area...")
            
            try:
                # Find file input
                file_input = None
                file_input_selectors = [
                    (By.CSS_SELECTOR, 'input[type="file"]'),
                    (By.CSS_SELECTOR, 'input[accept*="xlsx"]'),
                    (By.CSS_SELECTOR, 'input[accept*="xls"]')
                ]
                
                for by, selector in file_input_selectors:
                    try:
                        file_input = self.driver.find_element(by, selector)
                        logger.info(f"Found file input with selector: {selector}")
                        break
                    except NoSuchElementException:
                        continue
                
                if file_input is None:
                    raise Exception("File input element not found")
                
                # Upload file
                file_input.send_keys(str(file_path.absolute()))
                logger.info(f"Uploaded file: {file_path}")
                
            except Exception as e:
                logger.error(f"File upload failed: {e}")
                raise
            
            # Wait for file to be processed
            time.sleep(3)
            
            
            # Step 5: Click second 'Next' button
            logger.info("Looking for second 'Next' button...")
            time.sleep(2)
            
            second_next_clicked = False
            for by, selector in next_button_selectors:
                try:
                    btn = self.driver.find_element(by, selector)
                    if btn.is_displayed() and btn.is_enabled():
                        btn.click()
                        logger.info(f"Clicked second 'Next' button using selector: {selector}")
                        second_next_clicked = True
                        time.sleep(2)
                        break
                except NoSuchElementException:
                    continue
            
            if not second_next_clicked:
                logger.warning("Could not find second 'Next' button, upload might complete automatically")
            
            
            # Check for third Next button
            logger.info("Looking for third 'Next' button...")
            time.sleep(2)
            
            third_next_clicked = False
            for by, selector in next_button_selectors:
                try:
                    btn = self.driver.find_element(by, selector)
                    if btn.is_displayed() and btn.is_enabled():
                        logger.info(f"Found third 'Next' button with selector: {selector}")
                        btn.click()
                        logger.info("Clicked third 'Next' button")
                        third_next_clicked = True
                        time.sleep(3)
                        break
                except NoSuchElementException:
                    continue
            

            if third_next_clicked:
                logger.info("✅ Upload successful - third 'Next' button clicked")
                return True
            else:
                logger.info("No third 'Next' button found or it's disabled")
            
            # Wait for completion
            # self.wait_for_upload_completion()
            
            logger.info(f"Excel file uploaded successfully: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return False
    
    def wait_for_upload_completion(self):
        """Wait for upload process to complete"""
        try:
            # Wait for success message
            success_selectors = [
                (By.XPATH, '//div[contains(text(), "Success") or contains(text(), "Complete") or contains(text(), "成功")]'),
                (By.XPATH, '//span[contains(text(), "Success") or contains(text(), "Complete") or contains(text(), "成功")]'),
                (By.CSS_SELECTOR, '.success'),
                (By.CSS_SELECTOR, '.complete'),
                (By.CSS_SELECTOR, 'div[class*="success"]')
            ]
            
            for by, selector in success_selectors:
                try:
                    self.wait.until(EC.presence_of_element_located((by, selector)))
                    logger.info("Upload completed successfully")
                    return
                except TimeoutException:
                    continue
            
            # If no success message, wait and assume completion
            time.sleep(5)
            logger.info("Upload process completed (no confirmation message detected)")
            
        except Exception as e:
            logger.warning(f"Error waiting for completion: {e}")
    
    def run(self, excel_file):
        """Main execution method"""
        try:
            # Validate Excel file exists
            excel_path = Path(excel_file)
            if not excel_path.exists():
                logger.error(f"Excel file not found: {excel_file}")
                return False
            
            logger.info(f"Starting upload of Excel file: {excel_file}")
            
            # Setup and execute upload
            self.setup_driver()
            
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
            if self.driver:
                try:
                    pass
                except:
                    pass
            return False
            
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("Browser closed")
                except Exception as e:
                    logger.warning(f"Error closing browser: {e}")