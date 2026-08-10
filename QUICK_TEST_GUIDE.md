# Quick Expiration Testing Guide

## 🚀 How to Know if Product Key is Expired

### In the Database (Supabase)
```
1. Go to Supabase Dashboard → Table Editor → product_keys
2. Look at the "expires_at" column
3. Compare with current date/time (UTC)
   - If expires_at > current time → ✅ ACTIVE
   - If expires_at <= current time → ❌ EXPIRED
```

### In the Application
When a key is expired, the application will show error messages:
- ❌ "This product key has expired. Please contact support for renewal."
- Features will be disabled (scraping/upload buttons)

---

## 🧪 Testing Expiration (Without Waiting 1 Year!)

### Method 1: Quick Test (2 Minutes) ⚡

**Step 1:** Run the test script
```bash
python test_expiration.py
```

**Step 2:** Choose option 2 (Set key to expire in X minutes)
```
Enter product key: YOUR-KEY-HERE
Enter minutes until expiration: 2
```

**Step 3:** Open your app and verify it works
```bash
python main-gui-tkinter.py
# Try scraping - should work ✅
```

**Step 4:** Wait 2 minutes, then try again
```
# Try scraping again - should show "expired" error ❌
```

---

### Method 2: Instant Expired Test ⚡⚡

**Step 1:** Run the automated test
```bash
python test_expiration.py
```

**Step 2:** Choose option 7 (Run automated expired key test)
```
Enter product key: YOUR-KEY-HERE
```

**Step 3:** The script will:
- Set the key to expired (1 day ago)
- Test validation
- Show ✅ or ❌ if expiration detection works

---

## 📋 All Test Script Options

```
python test_expiration.py
```

**Menu:**
```
1. List all product keys           → See all keys and their status
2. Set key to expire in X minutes  → Quick real-time test (2-5 min)
3. Set key to expired (1 day ago)  → Instant expired state
4. Set custom expiration           → Set any date you want
5. Validate key status             → Check if key is currently valid
6. Reset key to 1 year expiration  → Return to normal after testing
7. Run automated expired key test  → Full automated test
0. Exit
```

---

## 🔄 After Testing: Reset Keys

Always reset your keys back to normal 1-year expiration after testing:

```bash
python test_expiration.py
# Choose option 6
# Enter your product key
```

Or manually in Supabase:
```sql
UPDATE product_keys 
SET expires_at = NOW() + INTERVAL '365 days'
WHERE product_key = 'YOUR-KEY-HERE';
```

---

## ✅ Test Checklist

- [ ] Test 1: Key expires immediately (option 7)
- [ ] Test 2: Key expires in 2 minutes (option 2)
- [ ] Test 3: Verify expired key is rejected in app
- [ ] Test 4: Reset key and verify it works again (option 6)
- [ ] Test 5: List all keys to see their status (option 1)

---

## 📝 Important Notes

1. **All times are in UTC** (Coordinated Universal Time)
2. **Changes are server-based** (stored in Supabase, not locally)
3. **Restart your app** after changing expiration dates to see the effect
4. **You manually deleted** the `machine_name` column - this is fine, the code has been updated

---

## 🐛 Troubleshooting

**Q: I changed expiration but app still works**
→ Restart the application

**Q: Script says "Key not found"**
→ Check you typed the product key correctly (case-sensitive)

**Q: Connection error**
→ Check your `.env` file has correct Supabase credentials

---

## 📚 For More Details

See `EXPIRATION_TESTING_GUIDE.md` for complete documentation.
