"""
Populate Supabase with Product Keys
This script inserts all 100 product keys into the Supabase database
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
from product_keys import ProductKeyManager

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")

def populate_keys():
    """Insert all product keys into Supabase"""
    
    print("=" * 70)
    print("  POPULATING SUPABASE WITH PRODUCT KEYS")
    print("=" * 70)
    print()
    
    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print(f"✓ Connected to Supabase: {SUPABASE_URL}")
    print()
    
    # Read keys from PRODUCT_KEYS.txt
    scraping_keys = []
    full_access_keys = []
    
    try:
        with open('PRODUCT_KEYS.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('SCRP-'):
                    scraping_keys.append(line)
                elif line.startswith('FULL-'):
                    full_access_keys.append(line)
    except FileNotFoundError:
        print("❌ PRODUCT_KEYS.txt not found!")
        return
    
    print(f"📊 Found {len(scraping_keys)} Scraping Keys")
    print(f"📊 Found {len(full_access_keys)} Full Access Keys")
    print(f"📊 Total: {len(scraping_keys) + len(full_access_keys)} keys")
    print()
    
    # Check if table exists and has data
    try:
        result = supabase.table('product_keys').select('count', count='exact').execute()
        existing_count = result.count if hasattr(result, 'count') else 0
        
        if existing_count > 0:
            print(f"⚠️  Warning: Table already contains {existing_count} keys")
            response = input("Do you want to clear existing keys and repopulate? (yes/no): ")
            if response.lower() == 'yes':
                print("🗑️  Deleting existing keys...")
                supabase.table('product_keys').delete().neq('id', 0).execute()
                print("✓ Existing keys deleted")
            else:
                print("❌ Operation cancelled")
                return
    except Exception as e:
        print(f"ℹ️  Table is empty or doesn't exist yet: {e}")
    
    print()
    print("📤 Inserting keys into Supabase...")
    print()
    
    inserted_count = 0
    failed_count = 0
    
    # Insert scraping keys
    print("Inserting Scraping Keys...")
    for i, key in enumerate(scraping_keys, 1):
        try:
            data = {
                'product_key': key,
                'key_type': 'scraping_only',
                'is_activated': False
            }
            supabase.table('product_keys').insert(data).execute()
            inserted_count += 1
            print(f"  ✓ [{i}/{len(scraping_keys)}] {key}")
        except Exception as e:
            failed_count += 1
            print(f"  ✗ [{i}/{len(scraping_keys)}] {key} - Error: {e}")
    
    print()
    
    # Insert full access keys
    print("Inserting Full Access Keys...")
    for i, key in enumerate(full_access_keys, 1):
        try:
            data = {
                'product_key': key,
                'key_type': 'full_access',
                'is_activated': False
            }
            supabase.table('product_keys').insert(data).execute()
            inserted_count += 1
            print(f"  ✓ [{i}/{len(full_access_keys)}] {key}")
        except Exception as e:
            failed_count += 1
            print(f"  ✗ [{i}/{len(full_access_keys)}] {key} - Error: {e}")
    
    print()
    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"✓ Successfully inserted: {inserted_count} keys")
    if failed_count > 0:
        print(f"✗ Failed to insert: {failed_count} keys")
    print()
    
    # Verify insertion
    try:
        result = supabase.table('product_keys').select('count', count='exact').execute()
        total_count = result.count if hasattr(result, 'count') else 0
        print(f"📊 Total keys in database: {total_count}")
        
        # Count by type
        scraping_result = supabase.table('product_keys').select('count', count='exact').eq('key_type', 'scraping_only').execute()
        full_result = supabase.table('product_keys').select('count', count='exact').eq('key_type', 'full_access').execute()
        
        scraping_count = scraping_result.count if hasattr(scraping_result, 'count') else 0
        full_count = full_result.count if hasattr(full_result, 'count') else 0
        
        print(f"   • Scraping Only: {scraping_count}")
        print(f"   • Full Access: {full_count}")
    except Exception as e:
        print(f"⚠️  Could not verify: {e}")
    
    print()
    print("✅ Database population complete!")
    print()

if __name__ == "__main__":
    populate_keys()
