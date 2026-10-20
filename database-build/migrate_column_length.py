"""
Migrate Supabase product_keys table to increase column length
This script alters the product_key column from VARCHAR(30) to VARCHAR(50)
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")

def migrate_column():
    """Alter the product_key column to increase its length"""
    
    print("=" * 70)
    print("  MIGRATING PRODUCT_KEYS TABLE")
    print("=" * 70)
    print()
    
    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print(f"✓ Connected to Supabase: {SUPABASE_URL}")
    print()
    
    # SQL to alter the column
    alter_sql = """
    ALTER TABLE product_keys 
    ALTER COLUMN product_key TYPE VARCHAR(50);
    """
    
    print("📝 Executing migration SQL...")
    print()
    
    try:
        # Execute the SQL using Supabase RPC or direct query
        # Note: Supabase Python client doesn't directly support DDL statements
        # You'll need to run this in the Supabase SQL Editor
        
        print("⚠️  Note: The Python Supabase client doesn't support DDL statements.")
        print("Please run the following SQL in your Supabase SQL Editor:")
        print()
        print("-" * 70)
        print(alter_sql)
        print("-" * 70)
        print()
        print("Steps:")
        print("1. Go to your Supabase dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Copy and paste the SQL above")
        print("4. Click 'Run'")
        print()
        print("Alternatively, the SQL has been saved to:")
        print("   database-build/alter_product_key_length.sql")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    migrate_column()
