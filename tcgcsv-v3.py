##this version can download multiple category ids at once and save as json or csv, but now download the images

import requests
import time
import json
import csv
import os
from datetime import datetime, timedelta

class TCGCSVScraper:
    def __init__(self, category_ids=['1'], app_name='MyTCGApp', export_format='json', test_mode=False):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'{app_name}/1.0.0'  # Custom User-Agent as required
        })
        if isinstance(category_ids, str):
            category_ids = [category_ids]
        self.category_ids = category_ids
        self.base_url = "https://tcgcsv.com"
        self.last_update_file = 'last_updated.txt'
        # self.data_file = f'tcg_data_{category_id}'
        self.data_file = f'tcg_data_{"_".join(self.category_ids)}'
        self.export_format = export_format  # 'json' or 'csv'
        self.test_mode = test_mode  # Add this line
        self.max_test_groups = 5     # Add this line
        
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
                    return datetime.fromisoformat(timestamp)
            except:
                return None
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
        # """Check if we should sync based on last build time"""
        # build_time = self.get_last_build_timestamp()
        # if not build_time:
        #     print("Could not determine build time, proceeding with sync...")
        #     return True
        
        # last_sync = self.get_last_sync_time()
        # if not last_sync:
        #     print("No previous sync found, proceeding with sync...")
        #     return True
        
        # # Only sync if new data is available
        # if build_time > last_sync:
        #     print(f"New data available! Build time: {build_time}")
        #     return True
        # else:
        #     print(f"No new data available. Last sync: {last_sync}, Build time: {build_time}")
        #     return False
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
        """Save data in the specified format"""
        if self.export_format == 'json':
            return self.export_to_json(data)
        elif self.export_format == 'csv':
            return self.export_to_csv(data)
        else:
            # Default to both JSON and CSV
            json_file = self.export_to_json(data)
            csv_file = self.export_to_csv(data)
            return [json_file, csv_file]
    
    def save_progress(self, data):
        """Save progress in case of partial scrape"""
        progress_file = f'{self.data_file}.partial'
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Progress saved to: {progress_file}")
    
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
            
            groups_to_process = all_groups[:self.max_test_groups] if self.test_mode else all_groups
            
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
        # print(f"Category ID: {self.category_id}")
        print(f"Export format: {self.export_format}")
        
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
    
    # Category ID: 1=Pokemon, 3=YuGiOh, 4=Magic, 7=Epic
    CATEGORY_IDS = ['1', '4']
    
    # Application name for User-Agent header
    APP_NAME = 'MyTCGDataCollector'
    
    # Export format options:
    # 'json' - Save as JSON file (nested structure)
    # 'csv'  - Save as CSV file (flattened structure)
    # 'both' - Save as both JSON and CSV files
    EXPORT_FORMAT = 'csv'  # Change to 'json' or 'csv' or 'bothas needed
    
    # Test mode - set to True to only process first 5 groups
    TEST_MODE = True  # Set to True for testing
    
    # ============================================
    # END OF CONFIGURATION
    # ============================================
    
    scraper = TCGCSVScraper(CATEGORY_IDS, APP_NAME, EXPORT_FORMAT)
    
    # If testing, we can limit groups in the scrape method
    # if TEST_MODE:
    #     print("TEST MODE: Only processing first 5 groups")
    #     # Note: To implement this, you'd need to modify the scrape_data method
    #     # or pass a max_groups parameter. For now, it's just a flag.
    #     print("WARNING: TEST_MODE is set but not implemented in this version.")
    #     print("To test, manually limit the loop in scrape_data()")
    
    scraper = TCGCSVScraper(CATEGORY_IDS, APP_NAME, EXPORT_FORMAT, test_mode=TEST_MODE)

    if TEST_MODE:
        print("TEST MODE: Only processing first 5 groups")
        
    scraper.run()

if __name__ == "__main__":
    main()