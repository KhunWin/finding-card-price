# Database Migration Instructions

## Issue Identified

The `product_keys` table in Supabase has a column length issue:
- Current: `product_key VARCHAR(30)`
- Required: `product_key VARCHAR(50)`

Product keys with " (used)" suffix are 32 characters long, which exceeds the current 30-character limit.

Example failing keys:
- `SCRP-A7K9-M2X4-P8Q1-W5E3 (used)` - 32 characters
- `FULL-A9M7-K3X5-P2Q8-W6E4 (used)` - 32 characters

## Migration Steps

### Option 1: Using Supabase SQL Editor (Recommended)

1. Go to your Supabase dashboard: https://app.supabase.com
2. Select your project
3. Navigate to **SQL Editor** in the left sidebar
4. Create a new query
5. Copy and paste this SQL:

```sql
ALTER TABLE product_keys 
ALTER COLUMN product_key TYPE VARCHAR(50);
```

6. Click **Run** or press `Ctrl+Enter`
7. You should see a success message

### Option 2: Using the provided SQL file

1. Open the file: `database-build/alter_product_key_length.sql`
2. Copy its contents
3. Follow steps 1-6 from Option 1

## Verification

After running the migration, verify the change:

```sql
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'product_keys' 
AND column_name = 'product_key';
```

Expected result:
- `character_maximum_length`: 50

## After Migration

Once the column length is increased, re-run the population script:

```bash
cd database-build
python populate_supabase_keys.py
```

This will:
1. Check for existing keys (should be 96 currently)
2. Ask if you want to clear and repopulate (respond "yes")
3. Insert all 100 keys successfully

## Current Status

✅ Fixed Issues:
- Removed unused import of `ProductKeyManager`
- Fixed file path to `PRODUCT_KEYS.txt`
- Added UTF-8 encoding for file reading
- Updated schema file to use VARCHAR(50)

⚠️ Pending:
- Run the ALTER TABLE command in Supabase (see steps above)
- Re-run populate script after migration

## Files Modified/Created

1. `populate_supabase_keys.py` - Fixed import and file path issues
2. `supabase_schema.sql` - Updated to VARCHAR(50)
3. `alter_product_key_length.sql` - New migration script
4. `migrate_column_length.py` - Helper script with instructions
5. `MIGRATION_INSTRUCTIONS.md` - This file

## Summary of Results (Before Migration)

- Successfully inserted: 96/100 keys
- Failed: 4 keys (all had " (used)" suffix)
- Scraping Only: 49/50 (1 failed)
- Full Access: 47/50 (3 failed)

After migration, all 100 keys should insert successfully.
