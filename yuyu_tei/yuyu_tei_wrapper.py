"""
Yuyu-Tei Wrapper - Interface between GUI and scraper
"""
import sys
import os
import time
from pathlib import Path

# Import the actual scraper
try:
    from scarp_yuyu_v4 import YuyuteiScraper, CardInfo
except ImportError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    from scarp_yuyu_v4 import YuyuteiScraper, CardInfo


class YuyuTeiWrapper:
    """Wrapper to integrate YuyuteiScraper with the GUI"""
    
    def __init__(self, category_id, group_ids, output_folder, download_images=True,
                 log_callback=None, progress_callback=None, is_running_callback=None):
        self.category_id = category_id
        self.group_ids = group_ids if isinstance(group_ids, list) else [group_ids]
        self.output_folder = output_folder
        self.download_images = download_images
        self.log_callback = log_callback or self._default_log
        self.progress_callback = progress_callback or self._default_progress
        self.is_running_callback = is_running_callback or (lambda: True)
        self.image_dir = os.path.join(output_folder, 'card_images')
    
    def _default_log(self, message, color='white'):
        print(message, end='')
    
    def _default_progress(self, value):
        pass
    
    def log(self, message, color='white'):
        self.log_callback(message, color)
    
    def update_progress(self, current, total):
        if total > 0:
            percentage = (current / total) * 100
            self.progress_callback(percentage)
    
    def scrape_all(self):
        start_time = time.time()
        all_cards = []
        total_images_downloaded = 0
        total_images_failed = 0
        total_groups = len(self.group_ids)
        
        for idx, group_code in enumerate(self.group_ids, 1):
            if not self.is_running_callback():
                self.log("⚠️ Scraping cancelled by user\n", "yellow")
                break
            
            self.log(f"\n📦 Processing Group {idx}/{total_groups}: {group_code}\n", "cyan")
            self.log(f"{'='*60}\n", "cyan")
            
            try:
                scraper = YuyuteiScraper(delay=0.5, download_images=self.download_images, image_dir=self.image_dir)
                cards = scraper.scrape_card_group(group_code, self.category_id)
                
                if cards:
                    all_cards.extend(cards)
                    if self.download_images:
                        downloaded = sum(1 for card in cards if card.image_download_success)
                        failed = sum(1 for card in cards if not card.image_download_success and card.image_url)
                        total_images_downloaded += downloaded
                        total_images_failed += failed
                        self.log(f"  📷 Images: {downloaded} downloaded, {failed} failed\n", "white")
                    self.log(f"  ✓ {len(cards)} cards scraped from {group_code}\n", "green")
                else:
                    self.log(f"  ⚠️ No cards found for {group_code}\n", "yellow")
            except Exception as e:
                self.log(f"  ❌ Error scraping {group_code}: {str(e)}\n", "red")
            
            self.update_progress(idx, total_groups)
        
        if all_cards and self.is_running_callback():
            self.log(f"\n💾 Saving results...\n", "cyan")
            temp_scraper = YuyuteiScraper(delay=0.5, download_images=self.download_images, image_dir=self.image_dir)
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            prefix = f"yuyutei_{self.category_id}_{timestamp}"
            
            # csv_filename = os.path.join(self.output_folder, f"{prefix}.csv")
            excel_filename = os.path.join(self.output_folder, f"{prefix}.xlsx")
            # summary_filename = os.path.join(self.output_folder, f"{prefix}_summary.txt")
            
            # temp_scraper.save_to_csv(all_cards, csv_filename)
            # self.log(f"  ✓ CSV saved: {csv_filename}\n", "green")
            temp_scraper.save_to_excel(all_cards, excel_filename)
            self.log(f"  ✓ Excel saved: {excel_filename}\n", "green")
            # temp_scraper._save_summary(all_cards, summary_filename)
            # self.log(f"  ✓ Summary saved: {summary_filename}\n", "green")
        
        elapsed_time = time.time() - start_time
        return {
            'groups': total_groups,
            'cards': len(all_cards),
            'images_downloaded': total_images_downloaded,
            'images_failed': total_images_failed,
            'time': elapsed_time
        }

