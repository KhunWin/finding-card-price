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
import html  # Added for HTML entity decoding

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CardInfo:
    """Data class to represent a card"""
    name: str
    name_power: str  # Name with reading if available
    price: int
    price_text: str
    image_url: str
    description: str  # Card ID (e.g., DC/W01-023S)
    card_url: str
    card_id: str
    
    def to_dict(self):
        return asdict(self)

class YuyuteiScraper:
    """Scraper for YuYu-Tei card data"""
    
    BASE_URL = "https://yuyu-tei.jp"
    
    def __init__(self, delay: float = 1.0):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
        })
        self.delay = delay
    
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
            
            # Find JSON-LD script tags
            script_tags = soup.find_all('script', type='application/ld+json')
            
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
    
    def scrape_card_group(self, group_code: str, ws: str = 'ws') -> List[CardInfo]:
        """
        Scrape all cards from a specific group
        
        Args:
            group_code: Group code like 'dc'
            ws: WS identifier (default: 'ws')
            
        Returns:
            List of CardInfo objects
        """
        logger.info(f"{'='*60}")
        logger.info(f"Starting scrape for group: {group_code} with ws: {ws}")
        logger.info(f"{'='*60}")
        
        # Step 1: Get card links from search results
        card_links = self._get_card_links_from_search(group_code, ws)
        
        if not card_links:
            logger.warning(f"No card links found for group {group_code}")
            return []
        
        logger.info(f"Found {len(card_links)} card links, starting to scrape details...")
        
        # Step 2: Visit each card detail page
        cards = []
        for i, link in enumerate(card_links, 1):
            logger.info(f"Processing card {i}/{len(card_links)}: {link}")
            
            card_data = self._parse_card_from_detail_page(link)
            
            if card_data:
                try:
                    card = CardInfo(
                        name=card_data.get('name', 'Unknown'),
                        name_power=card_data.get('name_power', ''),
                        price=card_data.get('price', 0),
                        price_text=card_data.get('price_text', '0 円'),
                        image_url=card_data.get('image_url', ''),
                        description=card_data.get('description', ''),
                        card_url=card_data.get('card_url', ''),
                        card_id=card_data.get('card_id', ''),
                        # reading=card_data.get('reading', '')  # Add reading field
                    )
                    cards.append(card)
                    logger.info(f"  ✓ {card.name} - {card.price_text}")
                    
                except Exception as e:
                    logger.error(f"  ✗ Error creating CardInfo: {e}")
            else:
                logger.warning(f"  ✗ No data found for {link}")
            
            # Respectful delay
            if i < len(card_links):
                time.sleep(self.delay)
        
        logger.info(f"Completed group {group_code}: {len(cards)} cards scraped successfully")
        return cards
    
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
                fieldnames = ['name', 'name_power', 'price', 'price_text', 'image_url', 
                             'description', 'card_url', 'card_id']  # Removed reading
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for card in cards:
                    writer.writerow(card.to_dict())
            logger.info(f"Saved {len(cards)} cards to {filename}")
            print(f"\n✅ CSV file saved as: {filename}")
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
    
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
        
        print(f"\nTop 5 most expensive cards:")
        sorted_cards = sorted(cards, key=lambda x: x.price, reverse=True)[:5]
        for i, card in enumerate(sorted_cards, 1):
            print(f"  {i}. {card.name} - {card.price_text}")
        print(f"{'='*60}\n")

def main():
    """Main function"""
    # You can change these parameters here
    group_code = 'dcext1.0'  # Change this to your desired group code
    ws = 'ws'  # Change this to your desired WS value
    
    scraper = YuyuteiScraper(delay=0.5)
    
    print(f"\n{'='*60}")
    print(f"SCRAPING CARDS FOR GROUP: {group_code.upper()} with WS: {ws}")
    print(f"{'='*60}\n")
    
    cards = scraper.scrape_card_group(group_code, ws)
    
    if cards:
        scraper.print_summary(cards)
        
        # Save to CSV (this is the primary output)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f"yuyutei_{group_code}_{ws}_{timestamp}.csv"
        scraper.save_to_csv(cards, csv_filename)
        
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
        
        print(f"\n✅ Scraping complete! Found {len(cards)} cards.")
    else:
        print("❌ No cards found. Please check:")
        print("1. Internet connection")
        print("2. Group code (e.g., 'dcext1.0' for D.C./D.C.II)")
        print("3. WS value (e.g., 'ws' or other appropriate value)")
        print("4. The website may have changed its structure")

if __name__ == "__main__":
    main()