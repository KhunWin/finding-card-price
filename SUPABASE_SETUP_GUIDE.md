# 🚀 Supabase Setup Guide - Server-Based Product Key System

This guide will help you set up the server-based product key validation system using Supabase.

---

## 📋 Prerequisites

- Supabase account (already configured in `.env` file)
- Python 3.7+ installed
- Required packages installed (see Installation section)

---

## 🔧 Installation Steps

### Step 1: Install Required Packages

```bash
pip install -r requirements.txt
```

This will install:
- `supabase` - Supabase Python client
- `python-dotenv` - Environment variable management
- Other dependencies (selenium, openpyxl, pandas, webdriver-manager)

---

### Step 2: Create Database Table

You have **two options** to create the table:

#### Option A: Using Supabase SQL Editor (Recommended)

1. **Run the setup script** to generate the SQL:
   ```bash
   python3 setup_supabase_tables.py
   ```

2. **Copy the SQL** from the output or from `supabase_schema.sql`

3. **Open Supabase SQL Editor**:
   - Go to: https://najsttsptlnqhcupxnbn.supabase.co/project/_/sql
   - Click "New Query"

4. **Paste and execute** the SQL schema

5. **Verify** the table was created:
   - Go to Table Editor
   - You should see `product_keys` table

#### Option B: Manual Table Creation

If you prefer, create the table manually with these columns:

| Column | Type | Constraints |
|--------|------|-------------|
| id | BIGSERIAL | PRIMARY KEY |
| product_key | VARCHAR(30) | UNIQUE, NOT NULL |
| key_type | VARCHAR(20) | NOT NULL, CHECK (scraping_only or full_access) |
| is_activated | BOOLEAN | DEFAULT FALSE |
| machine_id | VARCHAR(255) | NULL |
| machine_name | VARCHAR(255) | NULL |
| activated_at | TIMESTAMPTZ | NULL |
| expires_at | TIMESTAMPTZ | NULL |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() |

---

### Step 3: Populate Product Keys

Once the table is created, populate it with the 100 product keys:

```bash
python3 populate_supabase_keys.py
```

**Expected Output:**
```
======================================================================
  POPULATING SUPABASE WITH PRODUCT KEYS
======================================================================

✓ Connected to Supabase: https://najsttsptlnqhcupxnbn.supabase.co

📊 Found 50 Scraping Keys
📊 Found 50 Full Access Keys
📊 Total: 100 keys

📤 Inserting keys into Supabase...

Inserting Scraping Keys...
  ✓ [1/50] SCRP-A7K9-M2X4-P8Q1-W5E3
  ✓ [2/50] SCRP-B3N8-L6R2-T9Y4-K1F7
  ...

Inserting Full Access Keys...
  ✓ [1/50] FULL-X9Z2-C5V8-N3M6-Q1W4
  ✓ [2/50] FULL-D7H4-J2K9-P6L3-R8T5
  ...

======================================================================
  SUMMARY
======================================================================
✓ Successfully inserted: 100 keys

📊 Total keys in database: 100
   • Scraping Only: 50
   • Full Access: 50

✅ Database population complete!
```

---

### Step 4: Verify Setup

Test the connection and key validation:

```bash
python3 test_supabase_connection.py
```

This will:
1. Check Supabase connection
2. Verify table exists
3. Test key validation
4. Test key activation

---

## 🔑 How It Works

### Machine Identification

Each machine is uniquely identified by:
- **MAC Address** - Network hardware identifier
- **Hostname** - Computer name
- **Platform Info** - OS and system details

These are combined and hashed to create a unique `machine_id`.

### Key Activation Flow

```
1. User enters product key
   ↓
2. System validates key format (SCRP-XXXX or FULL-XXXX)
   ↓
3. Check if key exists in Supabase database
   ↓
4. Check if key is already activated
   ├─ If activated on THIS machine → Allow access
   ├─ If activated on DIFFERENT machine → Reject
   └─ If not activated → Activate for this machine
   ↓
5. Store activation data:
   - machine_id (unique hash)
   - machine_name (human-readable)
   - activated_at (timestamp)
   - expires_at (1 year from activation)
```

### Cross-Machine Protection

✅ **Protected:**
- Same key **CANNOT** be used on multiple machines
- Once activated on Machine A, it's locked to Machine A
- Other machines will be rejected

✅ **Tracked:**
- Which machine activated the key
- When it was activated
- When it expires

