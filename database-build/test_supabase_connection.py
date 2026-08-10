"""
Test Supabase Connection and Product Key System
This script verifies that the Supabase setup is working correctly
"""

import os
from product_keys_supabase import SupabaseProductKeyManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test basic connection to Supabase"""
    print("=" * 70)
    print("  TESTING SUPABASE CONNECTION")
    print("=" * 70)
    print()
    
    try:
        manager = SupabaseProductKeyManager()
        print(f"✓ ProductKeyManager initialized")
        print(f"  • Supabase URL: {manager.supabase_url}")
        print(f"  • Machine ID: {manager.machine_id[:16]}...")
        print(f"  • Machine Name: {manager.machine_name}")
        print()
        
        # Test connection
        success, message = manager.check_connection()
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
            return False
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return False


def test_key_validation():
    """Test key validation"""
    print("=" * 70)
    print("  TESTING KEY VALIDATION")
    print("=" * 70)
    print()
    
    manager = SupabaseProductKeyManager()
    
    # Test valid key format
    test_cases = [
        ("SCRP-A7K9-M2X4-P8Q1-W5E3", True, "Valid scraping key"),
        ("FULL-X9Z2-C5V8-N3M6-Q1W4", True, "Valid full access key"),
        ("INVALID-KEY", False, "Invalid format"),
        ("", False, "Empty key"),
        ("SCRP-XXXX-XXXX-XXXX-XXXX", False, "Non-existent key"),
    ]
    
    for key, should_be_valid, description in test_cases:
        is_valid, message = manager.validate_key(key)
        status = "✅" if is_valid == should_be_valid else "❌"
        print(f"{status} {description}")
        print(f"   Key: {key if key else '(empty)'}")
        print(f"   Valid: {is_valid}")
        print(f"   Message: {message}")
        print()
    
    return True


def test_key_activation():
    """Test key activation (read-only, doesn't actually activate)"""
    print("=" * 70)
    print("  TESTING KEY ACTIVATION (INFO ONLY)")
    print("=" * 70)
    print()
    
    manager = SupabaseProductKeyManager()
    
    print("ℹ️  This test checks activation logic without actually activating keys")
    print()
    
    # Check current access
    has_scraping = manager.has_scraping_access()
    has_upload = manager.has_upload_access()
    
    print(f"Current Access Status:")
    print(f"  • Scraping Access: {'✅ Yes' if has_scraping else '❌ No'}")
    print(f"  • Upload Access: {'✅ Yes' if has_upload else '❌ No'}")
    print()
    
    # Show activated keys
    activated_keys = manager.get_activated_keys()
    if activated_keys:
        print(f"Activated Keys on This Machine:")
        for key, data in activated_keys.items():
            print(f"  • {key}")
            print(f"    Type: {data['type']}")
            print(f"    Activated: {data['activated_at']}")
            print(f"    Expires: {data['expires_at']}")
            print()
    else:
        print("No keys activated on this machine yet.")
        print()
    
    return True


def test_database_stats():
    """Show database statistics"""
    print("=" * 70)
    print("  DATABASE STATISTICS")
    print("=" * 70)
    print()
    
    try:
        manager = SupabaseProductKeyManager()
        
        # Get total keys
        response = manager.supabase.table('product_keys').select('count', count='exact').execute()
        total = response.count if hasattr(response, 'count') else 0
        
        # Get activated keys
        activated_response = manager.supabase.table('product_keys').select('count', count='exact').eq('is_activated', True).execute()
        activated = activated_response.count if hasattr(activated_response, 'count') else 0
        
        # Get by type
        scraping_response = manager.supabase.table('product_keys').select('count', count='exact').eq('key_type', 'scraping_only').execute()
        scraping = scraping_response.count if hasattr(scraping_response, 'count') else 0
        
        full_response = manager.supabase.table('product_keys').select('count', count='exact').eq('key_type', 'full_access').execute()
        full = full_response.count if hasattr(full_response, 'count') else 0
        
        print(f"📊 Total Keys: {total}")
        print(f"   • Scraping Only: {scraping}")
        print(f"   • Full Access: {full}")
        print()
        print(f"🔑 Activation Status:")
        print(f"   • Activated: {activated}")
        print(f"   • Available: {total - activated}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Could not retrieve statistics: {e}")
        return False


def main():
    """Run all tests"""
    print("\n")
    print("🧪 SUPABASE PRODUCT KEY SYSTEM - TEST SUITE")
    print("\n")
    
    tests = [
        ("Connection Test", test_connection),
        ("Key Validation Test", test_key_validation),
        ("Key Activation Test", test_key_activation),
        ("Database Statistics", test_database_stats),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    print()
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    print()
    
    if passed == total:
        print("🎉 All tests passed! System is ready to use.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    print()


if __name__ == "__main__":
    main()
