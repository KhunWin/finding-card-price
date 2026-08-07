import asyncio
import csv
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import aiohttp
from tcgdexsdk import TCGdex, Query
from tcgdexsdk.enums import Quality, Extension


class TCGdexCardExtractorByName:
    """
    A class to extract specific Pokémon TCG cards by their names from a CSV file.
    """
    
    def __init__(self, input_csv: str, language: str = "en", output_dir: str = "tcg_output"):
        """
        Initialize the TCGdex card extractor.
        
        Args:
            input_csv: Path to CSV file containing card names
            language: Language code for card data (default: "en")
            output_dir: Directory to save output files
        """
        self.sdk = TCGdex(language)
        self.input_csv = Path(input_csv)
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
    
    def read_card_names_from_csv(self) -> List[str]:
        """
        Read card names from the input CSV file.
        
        Returns:
            List of card names
        """
        try:
            if not self.input_csv.exists():
                raise FileNotFoundError(f"Input CSV file not found: {self.input_csv}")
            
            card_names = []
            with open(self.input_csv, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Check if 'name' column exists
                if 'name' not in reader.fieldnames:
                    raise ValueError("CSV file must contain a 'name' column")
                
                for row in reader:
                    name = row['name'].strip()
                    if name:  # Skip empty names
                        card_names.append(name)
            
            print(f"✓ Read {len(card_names)} card names from {self.input_csv}")
            return card_names
            
        except Exception as e:
            print(f"✗ Error reading CSV file: {e}")
            raise
    
    async def search_card_by_name(self, card_name: str) -> List:
        """
        Search for cards by name using the TCGdex API.
        
        Args:
            card_name: Name of the card to search for
            
        Returns:
            List of matching card objects
        """
        try:
            print(f"  Searching for: {card_name}")
            
            # Create a query to search by name
            query = Query().equal("name", card_name)
            cards = await self.sdk.card.list(query)
            
            if cards:
                print(f"  ✓ Found {len(cards)} card(s) matching '{card_name}'")
            else:
                print(f"  ✗ No cards found for '{card_name}'")
            
            return cards
            
        except Exception as e:
            print(f"  ✗ Error searching for card '{card_name}': {e}")
            return []
    
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
            print(f"  ✗ Error fetching card details for {card_id}: {e}")
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
                print(f"  ✗ No image URL for card {card.id}")
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
                        print(f"  ✓ Image downloaded: {filename}")
                        return str(filepath)
                    else:
                        print(f"  ✗ Failed to download image for {card.id}: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            print(f"  ✗ Error downloading image for {card.id}: {e}")
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
                print(f"  ✗ Error getting image URL for {card.id}: {e}")
            
            return data
            
        except Exception as e:
            print(f"  ✗ Error extracting data from card: {e}")
            return {}
    
    async def process_card_names(self, card_names: List[str], download_images: bool = True) -> List[Dict]:
        """
        Process cards by searching for each name and extracting their data.
        
        Args:
            card_names: List of card names to search for
            download_images: Whether to download card images (default: True)
            
        Returns:
            List of dictionaries containing card data
        """
        processed_data = []
        
        print(f"\nProcessing {len(card_names)} card names...")
        print("=" * 60)
        
        for idx, card_name in enumerate(card_names, 1):
            try:
                print(f"\n[{idx}/{len(card_names)}] Processing: {card_name}")
                
                # Search for cards by name
                matching_cards = await self.search_card_by_name(card_name)
                
                if not matching_cards:
                    print(f"  ⚠ Skipping '{card_name}' - no matches found")
                    continue
                
                # Process each matching card
                for card_idx, card in enumerate(matching_cards, 1):
                    print(f"  Processing variant {card_idx}/{len(matching_cards)}: {card.id}")
                    
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
                print(f"  ✗ Error processing '{card_name}': {e}")
                continue
        
        print("\n" + "=" * 60)
        print(f"✓ Successfully processed {len(processed_data)} cards")
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
    
    async def extract_cards_from_csv(self, download_images: bool = True) -> None:
        """
        Main method to extract card data based on names from CSV file.
        
        Args:
            download_images: Whether to download card images (default: True)
        """
        try:
            print("=" * 60)
            print("TCGdex Card Extraction by Name - Started")
            print("=" * 60)
            
            # Read card names from CSV
            card_names = self.read_card_names_from_csv()
            
            if not card_names:
                print("✗ No card names found in CSV")
                return
            
            # Process cards
            processed_data = await self.process_card_names(card_names, download_images)
            
            # Save to CSV
            if processed_data:
                self.save_to_csv(processed_data)
            else:
                print("\n✗ No cards were successfully processed")
            
            print("\n" + "=" * 60)
            print("Extraction Complete!")
            print("=" * 60)
            print(f"Input CSV: {self.input_csv}")
            print(f"Output CSV: {self.csv_file}")
            print(f"Images Directory: {self.images_dir}")
            print(f"Total Cards Processed: {len(processed_data)}")
            
        except Exception as e:
            print(f"\n✗ Fatal error during extraction: {e}")
            raise


async def main():
    """
    Main function to run the card extraction by name.
    """
    try:
        # Initialize extractor with input CSV file
        input_csv = "card_names.csv"  # Change this to your CSV file path
        
        extractor = TCGdexCardExtractorByName(
            input_csv=input_csv,
            language="en",
            output_dir="tcg_data"
        )
        
        # Extract cards based on names in CSV
        await extractor.extract_cards_from_csv(download_images=True)
        
    except KeyboardInterrupt:
        print("\n\n✗ Extraction cancelled by user")
    except Exception as e:
        print(f"\n✗ An error occurred: {e}")
        raise


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