---

## 📊 Database Schema

### Table: `product_keys`

```sql
CREATE TABLE product_keys (
    id BIGSERIAL PRIMARY KEY,
    product_key VARCHAR(30) UNIQUE NOT NULL,
    key_type VARCHAR(20) NOT NULL,
    is_activated BOOLEAN DEFAULT FALSE,
    machine_id VARCHAR(255),
    machine_name VARCHAR(255),
    activated_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Example Data

| product_key | key_type | is_activated | machine_id | machine_name | activated_at | expires_at |
|-------------|----------|--------------|------------|--------------|--------------|------------|
| SCRP-A7K9-M2X4-P8Q1-W5E3 | scraping_only | TRUE | abc123... | MyPC (Windows) | 2026-08-10 | 2027-08-10 |
| FULL-X9Z2-C5V8-N3M6-Q1W4 | full_access | FALSE | NULL | NULL | NULL | NULL |

---

## 🔐 Security Features

### Row Level Security (RLS)

The table has RLS enabled with policies:

1. **Service Role** - Full access (for admin operations)
2. **Anonymous/Authenticated Users** - Can:
   - Read product keys
   - Activate unactivated keys
   - Cannot deactivate or modify activated keys

### Key Expiration

- Keys expire **1 year** after activation
- Expired keys are automatically rejected
- Users must renew their keys after expiration

### Machine Binding

- Keys are bound to the first machine that activates them
- Machine ID is a SHA-256 hash of hardware identifiers
- Cannot be transferred to another machine

---

## 🧪 Testing

### Test Connection

```python
from product_keys_supabase import SupabaseProductKeyManager

manager = SupabaseProductKeyManager()
success, message = manager.check_connection()
print(message)
```

### Test Key Activation

```python
# Activate a scraping key
success, key_type, message = manager.activate_key("SCRP-A7K9-M2X4-P8Q1-W5E3")
print(f"Success: {success}")
print(f"Type: {key_type}")
print(f"Message: {message}")

# Check access
has_scraping = manager.has_scraping_access()
has_upload = manager.has_upload_access()
print(f"Scraping Access: {has_scraping}")
print(f"Upload Access: {has_upload}")
```

---

## 📦 Building .exe with Supabase

When building the .exe file, ensure:

1. **Include .env file** in the build
2. **Bundle Supabase package** and dependencies
3. **Test on target machine** before distribution

Update `build_exe.py`:

```python
# Add to data_files
data_files = [
    ('.', ['.env']),  # Include .env file
    # ... other files
]

# Add to packages
packages = [
    'supabase',
    'python-dotenv',
    # ... other packages
]
```

---

## 🚨 Troubleshooting

### Connection Failed

**Error:** `Connection failed: ...`

**Solutions:**
1. Check `.env` file has correct credentials
2. Verify Supabase project is active
3. Check internet connection
4. Verify firewall isn't blocking Supabase

### Table Not Found

**Error:** `relation "product_keys" does not exist`

**Solutions:**
1. Run `setup_supabase_tables.py` to generate SQL
2. Execute SQL in Supabase SQL Editor
3. Verify table was created in Table Editor

### Key Already Activated

**Error:** `This product key has already been activated on another machine`

**Solutions:**
1. This is expected behavior (cross-machine protection)
2. Use a different key for the new machine
3. If you need to reset a key, manually update it in Supabase:
   ```sql
   UPDATE product_keys 
   SET is_activated = FALSE, 
       machine_id = NULL, 
       machine_name = NULL,
       activated_at = NULL,
       expires_at = NULL
   WHERE product_key = 'SCRP-XXXX-XXXX-XXXX-XXXX';
   ```

### Import Error

**Error:** `ModuleNotFoundError: No module named 'supabase'`

**Solution:**
```bash
pip install supabase python-dotenv
```

---

## 📞 Support

For issues or questions:
1. Check this guide first
2. Review `KEY_USAGE_POLICY.md` for key management
3. Check Supabase logs in dashboard
4. Verify `.env` credentials are correct

---

## 🎯 Next Steps

After setup is complete:

1. ✅ Test the application with a test key
2. ✅ Verify cross-machine protection works
3. ✅ Build the .exe file
4. ✅ Distribute keys to users
5. ✅ Keep a record of which keys are assigned to whom

---

**Last Updated:** 2026-08-10  
**Version:** 1.0
