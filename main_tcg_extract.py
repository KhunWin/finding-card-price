
import sys
import os
import threading
import requests
import time
import json
import csv
from datetime import datetime
from urllib.parse import urlparse
import hashlib

class TCGCSVScraperGUI:
    def __init__(self, category_ids, group_ids, output_folder, app_name, download_images, image_size, log_callback, progress_callback, is_running_callback):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'{app_name}/1.0.0'
        })
        
        if isinstance(category_ids, str):
            category_ids = [category_ids]
        self.category_ids = category_ids
        
        if group_ids is not None:
            if isinstance(group_ids, str):
                group_ids = [group_ids]
            self.group_ids = [str(gid).strip() for gid in group_ids if gid.strip()]
        else:
            self.group_ids = None
            
        self.base_url = "https://tcgcsv.com"
        self.output_folder = output_folder
        self.download_images = download_images
        self.image_size = image_size
        self.image_folder = os.path.join(output_folder, 'downloaded_images')
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.is_running_callback = is_running_callback
        
        if self.download_images and not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)
            self.log_callback(f"✓ Created image folder: {self.image_folder}", "green")

    def is_running(self):
        """Check if scraper should continue running"""
        return self.is_running_callback()
    
    def log(self, message, color="white"):
        """Log message with color"""
        self.log_callback(message, color)
        
    def fetch_with_retry(self, url, max_retries=3):
        for attempt in range(max_retries):
            if not self.is_running():
                return None
            try:
                r = self.session.get(url)
                if r.status_code == 429:
                    self.log(f"⚠ Rate limited, waiting 10 minutes...", "yellow")
                    for i in range(600):
                        if not self.is_running():
                            return None
                        time.sleep(1)
                    continue
                r.raise_for_status()
                return r
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                self.log(f"⚠ Request failed (attempt {attempt + 1}/{max_retries}): {e}", "orange")
                time.sleep(2 ** attempt)
        return None
    
    def get_filename_from_url(self, url, product_id=None):
        try:
            parsed_url = urlparse(url)
            path = parsed_url.path
            filename = os.path.basename(path)
            
            if not filename or '.' not in filename:
                if product_id:
                    filename = f"product_{product_id}.jpg"
                else:
                    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
                    filename = f"image_{url_hash}.jpg"
            
            filename = filename.split('?')[0]
            filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
            
            return filename
        except Exception as e:
            if product_id:
                return f"product_{product_id}.jpg"
            else:
                return f"image_{int(time.time())}.jpg"
    
    def download_image(self, image_url, product_id=None, product_name=None, max_retries=3):
        if not image_url or not self.download_images or not self.is_running():
            return None

        # Apply image size modification
        if self.image_size == '_400w':
            if '_200w' in image_url:
                image_url = image_url.replace('_200w', '_400w')
        elif self.image_size == '_in_1000x1000':
            # Replace size pattern with _in_1000x1000
            import re
            image_url = re.sub(r'_\d+w', '_in_1000x1000', image_url)
            # Also remove file extension and add back
            base_url = image_url.rsplit('.', 1)[0]
            if not base_url.endswith('_in_1000x1000'):
                image_url = base_url + '_in_1000x1000.jpg'
        
        if product_name:
            clean_name = ''.join(c for c in product_name if c.isalnum() or c in ' _-')[:50]
            filename = f"{clean_name}_{product_id}.jpg" if product_id else f"{clean_name}.jpg"
        else:
            filename = self.get_filename_from_url(image_url, product_id)
        
        if product_id and not filename.startswith(str(product_id)):
            name_parts = filename.rsplit('.', 1)
            if len(name_parts) == 2:
                filename = f"{product_id}_{name_parts[0]}.{name_parts[1]}"
        
        filepath = os.path.join(self.image_folder, filename)
        
        if os.path.exists(filepath):
            return filepath
        
        for attempt in range(max_retries):
            if not self.is_running():
                return None
            try:
                img_response = requests.get(image_url, timeout=30, stream=True)
                img_response.raise_for_status()
                
                content_type = img_response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    self.log(f"✗ Not an image: {image_url} (type: {content_type})", "red")
                    return None
                
                with open(filepath, 'wb') as f:
                    for chunk in img_response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                self.log(f"  ✓ Downloaded: {filename}", "lightgreen")
                return filepath
                
            except requests.exceptions.Timeout:
                self.log(f"✗ Timeout: {filename} (attempt {attempt+1}/{max_retries})", "red")
                if attempt == max_retries - 1:
                    return None
                time.sleep(2 ** attempt)
                
            except requests.exceptions.RequestException as e:
                self.log(f"✗ Download error: {filename} - {e}", "red")
                if attempt == max_retries - 1:
                    return None
                time.sleep(2 ** attempt)
                
            except Exception as e:
                self.log(f"✗ Unexpected error: {filename} - {e}", "red")
                return None
        
        return None
    
    def export_to_csv(self, data):
        # csv_file = os.path.join(self.output_folder, f'tcg_data_categoryId{"_".join(self.category_ids)}.csv')
        excel_file = os.path.join(self.output_folder, f'tcg_data_categoryId{"_".join(self.category_ids)}.xlsx')
        
        rows = []
        for group_data in data:
            group = group_data['group']
            for product in group_data['products']:
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
        
        # if rows:
            # with open(excel_file, 'w', newline='', encoding='utf-8') as f:
            #     writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            #     writer.writeheader()
            #     writer.writerows(rows)
            # self.log(f"✓ Excel file saved: {excel_file}", "green")
        
        if rows:
            import pandas as pd
            df = pd.DataFrame(rows)
            df.to_excel(excel_file, index=False, engine='openpyxl')
            self.log(f"✓ Excel saved: {excel_file}", "green")
        
        return excel_file
    
    def scrape_data(self):
        self.log("=" * 60, "cyan")
        self.log("Starting TCG Data Scraper", "cyan")
        self.log("=" * 60, "cyan")
        
        start_time = time.time()
        request_count = 0
        all_data = []
        total_products = 0
        total_groups = 0
        downloaded_images = 0
        failed_images = 0
        
        for category_id in self.category_ids:
            if not self.is_running():
                self.log("Scraping cancelled by user", "yellow")
                break
                
            self.log(f"\n📁 Processing Category ID: {category_id}", "cyan")
            
            self.log("Fetching groups...", "white")
            r = self.fetch_with_retry(f"{self.base_url}/tcgplayer/{category_id}/groups")
            if not r:
                self.log(f"✗ Failed to fetch groups for category {category_id}", "red")
                continue
            all_groups = r.json()['results']
            request_count += 1
            
            if self.group_ids:
                groups_to_process = [g for g in all_groups if str(g['groupId']) in self.group_ids]
                self.log(f"Processing {len(groups_to_process)} specified groups", "white")
                
                found_group_ids = {str(g['groupId']) for g in groups_to_process}
                missing_group_ids = set(self.group_ids) - found_group_ids
                if missing_group_ids:
                    self.log(f"⚠ Group IDs not found: {', '.join(missing_group_ids)}", "yellow")
            else:
                groups_to_process = all_groups
                self.log(f"Processing all {len(groups_to_process)} groups", "white")
            
            for idx, group in enumerate(groups_to_process):
                if not self.is_running():
                    break
                    
                group_id = group['groupId']
                group_name = group['name']
                self.log(f"\n📦 [{idx + 1}/{len(groups_to_process)}] {group_name} (ID: {group_id})", "yellow")
                self.progress_callback(idx + 1, len(groups_to_process))
                
                time.sleep(0.1)
                
                r = self.fetch_with_retry(f"{self.base_url}/tcgplayer/{category_id}/{group_id}/products")
                if not r:
                    self.log(f"✗ Failed to fetch products for group {group_id}", "red")
                    continue
                products = r.json()['results']
                request_count += 1
                
                time.sleep(0.1)
                
                r = self.fetch_with_retry(f"{self.base_url}/tcgplayer/{category_id}/{group_id}/prices")
                if not r:
                    self.log(f"✗ Failed to fetch prices for group {group_id}", "red")
                    continue
                prices = r.json()['results']
                request_count += 1
                
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
                
                # Download images for this group
                if self.download_images:
                    self.log(f"  📷 Downloading images...", "cyan")
                    for product in product_dict.values():
                        if not self.is_running():
                            break
                        image_url = product.get('imageUrl')
                        if image_url:
                            result = self.download_image(
                                image_url, 
                                product.get('productId'),
                                product.get('name')
                            )
                            if result:
                                downloaded_images += 1
                            else:
                                failed_images += 1
                            time.sleep(0.05)
                
                group_data = {
                    'categoryId': category_id,
                    'group': group,
                    'products': list(product_dict.values())
                }
                all_data.append(group_data)
                total_products += len(products)
                total_groups += 1
                
                self.log(f"  ✓ Processed {len(products)} products", "lightgreen")
        
        # Save CSV
        if all_data and self.is_running():
            self.log("\n💾 Saving data...", "cyan")
            csv_file = self.export_to_csv(all_data)
        
        elapsed_time = time.time() - start_time
        
        stats = {
            'groups': total_groups,
            'products': total_products,
            'requests': request_count,
            'time': elapsed_time,
            'images_downloaded': downloaded_images,
            'images_failed': failed_images,
            'csv_file': csv_file if all_data else None
        }
        
        self.log("\n" + "=" * 60, "cyan")
        self.log("✓ SCRAPING COMPLETED", "green")
        self.log("=" * 60, "cyan")
        self.log(f"Groups: {total_groups} | Products: {total_products}", "white")
        self.log(f"Requests: {request_count} | Time: {elapsed_time / 60:.2f} min", "white")
        if self.download_images:
            self.log(f"Images: {downloaded_images} downloaded, {failed_images} failed", "white")
        self.log("=" * 60, "cyan")
        
        return stats
