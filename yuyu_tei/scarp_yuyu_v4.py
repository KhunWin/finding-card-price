import requests
from bs4 import BeautifulSoup
import json
import re
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import logging
from urllib.parse import urljoin
from datetime import datetime
import csv
import html
import os
from pathlib import Path
import pandas as pd
from io import BytesIO
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Checkpoint helpers
# ---------------------------------------------------------------------------

def _get_checkpoint_path(output_dir: str, category_id: str, group_code: str) -> str:
    """Return the path to the checkpoint JSON file for a given category+group."""
    safe_group = re.sub(r'[^\w\-]', '_', group_code)
    safe_cat   = re.sub(r'[^\w\-]', '_', category_id)
    checkpoint_dir = os.path.join(output_dir, 'checkpoints')
    Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)
    return os.path.join(checkpoint_dir, f"{safe_cat}_{safe_group}_checkpoint.json")


def _load_checkpoint(checkpoint_path: str) -> dict:
    """Load an existing checkpoint, or return an empty structure."""
    if os.path.exists(checkpoint_path):
        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Checkpoint loaded: {checkpoint_path} "
                        f"({len(data.get('cards', []))} cards already saved)")
            return data
        except Exception as e:
            logger.warning(f"Could not read checkpoint {checkpoint_path}: {e}. Starting fresh.")
    return {"all_links": [], "processed_urls": [], "cards": [], "completed": False}


def _save_checkpoint(checkpoint_path: str, data: dict):
    """Persist the checkpoint dict to disk."""
    try:
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save checkpoint {checkpoint_path}: {e}")


def _delete_checkpoint(checkpoint_path: str):
    """Remove a checkpoint file once a group is fully scraped."""
    try:
        if os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)
            logger.info(f"Checkpoint deleted (scrape complete): {checkpoint_path}")
    except Exception as e:
        logger.warning(f"Could not delete checkpoint {checkpoint_path}: {e}")

@dataclass
class CardInfo:
    """Data class to represent a card"""
    name: str
    name_power: str  # Name with reading if available
    category: str  # Category from breadcrumb (position 3)
    price: int
    price_text: str
    image_url: str
    description: str  # Card ID (e.g., DC/W01-023S)
    card_url: str
    card_id: str
    image_filename: str = ""  # Local image filename
    image_download_success: bool = False  # Track if image was successfully downloaded
    
    def to_dict(self):
        return asdict(self)

