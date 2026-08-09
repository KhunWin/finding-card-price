#!/usr/bin/env python3
"""
Product Key Testing Script
Tests the validity and functionality of the product key system
"""

import os
import sys
from datetime import datetime, timedelta
from product_keys import ProductKeyManager


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_test(test_name, passed, message=""):
    """Print test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status} - {test_name}")
    if message:
        print(f"      {message}")


def test_key_validation():
    """Test basic key validation"""
    print_header("TEST 1: Key Validation")
    
    manager = ProductKeyManager()
    
    # Test 1.1: Valid scraping key
    is_valid, key_type, msg = manager.validate_key("SCRP-A7K9-M2X4-P8Q1-W5E3")
    print_test("Valid Scraping Key", is_valid and key_type == manager.KEY_TYPE_SCRAPING, msg)
    
    # Test 1.2: Valid full access key
    is_valid, key_type, msg = manager.validate_key("FULL-A9M7-K3X5-P2Q8-W6E4")
    print_test("Valid Full Access Key", is_valid and key_type == manager.KEY_TYPE_FULL, msg)
    
    # Test 1.3: Invalid key
    is_valid, key_type, msg = manager.validate_key("INVALID-KEY-1234-5678-9012")
    print_test("Invalid Key Detection", not is_valid, msg)
    
    # Test 1.4: Case insensitivity
    is_valid, key_type, msg = manager.validate_key("scrp-a7k9-m2x4-p8q1-w5e3")
    print_test("Case Insensitive Validation", is_valid, msg)
    
    # Test 1.5: Key with spaces
    is_valid, key_type, msg = manager.validate_key("SCRP A7K9 M2X4 P8Q1 W5E3")
    print_test("Key with Spaces", is_valid, msg)


def test_key_activation():
    """Test key activation"""
    print_header("TEST 2: Key Activation")
    
    # Clean up any existing test data
    test_file = '.product_keys.dat'
    if os.path.exists(test_file):
        os.remove(test_file)
    
    manager = ProductKeyManager()
    
    # Test 2.1: Activate scraping key
    success, key_type, msg = manager.activate_key("SCRP-B3N6-L9Y2-R4T7-U1I8")
    print_test("Activate Scraping Key", success and key_type == manager.KEY_TYPE_SCRAPING, msg)
    
    # Test 2.2: Try to use same key again
    success, key_type, msg = manager.activate_key("SCRP-B3N6-L9Y2-R4T7-U1I8")
    print_test("Prevent Duplicate Activation", not success, msg)
    
    # Test 2.3: Activate full access key
    success, key_type, msg = manager.activate_key("FULL-B5N8-L2Y4-R6T9-U3I1")
    print_test("Activate Full Access Key", success and key_type == manager.KEY_TYPE_FULL, msg)
    
    # Test 2.4: Check scraping access
    has_access = manager.has_scraping_access()
    print_test("Has Scraping Access", has_access, "User should have scraping access")
    
    # Test 2.5: Check upload access
    has_access = manager.has_upload_access()
    print_test("Has Upload Access", has_access, "User should have upload access")


def test_key_expiration():
    """Test key expiration functionality"""
    print_header("TEST 3: Key Expiration")
    
    # Clean up any existing test data
    test_file = '.product_keys.dat'
    if os.path.exists(test_file):
        os.remove(test_file)
    
    manager = ProductKeyManager()
    
    # Test 3.1: Activate a key and check expiration date
    success, key_type, msg = manager.activate_key("SCRP-C8H5-K1M3-V6B9-N2J4")
    print_test("Key Activation with Expiration", success, msg)
    
    # Test 3.2: Verify expiration is set to 1 year from now
    key_data = manager.used_keys.get("SCRP-C8H5-K1M3-V6B9-N2J4")
    if key_data:
        expires_at = datetime.fromisoformat(key_data["expires_at"])
        activated_at = datetime.fromisoformat(key_data["activated_at"])
        days_diff = (expires_at - activated_at).days
        print_test("Expiration Set to 1 Year", 364 <= days_diff <= 366, 
                   f"Expires in {days_diff} days")
    
    # Test 3.3: Manually create an expired key
    expired_key = "SCRP-D4F7-G2A5-S9D1-F3H6"
    manager.used_keys[expired_key] = {
        "type": manager.KEY_TYPE_SCRAPING,
        "activated_at": (datetime.now() - timedelta(days=400)).isoformat(),
        "expires_at": (datetime.now() - timedelta(days=35)).isoformat()
    }
    manager._save_used_keys()
    
    # Reload manager to test expired key
    manager2 = ProductKeyManager()
    has_access = manager2.has_scraping_access()
    print_test("Expired Key Blocks Access", not has_access, 
               "Expired key should not grant access")


def test_key_types():
    """Test different key types and their permissions"""
    print_header("TEST 4: Key Type Permissions")
    
    # Clean up any existing test data
    test_file = '.product_keys.dat'
    if os.path.exists(test_file):
        os.remove(test_file)
    
    # Test 4.1: Scraping-only key
    manager = ProductKeyManager()
    manager.activate_key("SCRP-E1J8-K5L2-Z7X4-C9V6")
    
    has_scraping = manager.has_scraping_access()
    has_upload = manager.has_upload_access()
    print_test("Scraping Key - Scraping Access", has_scraping, 
               "Should have scraping access")
    print_test("Scraping Key - No Upload Access", not has_upload, 
               "Should NOT have upload access")
    
    # Clean up
    os.remove(test_file)
    
    # Test 4.2: Full access key
    manager2 = ProductKeyManager()
    manager2.activate_key("FULL-C1H6-K9M4-V2B7-N5J8")
    
    has_scraping = manager2.has_scraping_access()
    has_upload = manager2.has_upload_access()
    print_test("Full Access Key - Scraping Access", has_scraping, 
               "Should have scraping access")
    print_test("Full Access Key - Upload Access", has_upload, 
               "Should have upload access")


def test_all_keys_unique():
    """Test that all 100 keys are unique and valid"""
    print_header("TEST 5: All Keys Validation")
    
    manager = ProductKeyManager()
    
    total_keys = len(manager.valid_keys)
    scraping_keys = sum(1 for k, v in manager.valid_keys.items() if v == manager.KEY_TYPE_SCRAPING)
    full_keys = sum(1 for k, v in manager.valid_keys.items() if v == manager.KEY_TYPE_FULL)
    
    print_test("Total Keys Count", total_keys == 100, f"Found {total_keys} keys")
    print_test("Scraping Keys Count", scraping_keys == 50, f"Found {scraping_keys} scraping keys")
    print_test("Full Access Keys Count", full_keys == 50, f"Found {full_keys} full access keys")
    
    # Test uniqueness
    unique_keys = len(set(manager.valid_keys.keys()))
    print_test("All Keys Unique", unique_keys == total_keys, 
               f"{unique_keys} unique out of {total_keys} total")


def display_sample_keys():
    """Display sample keys for testing"""
    print_header("SAMPLE KEYS FOR MANUAL TESTING")
    
    print("\n📋 SCRAPING ONLY KEYS (Test these for scraping-only access):")
    print("   1. SCRP-A7K9-M2X4-P8Q1-W5E3")
    print("   2. SCRP-B3N6-L9Y2-R4T7-U1I8")
    print("   3. SCRP-C8H5-K1M3-V6B9-N2J4")
    
    print("\n📋 FULL ACCESS KEYS (Test these for complete access):")
    print("   1. FULL-A9M7-K3X5-P2Q8-W6E4")
    print("   2. FULL-B5N8-L2Y4-R6T9-U3I1")
    print("   3. FULL-C1H6-K9M4-V2B7-N5J8")
    
    print("\n📋 INVALID KEYS (Test these for rejection):")
    print("   1. INVALID-1234-5678-9012-3456")
    print("   2. SCRP-XXXX-YYYY-ZZZZ-AAAA")
    print("   3. FULL-0000-0000-0000-0000")


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  TCG CARD SCRAPER PRO - PRODUCT KEY TESTING SUITE")
    print("=" * 70)
    print(f"  Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    try:
        # Run all tests
        test_key_validation()
        test_key_activation()
        test_key_expiration()
        test_key_types()
        test_all_keys_unique()
        display_sample_keys()
        
        print_header("TEST SUMMARY")
        print("✓ All automated tests completed!")
        print("\nNext Steps:")
        print("1. Build the .exe using: python3 build_exe.py")
        print("2. Run the application and test with sample keys above")
        print("3. Verify key expiration by checking activation dates")
        print("4. Test that used keys cannot be reused")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test file
        test_file = '.product_keys.dat'
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\n🧹 Cleaned up test file: {test_file}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
