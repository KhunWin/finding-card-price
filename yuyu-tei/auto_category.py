import re
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

class CardExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def fetch_html(self, url):
        """Fetch HTML content from URL."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_cards(self, html_content):
        """Extract card data from HTML."""
        cards = []
        
        # Find the card list section
        start_marker = '全選択'
        end_marker = 'ReturnCheckStatusVersPhone'
        
        start_idx = html_content.find(start_marker)
        if start_idx == -1:
            print("Could not find start marker")
            return []
        
        end_idx = html_content.find(end_marker, start_idx)
        if end_idx == -1:
            print("Could not find end marker")
            return []
        
        section = html_content[start_idx:end_idx]
        
        # Extract input-label pairs
        pattern = r'<input[^>]*value="([^"]+)"[^>]*>.*?<label[^>]*>\s*([^<]+?)\s*</label>'
        matches = re.findall(pattern, section, re.DOTALL)
        
        for value, label_text in matches:
            label_text = ' '.join(label_text.split())
            if not label_text:
                continue
            
            # Check for bracketed code
            bracketed_match = re.match(r'\[([A-Za-z0-9\.]+)\]\s*(.+)', label_text)
            if bracketed_match:
                code = bracketed_match.group(1)
                name = bracketed_match.group(2).strip()
            else:
                code = value
                name = label_text
            
            # Filter out common non-card items
            if not self.is_card_item(name, code):
                continue
            
            cards.append((name, code))
        
        # Remove duplicates
        seen = set()
        unique_cards = []
        for name, code in cards:
            if code not in seen:
                seen.add(code)
                unique_cards.append((name, code))
        
        return unique_cards
    
    def is_card_item(self, name, code):
        """Filter out non-card items like buttons, links, etc."""
        # Skip items that are clearly not cards
        skip_patterns = [
            r'^全選択$',
            r'^全解除$',
            r'^閉じる$',
            r'^検索$',
            r'^ページ$',
            r'^[0-9]+$',  # Just numbers
        ]
        
        for pattern in skip_patterns:
            if re.match(pattern, name):
                return False
        
        # Skip items with very short names
        if len(name) < 2:
            return False
        
        return True
    
    def process_game(self, game_type):
        """Process a single game type."""
        url = f"https://yuyu-tei.jp/top/{game_type}"
        print(f"\nProcessing: {game_type.upper()}")
        print(f"URL: {url}")
        
        html_content = self.fetch_html(url)
        if not html_content:
            return []
        
        cards = self.extract_cards(html_content)
        
        if cards:
            output_file = f"cards_{game_type}.csv"
            self.save_to_csv(cards, output_file)
            self.print_cards(cards, game_type)
        else:
            print(f"No cards found for {game_type}")
        
        return cards
    
    def process_all_games(self):
        """Process all game types."""
        game_types = ['yrd','dm']
        all_cards = {}
        
        print("=" * 70)
        print("STARTING CARD EXTRACTION")
        print("=" * 70)
        
        for game_type in game_types:
            cards = self.process_game(game_type)
            if cards:
                all_cards[game_type] = cards
            time.sleep(1)  # Be respectful to the server
        
        # self.save_combined_summary(all_cards)
        self.print_summary(all_cards)
        
        return all_cards
    
    def save_to_csv(self, cards, filename):
        """Save cards to CSV."""
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Display Name', 'Card Code'])
            for name, code in cards:
                writer.writerow([f'[{code}] {name}', code])
        print(f"  ✓ Saved {len(cards)} cards to: {filename}")
    
    def save_combined_summary(self, all_cards, filename='cards_all_games.csv'):
        """Save combined summary."""
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Game Type', 'Display Name', 'Card Code'])
            for game_type, cards in all_cards.items():
                for name, code in cards:
                    writer.writerow([game_type, f'[{code}] {name}', code])
        print(f"\n✓ Saved combined summary to: {filename}")
    
    def print_cards(self, cards, game_type, limit=5):
        """Print cards in requested format."""
        print(f"\n  Cards extracted ({len(cards)} total):")
        print("  " + "-" * 40)
        for i, (name, code) in enumerate(cards[:limit]):
            print(f"  [{code}] {name}, {code}")
        if len(cards) > limit:
            print(f"  ... and {len(cards) - limit} more cards")
        print("  " + "-" * 40)
    
    def print_summary(self, all_cards):
        """Print summary of all processed games."""
        print("\n" + "=" * 70)
        print("EXTRACTION COMPLETE - SUMMARY")
        print("=" * 70)
        total_cards = 0
        for game_type, cards in all_cards.items():
            count = len(cards)
            total_cards += count
            print(f"  {game_type.upper()}: {count} cards")
        print(f"\n  TOTAL: {total_cards} cards extracted")
        print("=" * 70)

def main():
    """Main entry point."""
    extractor = CardExtractor()
    
    # Process all game types
    extractor.process_all_games()
    
    # Alternatively, process a single game:
    # extractor.process_game('vg')

if __name__ == "__main__":
    main()