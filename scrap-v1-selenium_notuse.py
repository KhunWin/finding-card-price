import requests
import os
import time
from datetime import datetime
from urllib.parse import urlparse
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout

class WebPageScraper:
    """
    A class to scrape and save web pages as HTML files.
    """
    
    def __init__(self, output_dir="scraped_pages"):
        """
        Initialize the scraper with output directory.
        
        Args:
            output_dir (str): Directory to save HTML files
        """
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Create output directory if it doesn't exist
        self._create_output_directory()
        
    def _create_output_directory(self):
        """
        Create the output directory if it doesn't exist.
        """
        try:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
                print(f"✅ Created output directory: {self.output_dir}")
            else:
                print(f"📁 Output directory exists: {self.output_dir}")
        except OSError as e:
            print(f"❌ Error creating directory: {e}")
            raise
    
    def _sanitize_filename(self, url):
        """
        Create a safe filename from URL.
        
        Args:
            url (str): The URL to sanitize
            
        Returns:
            str: Safe filename
        """
        # Parse URL to get domain and path
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        path = parsed.path.strip('/').replace('/', '_')
        
        if not path:
            path = 'index'
        
        # Add timestamp to avoid duplicates
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{domain}_{path}_{timestamp}.html"
        
        # Remove invalid characters for filenames
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        return filename
    
    def scrape_page(self, url, max_retries=3, delay=2):
        """
        Scrape a web page and save it as HTML.
        
        Args:
            url (str): The URL to scrape
            max_retries (int): Maximum number of retry attempts
            delay (int): Delay between retries in seconds
            
        Returns:
            tuple: (success_bool, file_path_or_error_message)
        """
        print("\n" + "="*60)
        print(f"🌐 SCRAPING: {url}")
        print("="*60)
        
        # Step 1: Validate URL
        print("📌 Step 1: Validating URL...")
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            print(f"   🔄 Added HTTPS protocol: {url}")
        
        try:
            # Step 2: Prepare request
            print("📌 Step 2: Preparing HTTP request...")
            print(f"   📡 User-Agent: {self.session.headers['User-Agent']}")
            
            # Step 3: Send request with retries
            print(f"📌 Step 3: Sending request (max retries: {max_retries})...")
            
            for attempt in range(max_retries):
                try:
                    print(f"   Attempt {attempt + 1}/{max_retries}...")
                    
                    # Send GET request with timeout
                    response = self.session.get(url, timeout=30)
                    
                    # Step 4: Check response status
                    print("📌 Step 4: Checking response...")
                    response.raise_for_status()  # Raise HTTPError for bad responses
                    
                    print(f"   ✅ Status Code: {response.status_code}")
                    print(f"   📊 Content Length: {len(response.content)} bytes")
                    print(f"   🔤 Encoding: {response.encoding}")
                    
                    # Step 5: Get HTML content
                    print("📌 Step 5: Extracting HTML content...")
                    html_content = response.text
                    
                    # Step 6: Create filename
                    print("📌 Step 6: Creating filename...")
                    filename = self._sanitize_filename(url)
                    filepath = os.path.join(self.output_dir, filename)
                    print(f"   📄 Filename: {filename}")
                    
                    # Step 7: Save HTML to file
                    print("📌 Step 7: Saving HTML file...")
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    
                    print(f"   ✅ File saved successfully!")
                    print(f"   📁 Location: {filepath}")
                    print(f"   📊 File size: {os.path.getsize(filepath)} bytes")
                    
                    # Step 8: Return success
                    print("✅ SCRAPING COMPLETED SUCCESSFULLY!")
                    return True, filepath
                    
                except HTTPError as e:
                    print(f"   ⚠️ HTTP Error on attempt {attempt + 1}: {e}")
                    if response.status_code == 403:
                        print("   🚫 Access forbidden - website may be blocking requests")
                        print("   💡 Tip: Try adding more headers or using a proxy")
                    elif response.status_code == 404:
                        print("   🔍 Page not found - URL may be incorrect")
                        break  # No point retrying 404
                    elif response.status_code == 429:
                        print("   ⏳ Too many requests - rate limited")
                        print(f"   💤 Waiting {delay * 2} seconds...")
                        time.sleep(delay * 2)
                    else:
                        print(f"   💤 Waiting {delay} seconds before retry...")
                        time.sleep(delay)
                        
                except ConnectionError as e:
                    print(f"   ⚠️ Connection Error on attempt {attempt + 1}: {e}")
                    print(f"   💤 Waiting {delay} seconds before retry...")
                    time.sleep(delay)
                    
                except Timeout as e:
                    print(f"   ⚠️ Timeout Error on attempt {attempt + 1}: {e}")
                    print(f"   💤 Waiting {delay} seconds before retry...")
                    time.sleep(delay)
                    
                except RequestException as e:
                    print(f"   ⚠️ Request Error on attempt {attempt + 1}: {e}")
                    print(f"   💤 Waiting {delay} seconds before retry...")
                    time.sleep(delay)
            
            # If we get here, all retries failed
            print("❌ All retry attempts failed")
            return False, "Failed to retrieve page after all retries"
            
        except Exception as e:
            # Catch any unexpected errors
            print(f"❌ Unexpected error: {e}")
            return False, str(e)
    
    def scrape_multiple_pages(self, urls):
        """
        Scrape multiple web pages.
        
        Args:
            urls (list): List of URLs to scrape
            
        Returns:
            dict: Results for each URL
        """
        results = {}
        print(f"\n📋 Starting batch scraping for {len(urls)} URLs...")
        
        for i, url in enumerate(urls, 1):
            print(f"\n🔄 Processing URL {i}/{len(urls)}")
            success, result = self.scrape_page(url)
            results[url] = {
                'success': success,
                'result': result
            }
            
            # Add delay between requests to be respectful
            if i < len(urls):
                print(f"⏳ Waiting 2 seconds before next request...")
                time.sleep(2)
        
        return results
    
    def close(self):
        """Close the session."""
        self.session.close()
        print("🔒 Session closed")

def main():
    """
    Main function to demonstrate the scraper.
    """
    print("🚀 WEB PAGE SCRAPER STARTED")
    print("="*60)
    
    # Create scraper instance
    scraper = WebPageScraper(output_dir="my_scraped_pages")
    
    try:
        # Example 1: Scrape a single page
        # url1 = "https://example.com"
        # success, result = scraper.scrape_page(url1)
        
        # if success:
        #     print(f"\n✅ Successfully saved: {result}")
        # else:
        #     print(f"\n❌ Failed to scrape: {result}")
        
        # Example 2: Scrape multiple pages
        urls_to_scrape = [
            "https://www.tcgplayer.com/product/704835/pokemon-me05-pitch-black-gwynn-078-084?page=1&Language=English", # This will fail
        ]
        
        print("\n" + "="*60)
        print("📋 BATCH SCRAPING EXAMPLE")
        print("="*60)
        
        results = scraper.scrape_multiple_pages(urls_to_scrape)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 SCRAPING SUMMARY")
        print("="*60)
        successful = sum(1 for r in results.values() if r['success'])
        total = len(results)
        print(f"✅ Successful: {successful}/{total}")
        print(f"❌ Failed: {total - successful}/{total}")
        
        for url, data in results.items():
            status = "✅" if data['success'] else "❌"
            print(f"{status} {url}: {data['result']}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Scraping interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        # Clean up
        scraper.close()
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()