# Product Key Usage Policy

## 📋 Overview

The TCG Card Scraper Pro uses a **local-only** product key validation system. This document explains how the keys work and their limitations.

---

## 🔑 How Product Keys Work

### Local Storage System
- Product keys are validated and stored **locally** on each machine
- Activation data is saved in a hidden file: `.product_keys.dat`
- This file is created in the same directory as the application

### Key Activation Process
1. User enters a product key (SCRP-XXXX or FULL-XXXX)
2. System validates the key format and checks if it exists in the master key list
3. If valid, the key is marked as "used" and stored locally with:
   - Activation timestamp
   - Expiration date (1 year from activation)
   - Key type (scraping_only or full_access)

---

## ⚠️ Important Limitations

### Cross-Machine Usage

**The current system CANNOT prevent the same key from being used on multiple machines.**

#### Why?
- Keys are validated **locally** on each computer
- There is **NO central server** or database tracking key usage
- Each machine maintains its own `.product_keys.dat` file
- Machines do not communicate with each other

#### Example Scenario:
```
Machine A: User activates key "SCRP-A7K9-M2X4-P8Q1-W5E3" ✅
Machine B: User can ALSO activate "SCRP-A7K9-M2X4-P8Q1-W5E3" ✅
Machine C: User can ALSO activate "SCRP-A7K9-M2X4-P8Q1-W5E3" ✅
```

**Result:** The same key can be used on unlimited machines because there's no centralized tracking.

---

## 🛡️ Current Protection Features

### What IS Protected:
1. ✅ **Same machine reuse**: Once a key is activated on a machine, it cannot be activated again on that same machine
2. ✅ **Key format validation**: Invalid key formats are rejected
3. ✅ **Key existence check**: Keys not in the master list are rejected
4. ✅ **Expiration enforcement**: Keys expire 1 year after activation
5. ✅ **Key type enforcement**: Scraping keys cannot access Upload features

### What is NOT Protected:
1. ❌ **Cross-machine usage**: Same key can be used on multiple computers
2. ❌ **Key sharing**: Users can share keys with others
3. ❌ **Activation tracking**: No way to know how many times a key has been used globally
4. ❌ **Remote deactivation**: Cannot remotely disable a key once distributed

---

## 💡 Recommendations for Key Distribution

### Best Practices:

1. **Trust-Based Distribution**
   - Only distribute keys to trusted users
   - Keep a manual record of who receives which keys
   - Include usage terms in your distribution agreement

2. **Key Assignment Tracking**
   - Maintain a spreadsheet with:
     - Key ID
     - Assigned to (name/email)
     - Date distributed
     - Key type
     - Notes

3. **Usage Policy Communication**
   - Clearly communicate to users that:
     - Each key is intended for **one user/one machine**
     - Sharing keys violates the license agreement
     - Keys expire after 1 year

4. **Periodic Key Rotation**
   - Generate new keys periodically
   - Retire old keys by not including them in new builds
   - Notify users when keys need renewal

---

## 🔧 Technical Details

### File Location
```
Windows: C:\path\to\application\.product_keys.dat
Linux: /path/to/application/.product_keys.dat
```

### File Format
```json
{
  "SCRP-A7K9-M2X4-P8Q1-W5E3": {
    "type": "scraping_only",
    "activated_at": "2026-08-09T19:10:32",
    "expires_at": "2027-08-09T19:10:32"
  }
}
```

### Security Features
- Keys are hashed using SHA-256 before storage
- File is hidden (starts with `.`)
- JSON format for easy parsing

---

## 🚀 Future Enhancement Options

If you need **true cross-machine protection**, you would need to implement:

### Option 1: Server-Based Validation
- Set up a central server/database
- Each activation sends a request to the server
- Server tracks which keys are in use
- Requires internet connection

### Option 2: Hardware Binding
- Bind keys to specific hardware IDs (MAC address, CPU ID, etc.)
- Key only works on the machine it was first activated on
- More restrictive but prevents sharing

### Option 3: Online Activation Limits
- Allow each key to be activated N times (e.g., 2 machines)
- Track activations on a central server
- Provide deactivation mechanism

**Note:** All these options require significant additional development and infrastructure.

---

## 📞 Support

For questions about key management or to report unauthorized key usage:
- Contact your system administrator
- Review the main documentation in `PRODUCT_KEYS.txt`

---

## 📄 License Agreement Template

When distributing keys, consider including this agreement:

```
PRODUCT KEY LICENSE AGREEMENT

By using this product key, you agree to:

1. Use this key on ONE computer only
2. Not share this key with others
3. Not distribute or publish this key publicly
4. Renew your key after the 1-year expiration period
5. Report any unauthorized use of your key

Violation of these terms may result in:
- Key revocation
- Denial of future key access
- Legal action if applicable

Key ID: [KEY-XXXX-XXXX-XXXX-XXXX]
Issued to: [User Name]
Issue Date: [Date]
Expires: [Date + 1 year]
```

---

**Last Updated:** 2026-08-09  
**Version:** 1.0
