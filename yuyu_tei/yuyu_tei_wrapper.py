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
                 log_callback=None, progress_callback=None, card_progress_callback=None,
                 is_running_callback=None):
        self.category_id = category_id
        self.group_ids = group_ids if isinstance(group_ids, list) else [group_ids]
        self.output_folder = output_folder
        self.download_images = download_images
        self.log_callback = log_callback or self._default_log
        self.progress_callback = progress_callback or self._default_progress
        self.card_progress_callback = card_progress_callback  # callable(current, total) or None
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
        import re
        from datetime import datetime

        start_time = time.time()
        total_images_downloaded = 0
        total_images_failed = 0
        total_groups = len(self.group_ids)
        excel_files = []   # one file per group

        for idx, group_code in enumerate(self.group_ids, 1):
            if not self.is_running_callback():
                self.log("⚠️ Scraping cancelled by user\n", "yellow")
                break

            self.log(f"\n📦 Processing Group {idx}/{total_groups}: {group_code}\n", "cyan")
            self.log(f"{'='*60}\n", "cyan")

            # Per-group Excel file — sanitise the group code so characters like
            # '.' don't look odd in filenames (e.g. knk2.0 → knk2_0).
            safe_group = re.sub(r'[^\w\-]', '_', group_code)
            excel_filename = os.path.join(
                self.output_folder,
                f"yuyutei_{self.category_id}_{safe_group}.xlsx"
            )

            try:
                scraper = YuyuteiScraper(
                    delay=1.0,
                    download_images=self.download_images,
                    image_dir=self.image_dir,
                    output_dir=self.output_folder
                )

                # Pass excel_output_path so scraper flushes partial data
                # to disk after every card.  Also forward is_running so the
                # scraper stops cleanly when the user clicks Stop.
                cards = scraper.scrape_card_group(
                    group_code,
                    self.category_id,
                    excel_output_path=excel_filename,
                    progress_callback=self.card_progress_callback,
                    is_running_callback=self.is_running_callback
                )

                if cards:
                    if self.download_images:
                        downloaded = sum(1 for card in cards if card.image_download_success)
                        failed = sum(1 for card in cards if not card.image_download_success and card.image_url)
                        total_images_downloaded += downloaded
                        total_images_failed += failed
                        self.log(f"  📷 Images: {downloaded} downloaded, {failed} failed\n", "white")
                    self.log(f"  ✓ {len(cards)} cards for {group_code} (Excel up-to-date)\n", "green")
                    excel_files.append(excel_filename)
                else:
                    self.log(f"  ⚠️ No cards found for {group_code}\n", "yellow")

            except Exception as e:
                self.log(f"  ❌ Error scraping {group_code}: {str(e)}\n", "red")

            self.update_progress(idx, total_groups)

        # Report every generated file
        self.log(f"\n💾 Excel files saved:\n", "cyan")
        for ef in excel_files:
            self.log(f"   • {ef}\n", "cyan")

        elapsed_time = time.time() - start_time

        # Count total cards across all generated Excel files
        total_cards = 0
        try:
            import pandas as pd
            for ef in excel_files:
                df = pd.read_excel(ef, sheet_name='Cards')
                total_cards += len(df)
        except Exception:
            pass

        # Provide the last written file under the legacy 'excel_file' key so
        # any existing GUI code that reads that key continues to work.
        last_excel = excel_files[-1] if excel_files else ""

        return {
            'groups': total_groups,
            'cards': total_cards,
            'images_downloaded': total_images_downloaded,
            'images_failed': total_images_failed,
            'time': elapsed_time,
            'excel_file': last_excel,
            'excel_files': excel_files,
        }

