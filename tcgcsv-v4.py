##this version can download multiple category ids and group ids at once and save as json or csv, and now it can also download the images with 400w resolution instead of 200w, and it will save the images in a folder called downloaded_images. It also has a test mode to only scrape the first 5 groups for testing purposes. 


import requests
import time
import json
import csv
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse
import hashlib

class TCGCSVScraper:
    def __init__(self, category_ids=['1'], group_ids=None, app_name='MyTCGApp', export_format='json', test_mode=False, download_images=False):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'{app_name}/1.0.0'  # Custom User-Agent as required
        })
        if isinstance(category_ids, str):
            category_ids = [category_ids]
        self.category_ids = category_ids

        # Handle group_ids parameter
        if group_ids is not None:
            if isinstance(group_ids, str):
                group_ids = [group_ids]
            self.group_ids = [str(gid) for gid in group_ids]  # Convert to strings
        else:
            self.group_ids = None
            
        self.base_url = "https://tcgcsv.com"
        self.last_update_file = 'last_updated.txt'
        self.data_file = f'tcg_data_categoryId{"_".join(self.category_ids)}'
        self.export_format = export_format  # 'json' or 'csv'
        self.test_mode = test_mode
        self.max_test_groups = 5
        self.download_images = download_images  # New parameter
        self.image_folder = 'downloaded_images'  # Folder for images
        
        # Create image folder if it doesn't exist
        if self.download_images and not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)
            print(f"Created image folder: {self.image_folder}")
        
    def get_last_build_timestamp(self):
        """Check when the data was last built on TCGCSV"""
        try:
            r = self.session.get(f"{self.base_url}/last-updated.txt")
            r.raise_for_status()
            timestamp = r.text.strip()
            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except Exception as e:
            print(f"Error fetching last update timestamp: {e}")
            return None
    
    def get_last_sync_time(self):
        """Get the last time we synced data"""
        if os.path.exists(self.last_update_file):
            try:
                with open(self.last_update_file, 'r') as f:
                    timestamp = f.read().strip()
                    # Make it timezone-aware by adding UTC timezone
                    dt = datetime.fromisoformat(timestamp)
                    # If it's naive, make it aware with UTC
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
                    return dt
            except:
                return None
        return None

    def save_sync_time(self):
        """Save the current time as last sync time"""
        with open(self.last_update_file, 'w') as f:
            f.write(datetime.now().isoformat())
    
    def should_sync(self):
        return True  # Always sync for now, can implement logic later
    
    def fetch_with_retry(self, url, max_retries=3):
        """Fetch with retry logic for rate limiting"""
        for attempt in range(max_retries):
            try:
                r = self.session.get(url)
                if r.status_code == 429:  # Too Many Requests
                    print(f"Rate limited, waiting 10 minutes...")
                    time.sleep(600)  # Wait 10 minutes
                    continue
                r.raise_for_status()
                return r
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                print(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
        return None
    
    def get_filename_from_url(self, url, product_id=None):
        """Generate a safe filename from URL"""
        try:
            # Parse the URL to get the filename
            parsed_url = urlparse(url)
            path = parsed_url.path
            
            # Get the base filename
            filename = os.path.basename(path)
            
            # If no filename, use product_id or hash
            if not filename or '.' not in filename:
                if product_id:
                    filename = f"product_{product_id}.jpg"
                else:
                    # Create hash from URL
                    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
                    filename = f"image_{url_hash}.jpg"
            
            # Remove any query parameters
            filename = filename.split('?')[0]
            
            # Ensure filename is safe
            filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
            
            return filename
        except Exception as e:
            # Fallback to a simple filename
            if product_id:
                return f"product_{product_id}.jpg"
            else:
                return f"image_{int(time.time())}.jpg"
    
    def download_image(self, image_url, product_id=None, product_name=None, max_retries=3):
        """Download a single image with error handling"""
        if not image_url or not self.download_images:
            return None

        if '_200w' in image_url: #change the image size when downloading to 400w or
            image_url = image_url.replace('_200w', '_400w')
            print(f"  Changed image URL from 200w to 400w")
        #Original URL: https://tcgplayer-cdn.tcgplayer.com/product/451396_200w.jpg
        #Improved URL: https://tcgplayer-cdn.tcgplayer.com/product/451396_in_1000x1000.jpg
        
        # Generate a meaningful filename
        if product_name:
            clean_name = ''.join(c for c in product_name if c.isalnum() or c in ' _-')[:50]
            filename = f"{clean_name}_{product_id}.jpg" if product_id else f"{clean_name}.jpg"
        else:
            filename = self.get_filename_from_url(image_url, product_id)
        
        # Ensure unique filename by adding product_id if available
        if product_id and not filename.startswith(str(product_id)):
            name_parts = filename.rsplit('.', 1)
            if len(name_parts) == 2:
                filename = f"{product_id}_{name_parts[0]}.{name_parts[1]}"
        
        # Full path for saving
        filepath = os.path.join(self.image_folder, filename)
        
        # Check if image already exists
        if os.path.exists(filepath):
            print(f"  Image already exists: {filename}")
            return filepath
        
        # Download with retry logic
        for attempt in range(max_retries):
            try:
                # Use a separate session for image download
                img_response = requests.get(image_url, timeout=30, stream=True)
                img_response.raise_for_status()
                
                # Check if it's actually an image
                content_type = img_response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    print(f"  Warning: URL {image_url} is not an image (content-type: {content_type})")
                    return None
                
                # Save the image
                with open(filepath, 'wb') as f:
                    for chunk in img_response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                print(f"  Downloaded: {filename}")
                return filepath
                
            except requests.exceptions.Timeout:
                print(f"  Timeout downloading {filename} (attempt {attempt+1}/{max_retries})")
                if attempt == max_retries - 1:
                    return None
                time.sleep(2 ** attempt)
                
            except requests.exceptions.RequestException as e:
                print(f"  Download error for {filename}: {e} (attempt {attempt+1}/{max_retries})")
                if attempt == max_retries - 1:
                    return None
                time.sleep(2 ** attempt)
                
            except Exception as e:
                print(f"  Unexpected error downloading {filename}: {e}")
                return None
        
        return None
    
    def download_images_for_data(self, data):
        """Download all images from the scraped data"""
        if not self.download_images:
            print("Image downloading is disabled")
            return
        
        print(f"\n{'='*50}")
        print("Starting image downloads...")
        print(f"{'='*50}")
        
        total_images = 0
        downloaded_images = 0
        failed_images = 0
        
        for group_data in data:
            for product in group_data['products']:
                image_url = product.get('imageUrl')
                product_id = product.get('productId')
                product_name = product.get('name')
                
                if image_url:
                    total_images += 1
                    result = self.download_image(image_url, product_id, product_name)
                    if result:
                        downloaded_images += 1
                    else:
                        failed_images += 1
                    
                    # Rate limiting for image downloads
                    if self.download_images:
                        time.sleep(0.05)  # Small delay to avoid being blocked
        
        print(f"\n{'='*50}")
        print("Image download summary:")
        print(f"  Total images found: {total_images}")
        print(f"  Successfully downloaded: {downloaded_images}")
        print(f"  Failed downloads: {failed_images}")
        print(f"  Images saved to: {os.path.abspath(self.image_folder)}")
        print(f"{'='*50}")
    
    def export_to_json(self, data):
        """Export data to JSON format"""
        json_file = f'{self.data_file}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"JSON data saved to: {json_file}")
        return json_file
    
    def export_to_csv(self, data):
        """Export data to CSV format with flattened structure"""
        csv_file = f'{self.data_file}.csv'
        
        # Flatten the data for CSV
        rows = []
        for group_data in data:
            group = group_data['group']
            for product in group_data['products']:
                # For each price variant, create a separate row
                if product['prices']:
                    for price in product['prices']:
                        row = {
                            'groupId': group.get('groupId'),
                            'groupName': group.get('name'),
                            'groupAbbreviation': group.get('abbreviation'),
                            'groupIsSupplemental': group.get('isSupplemental'),
                            'groupPublishedOn': group.get('publishedOn'),
                            'groupModifiedOn': group.get('modifiedOn'),
                            'productId': product.get('productId'),
                            'productName': product.get('name'),
                            'cleanName': product.get('cleanName'),
                            'imageUrl': product.get('imageUrl'),
                            'categoryId': product.get('categoryId'),
                            'productUrl': product.get('url'),
                            'productModifiedOn': product.get('modifiedOn'),
                            'imageCount': product.get('imageCount'),
                            'isPresale': product.get('presaleInfo', {}).get('isPresale'),
                            'releasedOn': product.get('presaleInfo', {}).get('releasedOn'),
                            'subTypeName': price.get('subTypeName'),
                            'lowPrice': price.get('lowPrice'),
                            'midPrice': price.get('midPrice'),
                            'highPrice': price.get('highPrice'),
                            'marketPrice': price.get('marketPrice'),
                            'directLowPrice': price.get('directLowPrice')
                        }
                        rows.append(row)
                else:
                    # If no prices, still include the product with empty price fields
                    row = {
                        'groupId': group.get('groupId'),
                        'groupName': group.get('name'),
                        'groupAbbreviation': group.get('abbreviation'),
                        'groupIsSupplemental': group.get('isSupplemental'),
                        'groupPublishedOn': group.get('publishedOn'),
                        'groupModifiedOn': group.get('modifiedOn'),
                        'productId': product.get('productId'),
                        'productName': product.get('name'),
                        'cleanName': product.get('cleanName'),
                        'imageUrl': product.get('imageUrl'),
                        'categoryId': product.get('categoryId'),
                        'productUrl': product.get('url'),
                        'productModifiedOn': product.get('modifiedOn'),
                        'imageCount': product.get('imageCount'),
                        'isPresale': product.get('presaleInfo', {}).get('isPresale'),
                        'releasedOn': product.get('presaleInfo', {}).get('releasedOn'),
                        'subTypeName': None,
                        'lowPrice': None,
                        'midPrice': None,
                        'highPrice': None,
                        'marketPrice': None,
                        'directLowPrice': None
                    }
                    rows.append(row)
        
        # Write to CSV
        if rows:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            print(f"CSV data saved to: {csv_file}")
        else:
            print("No data to export to CSV")
        
        return csv_file
    
    def save_data(self, data):
        """Save data in the specified format and download images if enabled"""
        saved_files = []
        
        # Save data files
        if self.export_format == 'json':
            saved_files.append(self.export_to_json(data))
        elif self.export_format == 'csv':
            saved_files.append(self.export_to_csv(data))
        else:
            # Default to both JSON and CSV
            saved_files.append(self.export_to_json(data))
            saved_files.append(self.export_to_csv(data))
        
        # Download images if enabled
        if self.download_images:
            self.download_images_for_data(data)
        
        return saved_files
    
    def save_progress(self, data):
        """Save progress in case of partial scrape"""
        progress_file = f'{self.data_file}.partial'
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Progress saved to: {progress_file}")
    
    ##with specific ids
    def scrape_data(self):
        """Main scraping logic"""
        print("Starting data scrape...")
        start_time = time.time()
        request_count = 0
        
        all_data = []
        total_products = 0
        total_groups = 0
        
        # Process each category
        for category_id in self.category_ids:
            print(f"\n{'='*50}")
            print(f"Processing Category ID: {category_id}")
            print(f"{'='*50}")
            
            # Get all groups for this category
            print("Fetching groups...")
            r = self.fetch_with_retry(f"{self.base_url}/tcgplayer/{category_id}/groups")
            if not r:
                print(f"Failed to fetch groups for category {category_id}, skipping...")
                continue
            all_groups = r.json()['results']
            request_count += 1
            
            # Determine which groups to process
            if self.group_ids:
                # Filter groups by provided group IDs
                groups_to_process = [g for g in all_groups if str(g['groupId']) in self.group_ids]
                print(f"Processing {len(groups_to_process)} specified groups (from {len(self.group_ids)} requested)")
                
                # Check if any requested groups were not found
                found_group_ids = {str(g['groupId']) for g in groups_to_process}
                missing_group_ids = set(self.group_ids) - found_group_ids
                if missing_group_ids:
                    print(f"WARNING: Group IDs not found: {', '.join(missing_group_ids)}")
            elif self.test_mode:
                # Test mode: only process first N groups
                groups_to_process = all_groups[:self.max_test_groups]
                print(f"TEST MODE: Processing first {len(groups_to_process)} groups")
            else:
                # No specific groups and not test mode: process all groups
                groups_to_process = all_groups
                print(f"Processing all {len(groups_to_process)} groups")
            
            # Process each group
            for idx, group in enumerate(groups_to_process):
                group_id = group['groupId']
                group_name = group['name']
                print(f"Processing group {idx + 1}/{len(groups_to_process)}: {group_name} (ID: {group_id})")
                
                # Rate limiting - 100ms between requests
                time.sleep(0.1)
                
                # Get products for this group
                r = self.fetch_with_retry(f"{self.base_url}/tcgplayer/{category_id}/{group_id}/products")
                if not r:
                    print(f"Failed to fetch products for group {group_id}, skipping...")
                    continue
                products = r.json()['results']
                request_count += 1
                
                # Rate limiting - 100ms between requests
                time.sleep(0.1)
                
                # Get prices for this group
                r = self.fetch_with_retry(f"{self.base_url}/tcgplayer/{category_id}/{group_id}/prices")
                if not r:
                    print(f"Failed to fetch prices for group {group_id}, skipping...")
                    continue
                prices = r.json()['results']
                request_count += 1
                
                # Combine product and price data
                product_dict = {p['productId']: {
                    'productId': p['productId'],
                    'name': p['name'],
                    'cleanName': p.get('cleanName', ''),
                    'imageUrl': p.get('imageUrl', ''),
                    'categoryId': p.get('categoryId'),
                    'groupId': p.get('groupId'),
                    'url': p.get('url', ''),
                    'modifiedOn': p.get('modifiedOn', ''),
                    'imageCount': p.get('imageCount', 0),
                    'presaleInfo': p.get('presaleInfo', {}),
                    'extendedData': p.get('extendedData', []),
                    'prices': []
                } for p in products}
                
                # Add prices to products
                for price in prices:
                    product_id = price['productId']
                    if product_id in product_dict:
                        product_dict[product_id]['prices'].append({
                            'lowPrice': price.get('lowPrice'),
                            'midPrice': price.get('midPrice'),
                            'highPrice': price.get('highPrice'),
                            'marketPrice': price.get('marketPrice'),
                            'directLowPrice': price.get('directLowPrice'),
                            'subTypeName': price.get('subTypeName', '')
                        })
                
                group_data = {
                    'categoryId': category_id,
                    'group': group,
                    'products': list(product_dict.values())
                }
                all_data.append(group_data)
                total_products += len(products)
                total_groups += 1
                
                # Check if we're approaching request limit
                if request_count >= 9000:
                    print(f"WARNING: Approaching 10,000 request limit ({request_count} requests used)")
                    self.save_progress(all_data)
                
                # Check if we've exceeded the limit
                if request_count >= 10000:
                    print(f"ERROR: Reached 10,000 request limit. Stopping scrape.")
                    break
            
            if request_count >= 10000:
                break
        
        # Save final data in specified format
        saved_files = self.save_data(all_data)
        
        elapsed_time = time.time() - start_time
        print(f"\n{'='*50}")
        print(f"=== Scrape Complete ===")
        print(f"Categories processed: {len(self.category_ids)}")
        print(f"Groups processed: {total_groups}")
        print(f"Total products: {total_products}")
        print(f"Total requests: {request_count}")
        print(f"Time elapsed: {elapsed_time / 60:.2f} minutes")
        print(f"Data saved to: {saved_files}")
        
        # Save sync time after successful scrape
        self.save_sync_time()
        
    def load_data(self):
        """Load existing data if available"""
        json_file = f'{self.data_file}.json'
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def run(self):
        """Main entry point"""
        print("=== TCGCSV Scraper ===")
        print(f"Export format: {self.export_format}")
        print(f"Download images: {self.download_images}")
        if self.download_images:
            print(f"Image folder: {self.image_folder}")
        
        # Check if we should sync
        if not self.should_sync():
            print("No sync needed. Use --force to override.")
            return
        
        # Perform the scrape
        self.scrape_data()

def main():
    # ============================================
    # CONFIGURATION - Change these as needed
    # ============================================
    
    CATEGORY_IDS = ['85']
    # GROUP_IDS = ['24721','24653']  # Change this to a list of group IDs, e.g., ['1', '5', '10'] or None
    GROUP_IDS = None  # Set to None to scrape all groups in the category
    
    # Application name for User-Agent header
    APP_NAME = 'MyTCGDataCollector'
    
    # Export format options:
    # 'json' - Save as JSON file (nested structure)
    # 'csv'  - Save as CSV file (flattened structure)
    # 'both' - Save as both JSON and CSV files
    EXPORT_FORMAT = 'csv'  # Change to 'json' or 'csv' or 'both' as needed
    
    # Test mode - set to True to only process first 5 groups
    TEST_MODE = True  # Set to True for testing
    
    # Download images - set to True to download product images
    DOWNLOAD_IMAGES = False  # Set to True to download images
    
    # ============================================
    # END OF CONFIGURATION
    # ============================================
    
    # Create the scraper instance with all parameters
    scraper = TCGCSVScraper(
        category_ids=CATEGORY_IDS,
        group_ids=GROUP_IDS,
        app_name=APP_NAME,
        export_format=EXPORT_FORMAT,
        test_mode=TEST_MODE,
        download_images=DOWNLOAD_IMAGES
    )

    if GROUP_IDS:
        print(f"SPECIFIC GROUPS: Processing only group IDs: {', '.join(GROUP_IDS)}")
        print("NOTE: TEST_MODE is ignored when specific group IDs are provided")
    elif TEST_MODE:
        print("TEST MODE: Only processing first 5 groups")
    else:
        print("ALL GROUPS: Processing all available groups")
    
    if DOWNLOAD_IMAGES:
        print("IMAGE DOWNLOAD: Enabled")
        print(f"Images will be saved to: {scraper.image_folder}/")
        
    scraper.run()

if __name__ == "__main__":
    main()