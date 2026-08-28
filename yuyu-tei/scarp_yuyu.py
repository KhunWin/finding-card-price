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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CardInfo:
    """Data class to represent a card"""
    name: str
    price: int
    price_text: str
    image_url: str
    description: str  # Card ID (e.g., DC/W01-023S)
    rarity: str
    card_url: str
    availability: str
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
    
    def _get_card_links_from_search(self, group_code: str) -> List[str]:
        """
        Get all card detail page URLs from the search results page
        
        Args:
            group_code: Group code like 'dc'
            
        Returns:
            List of card detail URLs
        """
        search_url = f"{self.BASE_URL}/sell/ws/s/search"
        params = {
            'search_word': '',
            'vers[]': group_code,
            'rare': '',
            'type': '',
            'kizu': '0'
        }
        
        logger.info(f"Fetching search results for group: {group_code}")
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
                if '/sell/ws/card/' in href:
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
            
            # Find JSON-LD script tags
            script_tags = soup.find_all('script', type='application/ld+json')
            
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    
                    # Look for Product schema
                    if isinstance(data, dict) and data.get('@type') == 'Product':
                        card_data = {
                            'name': data.get('name', ''),
                            'image_url': data.get('image', ''),
                            'description': data.get('description', ''),
                            'card_url': url,
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
                            card_data['availability'] = offers.get('availability', 'Unknown')
                        else:
                            card_data['price'] = 0
                            card_data['price_text'] = '0 円'
                            card_data['availability'] = 'Unknown'
                        
                        # Extract card ID from URL
                        card_id_match = re.search(r'/card/[^/]+/(\d+)', url)
                        card_data['card_id'] = card_id_match.group(1) if card_id_match else ''
                        
                        # Extract rarity from the page title or description
                        # The description usually contains the card code (e.g., DC/W01-023S)
                        # The rarity is often at the end of the card code
                        desc = card_data['description']
                        # Try to extract rarity from description
                        rarity_match = re.search(r'[A-Z]{2,}$', desc)
                        card_data['rarity'] = rarity_match.group(0) if rarity_match else 'Unknown'
                        
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
    
    def scrape_card_group(self, group_code: str) -> List[CardInfo]:
        """
        Scrape all cards from a specific group
        
        Args:
            group_code: Group code like 'dc'
            
        Returns:
            List of CardInfo objects
        """
        logger.info(f"{'='*60}")
        logger.info(f"Starting scrape for group: {group_code}")
        logger.info(f"{'='*60}")
        
        # Step 1: Get card links from search results
        card_links = self._get_card_links_from_search(group_code)
        
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
                        price=card_data.get('price', 0),
                        price_text=card_data.get('price_text', '0 円'),
                        image_url=card_data.get('image_url', ''),
                        description=card_data.get('description', ''),
                        # rarity=card_data.get('rarity', 'Unknown'),
                        card_url=card_data.get('card_url', ''),
                        # availability=card_data.get('availability', 'Unknown'),
                        card_id=card_data.get('card_id', '')
                    )
                    cards.append(card)
                    logger.info(f"  ✓ {card.name} - {card.price_text} ({card.rarity})")
                    
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
        
        import csv
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['name', 'price', 'price_text', 'image_url', 
                             'description', 'rarity', 'card_url', 'availability', 'card_id']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for card in cards:
                    writer.writerow(card.to_dict())
            logger.info(f"Saved {len(cards)} cards to {filename}")
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
        
        rarity_counts = {}
        total_price = 0
        for card in cards:
            rarity_counts[card.rarity] = rarity_counts.get(card.rarity, 0) + 1
            total_price += card.price
        
        print(f"Total cards: {len(cards)}")
        print(f"Total value: {total_price:,} 円")
        if cards:
            print(f"Average price: {total_price // len(cards):,} 円")
        print(f"\nRarity breakdown:")
        for rarity, count in sorted(rarity_counts.items()):
            print(f"  {rarity}: {count} cards")
        
        print(f"\nTop 5 most expensive cards:")
        sorted_cards = sorted(cards, key=lambda x: x.price, reverse=True)[:5]
        for i, card in enumerate(sorted_cards, 1):
            print(f"  {i}. {card.name} - {card.price_text} ({card.rarity})")
        print(f"{'='*60}\n")

def main():
    """Main function"""
    scraper = YuyuteiScraper(delay=0.5)
    
    # Scrape DC group
    group_code = 'dc'
    print(f"\n{'='*60}")
    print(f"SCRAPING CARDS FOR GROUP: {group_code.upper()}")
    print(f"{'='*60}\n")
    
    cards = scraper.scrape_card_group(group_code)
    
    if cards:
        scraper.print_summary(cards)
        scraper.save_to_csv(cards)
        
        # Save to JSON
        import json
        with open(f"yuyutei_{group_code}_data.json", 'w', encoding='utf-8') as f:
            json.dump([card.to_dict() for card in cards], f, ensure_ascii=False, indent=2)
        print(f"JSON data saved to yuyutei_{group_code}_data.json")
        
        # Print sample
        print("\nSample cards:")
        for i, card in enumerate(cards[:3], 1):
            print(f"\nCard {i}:")
            print(f"  Name: {card.name}")
            print(f"  Price: {card.price_text}")
            print(f"  Rarity: {card.rarity}")
            print(f"  ID: {card.card_id}")
            print(f"  Description: {card.description}")
    else:
        print("No cards found. Please check:")
        print("1. Internet connection")
        print("2. Group code (use 'dc' for D.C./D.C.II)")
        print("3. The website may have changed its structure")

if __name__ == "__main__":
    main()