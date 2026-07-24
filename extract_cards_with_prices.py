import asyncio
import csv
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import aiohttp
from tcgdexsdk import TCGdex, Query
from tcgdexsdk.enums import Quality, Extension


class TCGdexCardExtractorWithPrices:
    """
    A class to extract specific Pokémon TCG cards by their names from a CSV file,
    including price information.
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
        self.csv_file = self.output_dir / f"cards_with_prices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
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
            Filename (not full path) of saved image or None if error
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
            
            # Download image with timeout
            timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        with open(filepath, 'wb') as f:
                            f.write(image_data)
                        print(f"  ✓ Image downloaded: {filename}")
                        return filename  # Return just the filename, not full path
                    else:
                        print(f"  ✗ Failed to download image for {card.id}: HTTP {response.status}")
                        return None
                        
        except asyncio.TimeoutError:
            print(f"  ✗ Timeout downloading image for {card.id}")
            return None
        except Exception as e:
            print(f"  ✗ Error downloading image for {card.id}: {e}")
            return None
    
    def extract_prices(self, card) -> List[str]:
        """
        Extract price information from a card object.
        
        Args:
            card: Card object from TCGdex
            
        Returns:
            List of price strings
        """
        prices = []
        
        try:
            # Check if card has tcgplayer attribute
            if hasattr(card, 'tcgplayer') and card.tcgplayer:
                tcgplayer = card.tcgplayer
                
                # Check for prices in tcgplayer data
                if hasattr(tcgplayer, 'prices') and tcgplayer.prices:
                    for price_type, price_data in tcgplayer.prices.items():
                        if isinstance(price_data, dict):
                            # Extract different price points (market, low, mid, high)
                            for price_key, price_value in price_data.items():
                                if price_value is not None:
                                    prices.append(f"${price_value}")
                        elif price_data is not None:
                            prices.append(f"${price_data}")
            
            # Check if card has cardmarket attribute
            if hasattr(card, 'cardmarket') and card.cardmarket:
                cardmarket = card.cardmarket
                
                # Check for prices in cardmarket data
                if hasattr(cardmarket, 'prices') and cardmarket.prices:
                    for price_type, price_value in cardmarket.prices.items():
                        if price_value is not None:
                            prices.append(f"€{price_value}")
            
            if prices:
                print(f"  ✓ Found {len(prices)} price(s)")
            else:
                print(f"  ⚠ No prices found for this card")
                
        except Exception as e:
            print(f"  ✗ Error extracting prices: {e}")
        
        return prices
    
    def extract_card_data(self, card, image_filename: Optional[str]) -> Dict:
        """
        Extract relevant data from a card object in simplified format.
        
        Args:
            card: Card object from TCGdex
            image_filename: Filename of the downloaded image
            
        Returns:
            Dictionary containing card name, prices, and image filename
        """
        try:
            # Extract prices
            prices = self.extract_prices(card)
            
            # Format prices as a list string
            prices_str = str(prices) if prices else "[]"
            
            data = {
                'name': getattr(card, 'name', ''),
                'prices': prices_str,
                'image': image_filename if image_filename else ''
            }
            
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
                    # Add entry with no data
                    processed_data.append({
                        'name': card_name,
                        'prices': '[]',
                        'image': ''
                    })
                    continue
                
                # Process each matching card
                for card_idx, card in enumerate(matching_cards, 1):
                    print(f"  Processing variant {card_idx}/{len(matching_cards)}: {card.id}")
                    
                    # Fetch detailed card information
                    detailed_card = await self.fetch_card_details(card.id)
                    
                    if not detailed_card:
                        continue
                    
                    # Download image if requested
                    image_filename = None
                    if download_images:
                        image_filename = await self.download_card_image(detailed_card)
                    
                    # Extract card data
                    card_data = self.extract_card_data(detailed_card, image_filename)
                    
                    if card_data:
                        processed_data.append(card_data)
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"  ✗ Error processing '{card_name}': {e}")
                continue
        
        print("\n" + "=" * 60)
        print(f"✓ Successfully processed {len(processed_data)} card entries")
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
            
            # Define fieldnames in specific order
            fieldnames = ['name', 'prices', 'image']
            
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
            print("TCGdex Card Extraction with Prices - Started")
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
            print(f"Total Card Entries: {len(processed_data)}")
            
        except Exception as e:
            print(f"\n✗ Fatal error during extraction: {e}")
            raise


async def main():
    """
    Main function to run the card extraction with prices.
    """
    try:
        # Initialize extractor with input CSV file
        input_csv = "card_names.csv"  # Change this to your CSV file path
        
        extractor = TCGdexCardExtractorWithPrices(
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