class YuyuteiScraper:
    """Scraper for YuYu-Tei card data"""
    
    BASE_URL = "https://yuyu-tei.jp"
    
    def __init__(self, delay: float = 1.0, download_images: bool = True, image_dir: str = "card_images",
                 output_dir: str = "."):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
        })
        self.delay = delay
        self.download_images = download_images
        self.image_dir = image_dir
        self.output_dir = output_dir  # Base dir used to store checkpoint files
        
        # Create image directory if it doesn't exist
        if self.download_images:
            Path(self.image_dir).mkdir(parents=True, exist_ok=True)
            logger.info(f"Image directory created/verified: {self.image_dir}")
    
    def _download_image(self, image_url: str, card_id: str, card_name: str) -> tuple:
        """
        Download image from URL and save locally
        
        Args:
            image_url: URL of the image
            card_id: Card ID for filename
            card_name: Card name for filename
            
        Returns:
            Tuple of (filename, success_flag)
        """
        if not image_url:
            logger.warning(f"No image URL for card {card_id}")
            return "", False
        
        try:
            # Create a safe filename from card ID and name
            safe_name = re.sub(r'[^\w\-_\. ]', '_', card_name)
            safe_name = safe_name[:30]  # Limit length
            timestamp = datetime.now().strftime('%H%M%S')
            filename = f"{card_id}_{safe_name}_{timestamp}.jpg"
            # Remove any problematic characters
            filename = re.sub(r'[^\w\-_\.]', '_', filename)
            filepath = os.path.join(self.image_dir, filename)
            
            # Check if image already exists
            if os.path.exists(filepath):
                logger.info(f"Image already exists: {filepath}")
                return filename, True
            
            # Download the image
            logger.info(f"Downloading image: {image_url}")
            time.sleep(self.delay)
            response = self.session.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Verify it's actually an image
            content_type = response.headers.get('content-type', '')
            if 'image' not in content_type.lower():
                logger.warning(f"URL does not point to an image: {content_type}")
                return "", False
            
            # Save the image
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Image saved: {filepath}")
            return filename, True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download image from {image_url}: {e}")
            return "", False
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            return "", False
    
    def _get_card_links_from_search(self, group_code: str, ws: str = 'ws') -> List[str]:
        """
        Get all card detail page URLs from the search results page
        
        Args:
            group_code: Group code like 'dc'
            ws: WS identifier (default: 'ws')
            
        Returns:
            List of card detail URLs
        """
        search_url = f"{self.BASE_URL}/sell/{ws}/s/search"
        params = {
            'search_word': '',
            'vers[]': group_code,
            'rare': '',
            'type': '',
            'kizu': '0'
        }
        
        logger.info(f"Fetching search results for group: {group_code} with ws: {ws}")
        time.sleep(self.delay)
        response = self.session.get(search_url, params=params)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        card_links = []
        
        # Find all card links - they are in divs with class 'card-product'
        # and contain an <a> tag linking to the card detail page
        card_containers = soup.find_all('div', class_='card-product')
        logger.info(f"Found {len(card_containers)} card containers in search results")
        
        for container in card_containers:
            # Find the link to the card detail page
            link_tag = container.find('a', href=True)
            if link_tag:
                href = link_tag['href']
                # Make sure it's a card detail link (contains /sell/ws/card/)
                if f'/sell/{ws}/card/' in href:
                    full_url = urljoin(self.BASE_URL, href)
                    card_links.append(full_url)
        
        logger.info(f"Found {len(card_links)} card detail links")
        return card_links
    
    def _parse_card_from_detail_page(self, url: str) -> Optional[Dict]:
        """
        Parse card data from detail page using JSON-LD
        
        Args:
            url: Card detail page URL
            
        Returns:
            Card data dictionary or None
        """
        try:
            logger.info(f"Fetching card detail: {url}")
            time.sleep(self.delay)
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract reading from id="power" if it exists
            reading = ""
            power_element = soup.find(id="power")
            if power_element:
                # Look for the <b> tag that contains the reading
                b_tag = power_element.find('b')
                if b_tag:
                    # Extract text and clean it
                    reading_text = b_tag.get_text(strip=True)
                    # Remove parentheses if they exist
                    reading = reading_text.strip('（）')
                    logger.info(f"Found reading: {reading}")
            
            # # Find JSON-LD script tags
            # script_tags = soup.find_all('script', type='application/ld+json')
            
            # for script in script_tags:
            #     try:
            #         if script.string is None:
            #             continue
            #         data = json.loads(script.string)
                    
            #         # Look for Product schema
            #         if isinstance(data, dict) and data.get('@type') == 'Product':
            #             # Get the name and decode HTML entities
            #             name = data.get('name', '')
                      
            #             # Decode HTML entities like &amp; to &
            #             name = html.unescape(name)

            #             name_power = name
            #             if reading:
            #                 name_power = f"{name}({reading})"
            #             card_data = {
            #                 'name': name,
            #                 'name_power': name_power,
            #                 'image_url': data.get('image', ''),
            #                 'description': data.get('description', ''),
            #                 'card_url': url,
            #                 'reading': reading,
            #             }
                        
            #             # Parse offers
            #             offers = data.get('offers', {})
            #             if isinstance(offers, dict):
            #                 price = offers.get('price', '0')
            #                 try:
            #                     card_data['price'] = int(float(price))
            #                 except (ValueError, TypeError):
            #                     card_data['price'] = 0
            #                 card_data['price_text'] = f"{price} 円"
            #             else:
            #                 card_data['price'] = 0
            #                 card_data['price_text'] = '0 円'
                        
            #             # Extract card ID from URL
            #             card_id_match = re.search(r'/card/[^/]+/(\d+)', url)
            #             card_data['card_id'] = card_id_match.group(1) if card_id_match else ''
                        
            #             return card_data
                        
            #     except json.JSONDecodeError:
            #         continue
            #     except Exception as e:
            #         logger.error(f"Error parsing script in {url}: {e}")
            #         continue
            

            # Find JSON-LD script tags
            # Find JSON-LD script tags
            script_tags = soup.find_all('script', type='application/ld+json')

            # Initialize category variable
            category = ""

            # First pass: extract category from BreadcrumbList
            for script in script_tags:
                try:
                    if script.string is None:
                        continue
                    data = json.loads(script.string)
                    
                    # Look for BreadcrumbList schema to extract category
                    if isinstance(data, dict) and data.get('@type') == 'BreadcrumbList':
                        item_list = data.get('itemListElement', [])
                        # Position 3 (index 2) contains the category
                        if len(item_list) >= 3:
                            position_3 = item_list[2]  # 0-based index: 0=トップ, 1=game, 2=category
                            if isinstance(position_3, dict):
                                category = position_3.get('name', '')
                                if category:
                                    # Clean up category name - remove "販売" if present
                                    category = category.replace(' 販売', '').strip()
                                    logger.info(f"Found category: {category}")
                                    break  # Exit loop once we find the category
                except (json.JSONDecodeError, AttributeError, KeyError) as e:
                    continue

            # Second pass: extract Product data
            for script in script_tags:
                try:
                    if script.string is None:
                        continue
                    data = json.loads(script.string)
                    
                    # Look for Product schema
                    if isinstance(data, dict) and data.get('@type') == 'Product':
                        # Get the name and decode HTML entities
                        name = data.get('name', '')
                    
                        # Decode HTML entities like &amp; to &
                        name = html.unescape(name)

                        name_power = name
                        if reading:
                            name_power = f"{name}({reading})"
                        card_data = {
                            'name': name,
                            'name_power': name_power,
                            'category': category,  # Add category from breadcrumb
                            'image_url': data.get('image', ''),
                            'description': data.get('description', ''),
                            'card_url': url,
                            'reading': reading,
                        }
                        
                        # Parse offers
                        offers = data.get('offers', {})
                        if isinstance(offers, dict):
                            price = offers.get('price', '0')
                            try:
                                card_data['price'] = int(float(price))
                            except (ValueError, TypeError):
                                card_data['price'] = 0
                            card_data['price_text'] = f"{price} 円"
                        else:
                            card_data['price'] = 0
                            card_data['price_text'] = '0 円'
                        
                        # Extract card ID from URL
                        card_id_match = re.search(r'/card/[^/]+/(\d+)', url)
                        card_data['card_id'] = card_id_match.group(1) if card_id_match else ''
                        
                        return card_data


                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"Error parsing script in {url}: {e}")
                    continue

                    
            logger.warning(f"No Product schema found in {url}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            return None
    
    def scrape_card_group(self, group_code: str, ws: str = 'ws',
                          excel_output_path: str = None,
                          progress_callback=None,
                          is_running_callback=None) -> List[CardInfo]:
        """
        Scrape all cards from a specific group with resume/checkpoint support.

        If interrupted, progress is saved to a checkpoint file AND the Excel
        output is updated after every card.  On re-run with the same
        category/group the scraper resumes from where it stopped.

        Args:
            group_code: Group code like 'dc'
            ws: WS identifier (default: 'ws')
            excel_output_path: Path for the Excel file (updated after every card).
            progress_callback: Optional callable(current_index, total).
            is_running_callback: Optional callable() -> bool; False = stop.

        Returns:
            List of all CardInfo objects (previously scraped + new).
        """
        if is_running_callback is None:
            is_running_callback = lambda: True

        logger.info(f"{'='*60}")
        logger.info(f"Starting scrape for group: {group_code} with ws: {ws}")
        logger.info(f"{'='*60}")

        # --- Checkpoint: load previous progress -------------------------
        checkpoint_path = _get_checkpoint_path(self.output_dir, ws, group_code)
        checkpoint = _load_checkpoint(checkpoint_path)

        already_done_urls: set = set(checkpoint.get("processed_urls", []))
        already_cards: List[CardInfo] = []
        for d in checkpoint.get("cards", []):
            try:
                already_cards.append(CardInfo(**d))
            except Exception as e:
                logger.warning(f"Could not restore card from checkpoint: {e}")

        # --- Step 1: Get (or reuse) card links --------------------------
        if checkpoint.get("all_links"):
            card_links = checkpoint["all_links"]
            logger.info(f"Reusing {len(card_links)} card links from checkpoint.")
        else:
            card_links = self._get_card_links_from_search(group_code, ws)
            if not card_links:
                logger.warning(f"No card links found for group {group_code}")
                return []
            checkpoint["all_links"] = card_links
            _save_checkpoint(checkpoint_path, checkpoint)

        total = len(card_links)
        pending_links = [lnk for lnk in card_links if lnk not in already_done_urls]

        if already_cards:
            logger.info(f"Resuming: {len(already_cards)}/{total} done. "
                        f"{len(pending_links)} remaining.")
        else:
            logger.info(f"Found {total} card links, starting to scrape details...")
        
        # --- Step 2: Visit each pending card detail page ---------------
        new_cards: List[CardInfo] = []

        for i, link in enumerate(pending_links, 1):
            if not is_running_callback():
                logger.info("Scraping cancelled by user – progress saved.")
                break

            overall_index = len(already_cards) + len(new_cards) + 1
            logger.info(f"Processing card {overall_index}/{total}: {link}")

            card_data = self._parse_card_from_detail_page(link)

            if card_data:
                try:
                    # Download image if enabled
                    image_filename = ""
                    image_download_success = False

                    if self.download_images and card_data.get('image_url'):
                        image_filename, image_download_success = self._download_image(
                            card_data['image_url'],
                            card_data.get('card_id', 'unknown'),
                            card_data.get('name', 'unknown')
                        )

                    card = CardInfo(
                        name=card_data.get('name', 'Unknown'),
                        name_power=card_data.get('name_power', ''),
                        category=card_data.get('category', ''),
                        price=card_data.get('price', 0),
                        price_text=card_data.get('price_text', '0 円'),
                        image_url=card_data.get('image_url', ''),
                        description=card_data.get('description', ''),
                        card_url=card_data.get('card_url', ''),
                        card_id=card_data.get('card_id', ''),
                        image_filename=image_filename,
                        image_download_success=image_download_success
                    )
                    new_cards.append(card)

                    download_status = "✓" if image_download_success else "✗" if self.download_images else "⊘"
                    logger.info(f"  ✓ {card.name} - {card.price_text} [Image: {download_status}]")

                except Exception as e:
                    logger.error(f"  ✗ Error creating CardInfo: {e}")
            else:
                logger.warning(f"  ✗ No data found for {link}")

            # Mark URL processed and persist checkpoint after every card
            already_done_urls.add(link)
            checkpoint["processed_urls"] = list(already_done_urls)
            checkpoint["cards"] = [asdict(c) for c in (already_cards + new_cards)]
            _save_checkpoint(checkpoint_path, checkpoint)

            # Save partial Excel so data is never lost mid-run
            if excel_output_path:
                try:
                    self.save_to_excel(already_cards + new_cards, excel_output_path)
                except Exception as e:
                    logger.warning(f"Could not flush partial Excel: {e}")

            if progress_callback:
                progress_callback(overall_index, total)


        # --- Finalize ---------------------------------------------------
        all_cards = already_cards + new_cards
        fully_done = len(already_done_urls) >= total

        if fully_done:
            logger.info(f"Completed group {group_code}: {len(all_cards)} cards scraped successfully")
            checkpoint["completed"] = True
            _save_checkpoint(checkpoint_path, checkpoint)
            _delete_checkpoint(checkpoint_path)
        else:
            logger.info(f"Partial scrape for group {group_code}: "
                        f"{len(all_cards)}/{total} cards saved (checkpoint kept).")

        return all_cards
    
    def save_to_csv(self, cards: List[CardInfo], filename: str = None):
        """Save card data to CSV"""
        if not cards:
            logger.warning("No cards to save")
            return
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"yuyutei_cards_{timestamp}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['name', 'name_power', 'category', 'price', 'price_text', 'image_url', 
                             'description', 'card_url', 'card_id', 'image_filename', 
                             'image_download_success']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for card in cards:
                    writer.writerow(card.to_dict())
            logger.info(f"Saved {len(cards)} cards to {filename}")
            print(f"\n✅ CSV file saved as: {filename}")
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
    
    def save_to_excel(self, cards: List[CardInfo], filename: str = None):
        """Save card data to Excel file with optional image preview"""
        if not cards:
            logger.warning("No cards to save")
            return
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"yuyutei_cards_{timestamp}.xlsx"
        
        try:
            # Convert to DataFrame
            data = [card.to_dict() for card in cards]
            df = pd.DataFrame(data)
            
            # Create Excel writer
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Write data to sheet
                df.to_excel(writer, sheet_name='Cards', index=False)
                
                # Auto-adjust column widths
                workbook = writer.book
                worksheet = writer.sheets['Cards']
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
                
                # Add a summary sheet
                self._add_excel_summary_sheet(writer, cards)
            
            logger.info(f"Saved {len(cards)} cards to {filename}")
            print(f"\n✅ Excel file saved as: {filename}")
            
        except ImportError:
            logger.error("pandas or openpyxl not installed. Please install: pip install pandas openpyxl")
            print("\n❌ Excel export requires: pip install pandas openpyxl")
        except Exception as e:
            logger.error(f"Error saving to Excel: {e}")
    
    def _add_excel_summary_sheet(self, writer, cards: List[CardInfo]):
        """Add a summary sheet to the Excel file"""
        try:
            total_cards = len(cards)
            total_price = sum(card.price for card in cards)
            avg_price = total_price // total_cards if total_cards > 0 else 0
            
            # Download statistics
            downloaded = sum(1 for card in cards if card.image_download_success)
            download_percentage = (downloaded / total_cards * 100) if total_cards > 0 else 0
            
            # Top 10 most expensive
            top_cards = sorted(cards, key=lambda x: x.price, reverse=True)[:10]
            
            summary_data = {
                'Metric': [
                    'Total Cards',
                    'Total Value (円)',
                    'Average Price (円)',
                    'Images Downloaded',
                    'Download Success Rate (%)',
                    'Generated Date'
                ],
                'Value': [
                    total_cards,
                    f"{total_price:,}",
                    f"{avg_price:,}",
                    f"{downloaded}/{total_cards}",
                    f"{download_percentage:.1f}",
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
            }
            
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
            
            # Top cards sheet
            top_data = []
            for i, card in enumerate(top_cards, 1):
                top_data.append({
                    'Rank': i,
                    'Name': card.name,
                    'Price': card.price_text,
                    'Card ID': card.card_id,
                    'Image Downloaded': 'Yes' if card.image_download_success else 'No'
                })
            
            if top_data:
                df_top = pd.DataFrame(top_data)
                df_top.to_excel(writer, sheet_name='Top 10 Cards', index=False)
                
        except Exception as e:
            logger.error(f"Error adding summary sheet: {e}")
    
    def save_to_csv_and_excel(self, cards: List[CardInfo], prefix: str = "yuyutei"):
        """Save card data to both CSV and Excel formats"""
        if not cards:
            logger.warning("No cards to save")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # # Save CSV
        # csv_filename = f"{prefix}_{timestamp}.csv"
        # self.save_to_csv(cards, csv_filename)
        
        # Save Excel
        excel_filename = f"{prefix}_{timestamp}.xlsx"
        self.save_to_excel(cards, excel_filename)
        
        # Save a combined summary
        # self._save_summary(cards, f"{prefix}_{timestamp}_summary.txt")
    
    def _save_summary(self, cards: List[CardInfo], filename: str):
        """Save a summary text file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"{'='*60}\n")
                f.write(f"CARD SUMMARY REPORT\n")
                f.write(f"{'='*60}\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Cards: {len(cards)}\n")
                
                if cards:
                    total_price = sum(card.price for card in cards)
                    avg_price = total_price // len(cards)
                    f.write(f"Total Value: {total_price:,} 円\n")
                    f.write(f"Average Price: {avg_price:,} 円\n")
                    
                    # Download statistics
                    downloaded = sum(1 for card in cards if card.image_download_success)
                    f.write(f"\n{'='*60}\n")
                    f.write("IMAGE DOWNLOAD STATISTICS\n")
                    f.write(f"{'='*60}\n")
                    f.write(f"Images successfully downloaded: {downloaded}/{len(cards)}\n")
                    if len(cards) > 0:
                        f.write(f"Download success rate: {(downloaded/len(cards))*100:.1f}%\n")
                    
                    # Failed downloads
                    failed = [card for card in cards if not card.image_download_success and card.image_url]
                    if failed:
                        f.write(f"\nFailed downloads ({len(failed)} cards):\n")
                        for card in failed[:10]:  # Show first 10 failures
                            f.write(f"  - {card.name} (ID: {card.card_id})\n")
                        if len(failed) > 10:
                            f.write(f"  ... and {len(failed) - 10} more\n")
                    
                    # Top 10 most expensive
                    f.write(f"\n{'='*60}\n")
                    f.write("TOP 10 MOST EXPENSIVE CARDS\n")
                    f.write(f"{'='*60}\n")
                    sorted_cards = sorted(cards, key=lambda x: x.price, reverse=True)[:10]
                    for i, card in enumerate(sorted_cards, 1):
                        f.write(f"{i:2d}. {card.name}\n")
                        f.write(f"    Price: {card.price_text}\n")
                        f.write(f"    ID: {card.card_id}\n")
                        f.write(f"    Image: {'✓ Downloaded' if card.image_download_success else '✗ Failed'}\n\n")
            
            logger.info(f"Summary saved to {filename}")
            print(f"\n✅ Summary file saved as: {filename}")
            
        except Exception as e:
            logger.error(f"Error saving summary: {e}")
    
    def print_summary(self, cards: List[CardInfo]):
        """Print summary of scraped cards"""
        if not cards:
            print("No cards found")
            return
        
        print(f"\n{'='*60}")
        print(f"SUMMARY: {len(cards)} cards found")
        print(f"{'='*60}")
        
        total_price = 0
        for card in cards:
            total_price += card.price
        
        print(f"Total cards: {len(cards)}")
        print(f"Total value: {total_price:,} 円")
        if cards:
            print(f"Average price: {total_price // len(cards):,} 円")
        
        # Image download stats
        if self.download_images:
            downloaded = sum(1 for card in cards if card.image_download_success)
            failed = sum(1 for card in cards if not card.image_download_success and card.image_url)
            no_image = sum(1 for card in cards if not card.image_url)
            print(f"\nImage Download Statistics:")
            print(f"  ✓ Successfully downloaded: {downloaded}")
            print(f"  ✗ Failed to download: {failed}")
            print(f"  ⊘ No image URL: {no_image}")
            if len(cards) > 0:
                print(f"  Success rate: {(downloaded/len(cards))*100:.1f}%")
        
        print(f"\nTop 5 most expensive cards:")
        sorted_cards = sorted(cards, key=lambda x: x.price, reverse=True)[:5]
        for i, card in enumerate(sorted_cards, 1):
            print(f"  {i}. {card.name} - {card.price_text}")
            status = "✓" if card.image_download_success else "✗" if card.image_url else "⊘"
            print(f"     Image: {status} {card.image_filename if card.image_filename else 'Not downloaded'}")
        print(f"{'='*60}\n")

def main():
    """Main function"""
    # You can change these parameters here
    group_code = 'dcext1.0'  # Change this to your desired group code
    ws = 'ws'  # Change this to your desired WS value
    
    # Create scraper with image download enabled
    scraper = YuyuteiScraper(delay=0.5, download_images=True, image_dir="card_images")
    
    print(f"\n{'='*60}")
    print(f"SCRAPING CARDS FOR GROUP: {group_code.upper()} with WS: {ws}")
    print(f"IMAGE DOWNLOAD: {'ENABLED' if scraper.download_images else 'DISABLED'}")
    print(f"{'='*60}\n")
    
    cards = scraper.scrape_card_group(group_code, ws)
    
    if cards:
        scraper.print_summary(cards)
        
        # Save to both CSV and Excel
        prefix = f"yuyutei_{group_code}_{ws}"
        scraper.save_to_csv_and_excel(cards, prefix)
        
        # Print sample cards
        print("\n📋 Sample cards (first 3):")
        for i, card in enumerate(cards[:3], 1):
            print(f"\nCard {i}:")
            print(f"  Name: {card.name}")
            print(f"  Price: {card.price_text}")
            print(f"  ID: {card.card_id}")
            print(f"  Description: {card.description}")
            if card.name_power:
                print(f"  Name with reading: {card.name_power}")
            print(f"  Image: {'✓ Downloaded' if card.image_download_success else '✗ Failed' if card.image_url else '⊘ No URL'}")
            if card.image_filename:
                print(f"  Image file: {card.image_filename}")
        
        print(f"\n✅ Scraping complete! Found {len(cards)} cards.")
        print(f"📁 Data saved to CSV, Excel, and images in '{scraper.image_dir}' folder.")
    else:
        print("❌ No cards found. Please check:")
        print("1. Internet connection")
        print("2. Group code (e.g., 'dcext1.0' for D.C./D.C.II)")
        print("3. WS value (e.g., 'ws' or other appropriate value)")
        print("4. The website may have changed its structure")

if __name__ == "__main__":
    main()