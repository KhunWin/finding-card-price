import asyncio
import csv
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import aiohttp
from tcgdexsdk import TCGdex, Language, Query
from tcgdexsdk.enums import Quality, Extension


class TCGdexDataExtractor:
    """
    A class to extract Pokémon TCG card data including prices and images.
    """
    
    def __init__(self, language: str = "en", output_dir: str = "tcg_output"):
        """
        Initialize the TCGdex data extractor.
        
        Args:
            language: Language code for card data (default: "en")
            output_dir: Directory to save output files
        """
        self.sdk = TCGdex(language)
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.csv_file = self.output_dir / f"cards_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Create directories if they don't exist
        self._setup_directories()
        
    def _setup_directories(self) -> None:
        """Create necessary directories for output."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.images_dir.mkdir(parents=True, exist_ok=True)
            print(f"✓ Output directories created: {self.output_dir}")
        except Exception as e:
            print(f"✗ Error creating directories: {e}")
            raise
    
    async def fetch_all_cards(self, query: Optional[Query] = None) -> List:
        """
        Fetch all cards from the API.
        
        Args:
            query: Optional Query object to filter cards
            
        Returns:
            List of card objects
        """
        try:
            print("Fetching cards from TCGdex API...")
            if query:
                cards = await self.sdk.card.list(query)
            else:
                cards = await self.sdk.card.list()
            
            print(f"✓ Successfully fetched {len(cards)} cards")
            return cards
        except Exception as e:
            print(f"✗ Error fetching cards: {e}")
            raise
    
    async def fetch_card_details(self, card_id: str) -> Optional[Dict]:
        """
        Fetch detailed information for a specific card.
        
        Args:
            card_id: The card ID to fetch
            
        Returns:
            Dictionary containing card details or None if error
        """
        try:
            card = await self.sdk.card.get(card_id)
            return card
        except Exception as e:
            print(f"✗ Error fetching card {card_id}: {e}")
            return None
    
    async def download_card_image(self, card, quality: Quality = Quality.HIGH, 
                                  extension: Extension = Extension.PNG) -> Optional[str]:
        """
        Download and save a card image.
        
        Args:
            card: Card object
            quality: Image quality (default: HIGH)
            extension: Image extension (default: PNG)
            
        Returns:
            Path to saved image or None if error
        """
        try:
            # Get image URL
            image_url = card.get_image_url(quality, extension)
            
            if not image_url:
                print(f"✗ No image URL for card {card.id}")
                return None
            
            # Create filename
            filename = f"{card.id}.{extension.value}"
            filepath = self.images_dir / filename
            
            # Download image
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        with open(filepath, 'wb') as f:
                            f.write(image_data)
                        return str(filepath)
                    else:
                        print(f"✗ Failed to download image for {card.id}: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            print(f"✗ Error downloading image for {card.id}: {e}")
            return None
    
    def extract_card_data(self, card) -> Dict:
        """
        Extract relevant data from a card object.
        
        Args:
            card: Card object from TCGdex
            
        Returns:
            Dictionary containing extracted card data
        """
        try:
            data = {
                'id': getattr(card, 'id', ''),
                'name': getattr(card, 'name', ''),
                'local_id': getattr(card, 'localId', ''),
                'illustrator': getattr(card, 'illustrator', ''),
                'rarity': getattr(card, 'rarity', ''),
                'category': getattr(card, 'category', ''),
                'hp': getattr(card, 'hp', ''),
                'types': ', '.join(getattr(card, 'types', [])),
                'stage': getattr(card, 'stage', ''),
                'retreat': getattr(card, 'retreat', ''),
                'regulation_mark': getattr(card, 'regulationMark', ''),
                'dex_id': ', '.join(map(str, getattr(card, 'dexId', []))),
                'set_name': '',
                'set_id': '',
                'serie_name': '',
                'release_date': '',
                'card_count': '',
                'image_url': '',
                'image_path': '',
            }
            
            # Extract set information
            if hasattr(card, 'set') and card.set:
                data['set_name'] = getattr(card.set, 'name', '')
                data['set_id'] = getattr(card.set, 'id', '')
                
                if hasattr(card.set, 'serie'):
                    data['serie_name'] = getattr(card.set.serie, 'name', '')
                
                if hasattr(card.set, 'releaseDate'):
                    data['release_date'] = getattr(card.set, 'releaseDate', '')
                
                if hasattr(card.set, 'cardCount') and card.set.cardCount:
                    data['card_count'] = f"{getattr(card.set.cardCount, 'total', '')}"
            
            # Get image URL
            try:
                data['image_url'] = card.get_image_url(Quality.HIGH, Extension.PNG)
            except Exception as e:
                print(f"✗ Error getting image URL for {card.id}: {e}")
            
            # Note: TCGdex API doesn't provide price data directly
            # Prices would need to be fetched from a separate API like TCGPlayer or CardMarket
            data['price_note'] = 'Price data requires separate API (TCGPlayer/CardMarket)'
            
            return data
            
        except Exception as e:
            print(f"✗ Error extracting data from card: {e}")
            return {}
    
    async def process_cards(self, cards: List, download_images: bool = True, 
                           max_cards: Optional[int] = None) -> List[Dict]:
        """
        Process multiple cards and extract their data.
        
        Args:
            cards: List of card objects
            download_images: Whether to download card images (default: True)
            max_cards: Maximum number of cards to process (None for all)
            
        Returns:
            List of dictionaries containing card data
        """
        processed_data = []
        cards_to_process = cards[:max_cards] if max_cards else cards
        
        print(f"\nProcessing {len(cards_to_process)} cards...")
        
        for idx, card in enumerate(cards_to_process, 1):
            try:
                print(f"Processing card {idx}/{len(cards_to_process)}: {card.id}")
                
                # Fetch detailed card information
                detailed_card = await self.fetch_card_details(card.id)
                
                if not detailed_card:
                    continue
                
                # Extract card data
                card_data = self.extract_card_data(detailed_card)
                
                # Download image if requested
                if download_images and card_data:
                    image_path = await self.download_card_image(detailed_card)
                    card_data['image_path'] = image_path if image_path else ''
                
                processed_data.append(card_data)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"✗ Error processing card {idx}: {e}")
                continue
        
        print(f"\n✓ Successfully processed {len(processed_data)} cards")
        return processed_data
    
    def save_to_csv(self, data: List[Dict]) -> None:
        """
        Save extracted card data to CSV file.
        
        Args:
            data: List of dictionaries containing card data
        """
        try:
            if not data:
                print("✗ No data to save")
                return
            
            # Get all unique keys from all dictionaries
            fieldnames = set()
            for item in data:
                fieldnames.update(item.keys())
            fieldnames = sorted(list(fieldnames))
            
            # Write to CSV
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            print(f"✓ Data saved to: {self.csv_file}")
            print(f"✓ Total records: {len(data)}")
            
        except Exception as e:
            print(f"✗ Error saving to CSV: {e}")
            raise
    
    async def extract_all_data(self, query: Optional[Query] = None, 
                              download_images: bool = True,
                              max_cards: Optional[int] = None) -> None:
        """
        Main method to extract all card data and save to CSV.
        
        Args:
            query: Optional Query object to filter cards
            download_images: Whether to download card images (default: True)
            max_cards: Maximum number of cards to process (None for all)
        """
        try:
            print("=" * 60)
            print("TCGdex Card Data Extraction Started")
            print("=" * 60)
            
            # Fetch all cards
            cards = await self.fetch_all_cards(query)
            
            if not cards:
                print("✗ No cards found")
                return
            
            # Process cards
            processed_data = await self.process_cards(cards, download_images, max_cards)
            
            # Save to CSV
            if processed_data:
                self.save_to_csv(processed_data)
            
            print("\n" + "=" * 60)
            print("Extraction Complete!")
            print("=" * 60)
            print(f"CSV File: {self.csv_file}")
            print(f"Images Directory: {self.images_dir}")
            print(f"Total Cards Processed: {len(processed_data)}")
            
        except Exception as e:
            print(f"\n✗ Fatal error during extraction: {e}")
            raise


async def main():
    """
    Main function to run the TCGdex data extraction.
    """
    try:
        # Initialize extractor
        extractor = TCGdexDataExtractor(language="en", output_dir="tcg_data")
        
        # Example 1: Extract all cards (limited to 50 for demo)
        print("\n--- Example 1: Extract first 50 cards ---")
        await extractor.extract_all_data(
            query=None,
            download_images=True,
            max_cards=50
        )
        
        # Example 2: Extract specific cards with query
        print("\n\n--- Example 2: Extract Charizard cards ---")
        extractor2 = TCGdexDataExtractor(language="en", output_dir="tcg_data_charizard")
        charizard_query = Query().equal("name", "Charizard")
        await extractor2.extract_all_data(
            query=charizard_query,
            download_images=True
        )
        
        # Example 3: Extract high HP Pokemon without downloading images
        print("\n\n--- Example 3: Extract high HP Pokemon (no images) ---")
        extractor3 = TCGdexDataExtractor(language="en", output_dir="tcg_data_high_hp")
        high_hp_query = Query().greaterThan("hp", 200).sort("hp", "desc")
        await extractor3.extract_all_data(
            query=high_hp_query,
            download_images=False,
            max_cards=30
        )
        
    except KeyboardInterrupt:
        print("\n\n✗ Extraction cancelled by user")
    except Exception as e:
        print(f"\n✗ An error occurred: {e}")
        raise


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())