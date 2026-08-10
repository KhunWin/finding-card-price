# Product Key Expiration Testing Guide

## Overview
This guide explains how the product key expiration mechanism works and how to test it without waiting 1 year.

## How Expiration Works

### 1. **Activation Process**
When a user activates a product key:
- The current timestamp is recorded in `activated_at`
- An expiration date is calculated: `activated_at + 365 days` (1 year)
- The expiration date is stored in `expires_at`

**Code Location:** `product_keys_supabase.py` - Line 187-188
```python
activation_time = datetime.utcnow()
expiration_time = activation_time + timedelta(days=365)  # 1 year expiration
```

### 2. **Validation Process**
When validating a key (every time the app starts or a feature is used):
- The system retrieves the `expires_at` timestamp from the database
- Compares it with the current time (`datetime.utcnow()`)
- If `expires_at > current_time` → Key is VALID ✅
- If `expires_at <= current_time` → Key is EXPIRED ❌

**Code Location:** `product_keys_supabase.py` - Lines 160-166
```python
expires_at = datetime.fromisoformat(key_data['expires_at'].replace('Z', '+00:00'))
if expires_at <= datetime.utcnow().replace(tzinfo=expires_at.tzinfo):
    return False, "", "This product key has expired. Please contact support for renewal."
```

### 3. **Access Control**
- `has_scraping_access()` checks for non-expired `scraping_only` or `full_access` keys
- `has_upload_access()` checks for non-expired `full_access` keys only

## Testing Expiration Without Waiting 1 Year

### Method 1: Using the Test Script (Recommended)

We've created `test_expiration.py` to help you test expiration scenarios:

#### Quick Start:
```bash
python test_expiration.py
```

#### Available Test Scenarios:

**A. Test Expired Key (Immediate)**
```
1. Choose option 7 (Run automated expired key test)
2. Enter your product key
3. The script will:
   - Set the key to expired (1 day ago)
   - Validate it
   - Show if expiration detection works
```

**B. Test Real-Time Expiration (2 minutes)**
```
1. Choose option 2 (Set key to expire in X minutes)
2. Enter your product key
3. Enter 2 (or any number of minutes)
4. The script sets expiration to 2 minutes from now
5. Wait 2 minutes
6. Choose option 5 (Validate key status) to confirm it's expired
```

**C. Custom Expiration Testing**
```
1. Choose option 4 (Set custom expiration)
2. Enter your product key
3. Choose your expiration type:
   - Days from now (e.g., 7 days for weekly test)
   - Hours from now (e.g., 24 hours for daily test)
   - Minutes from now (e.g., 5 minutes for quick test)
   - Days ago (e.g., 10 days ago for expired test)
```



### Method 2: Direct Database Manipulation

If you prefer to manually update the database:

1. **Log into Supabase Dashboard**
2. **Go to Table Editor → product_keys**
3. **Find your product key row**
4. **Edit the `expires_at` field:**
   - For expired test: Set to a past date (e.g., `2026-08-09T00:00:00Z`)
   - For expiring soon: Set to a near future date (e.g., 2 minutes from now)

**Example:**
```
Current time: 2026-08-10 10:00:00 UTC
For expired: 2026-08-09 10:00:00 UTC (1 day ago)
For expiring in 2 min: 2026-08-10 10:02:00 UTC
```

## Test Scenarios to Verify

### ✅ Scenario 1: Expired Key Detection
**Goal:** Verify the app rejects expired keys

**Steps:**
1. Use test script option 7 or set `expires_at` to yesterday
2. Try to use scraping feature
3. **Expected:** App should show "Product key has expired" error

### ✅ Scenario 2: Active Key Works
**Goal:** Verify valid keys work normally

**Steps:**
1. Set `expires_at` to 1 year from now (or use option 6 to reset)
2. Try to use scraping/upload features
3. **Expected:** Features should work normally

### ✅ Scenario 3: Key Expires During Use
**Goal:** Verify app detects expiration that occurs while app is running

**Steps:**
1. Set key to expire in 2 minutes
2. Start the app (key should be valid)
3. Wait 2 minutes
4. Try to use a feature
5. **Expected:** App should detect expiration and deny access

### ✅ Scenario 4: Different Key Types
**Goal:** Verify expiration works for both key types

**Steps:**
1. Test with `scraping_only` key (expires)
2. Test with `full_access` key (expires)
3. **Expected:** Both types should respect expiration


## Understanding the Code

### Where Expiration is Checked:

1. **`validate_key()` method** (Line 141-217)
   - Called during key activation
   - Checks if activated key is expired

2. **`has_scraping_access()` method** (Line 219-233)
   - Called when user tries to use scraping feature
   - Filters out expired keys from cache

3. **`has_upload_access()` method** (Line 235-249)
   - Called when user tries to use upload feature
   - Filters out expired full_access keys

### Key Code Sections:

**Expiration Check Logic:**
```python
expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
if expires_at > datetime.utcnow().replace(tzinfo=expires_at.tzinfo):
    # Key is still valid
    return True
else:
    # Key has expired
    return False
```

## Recommended Testing Workflow

### Quick 5-Minute Test:
```bash
# Terminal 1: Run test script
python test_expiration.py

# Choose option 2: Set key to expire in 2 minutes
# Enter your product key
# Enter 2 for minutes

# Terminal 2: Run your app
python main-gui-tkinter.py

# In app: Try to use scraping (should work)
# Wait 2-3 minutes
# In app: Try to use scraping again (should fail with "expired" message)
```

### Comprehensive Test (15 minutes):
1. **Test 1:** Expired key (immediate) - Option 7
2. **Test 2:** Valid key - Option 6 (reset to 1 year)
3. **Test 3:** Expiring soon - Option 2 (2 minutes)
4. **Test 4:** List all keys to verify - Option 1

## Resetting After Testing

After testing, reset your product keys to normal 1-year expiration:

```bash
python test_expiration.py
# Choose option 6: Reset key to 1 year expiration
# Enter your product key
```

Or manually in Supabase:
```sql
UPDATE product_keys 
SET expires_at = NOW() + INTERVAL '365 days'
WHERE product_key = 'YOUR-KEY-HERE';
```

## Important Notes

1. **Timezone:** All timestamps use UTC (Coordinated Universal Time)
2. **Database:** Expiration dates are stored in Supabase, not locally
3. **Cache:** The app caches activated keys, but still checks expiration
4. **No Wait Required:** You can test expiration immediately using past dates

## Troubleshooting

**Q: Key shows as expired but still works**
- Clear app cache and restart
- Check if you're testing with a different key than you think

**Q: Changes in test script don't reflect in app**
- Restart the app to reload data from database
- Check Supabase to verify the update actually happened

**Q: "Connection failed" error**
- Verify `.env` file has correct Supabase credentials
- Check internet connection
- Verify Supabase project is active

## Summary

You **DO NOT** need to wait 1 year to test expiration! 

Use the `test_expiration.py` script to:
- ✅ Set keys to expire in minutes or hours
- ✅ Set keys to already expired (past dates)
- ✅ Validate keys and see their current status
- ✅ Run automated expiration tests
- ✅ Reset keys back to normal after testing

The expiration mechanism is **server-based**, so it works reliably across all machines and cannot be bypassed by changing local system time.

