# scrape_multiple_groups.py
from scarp_yuyu import YuyuteiScraper
import json
from datetime import datetime

def scrape_all_groups():
    """Scrape multiple Weiss Schwarz card groups"""
    
    # Common Weiss Schwarz groups
    groups = [
        'dc',      # D.C./D.C.II
        # Add more groups as needed
    ]
    
    scraper = YuyuteiScraper(delay=1.5)
    
    all_results = {}
    total_cards = 0
    
    print(f"\n{'='*60}")
    print("SCRAPING MULTIPLE CARD GROUPS")
    print(f"{'='*60}\n")
    
    for group in groups:
        try:
            print(f"\nProcessing group: {group.upper()}")
            cards = scraper.scrape_card_group(group)
            
            if cards:
                all_results[group] = [card.to_dict() for card in cards]
                total_cards += len(cards)
                print(f"✓ Found {len(cards)} cards in group {group.upper()}")
                
                # Save individual group data
                scraper.save_to_csv(cards, filename=f"yuyutei_{group}_{datetime.now().strftime('%Y%m%d')}.csv")
            else:
                print(f"✗ No cards found for group {group.upper()}")
                
        except Exception as e:
            print(f"✗ Error processing group {group.upper()}: {e}")
    
    # Save all results to a single JSON file
    if all_results:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        with open(f"yuyutei_all_groups_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*60}")
        print(f"SUMMARY: Successfully scraped {total_cards} cards from {len(all_results)} groups")
        print(f"Data saved to: yuyutei_all_groups_{timestamp}.json")
        print(f"{'='*60}")

if __name__ == "__main__":
    scrape_all_groups()