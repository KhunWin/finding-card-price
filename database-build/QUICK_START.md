# Quick Start Guide - Database Population

## 🔴 IMMEDIATE ACTION REQUIRED

You need to run ONE SQL command in Supabase to complete the setup.

## The Problem

The script tried to populate 100 keys but failed on 4 keys because they were too long:
- Current database column size: `VARCHAR(30)`
- Keys with " (used)" suffix: 32 characters
- Result: 96 keys inserted, 4 failed ❌

## The Solution (2 Minutes)

### Step 1: Run SQL in Supabase (30 seconds)

1. Go to: https://app.supabase.com
2. Select your project
3. Click **SQL Editor** in left sidebar
4. Paste this command:

```sql
ALTER TABLE product_keys ALTER COLUMN product_key TYPE VARCHAR(50);
```

5. Click **Run**
6. Done! ✅

### Step 2: Re-populate Database (30 seconds)

In your terminal, run:

```bash
cd database-build
python populate_supabase_keys.py
```

When prompted "Do you want to clear existing keys and repopulate?", type: `yes`

## Expected Result

```
✓ Successfully inserted: 100 keys
📊 Total keys in database: 100
   • Scraping Only: 50
   • Full Access: 50
✅ Database population complete!
```

## What Was Fixed

✅ **Fixed in `populate_supabase_keys.py`:**
1. ✅ Removed unused import (`ProductKeyManager`)
2. ✅ Fixed file path to find `PRODUCT_KEYS.txt`
3. ✅ Added UTF-8 encoding for reading the file

✅ **Files Created:**
1. ✅ `alter_product_key_length.sql` - Migration SQL
2. ✅ `migrate_column_length.py` - Helper with instructions
3. ✅ `MIGRATION_INSTRUCTIONS.md` - Detailed guide
4. ✅ `QUICK_START.md` - This file

✅ **Schema Updated:**
1. ✅ `supabase_schema.sql` - Now uses `VARCHAR(50)`

## Current Status

- Database: 96/100 keys populated
- Missing: 4 keys with " (used)" suffix
- Action needed: Run the ALTER TABLE command above

## Questions?

Read `MIGRATION_INSTRUCTIONS.md` for detailed information.
