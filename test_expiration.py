"""
Product Key Expiration Testing Utility
This script helps you test the expiration mechanism without waiting 1 year
"""

import os
from datetime import datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ExpirationTester:
    """Utility to test product key expiration"""
    
    def __init__(self):
        """Initialize Supabase connection"""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SECRET_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials not found in .env file")
        
        self.supabase = create_client(self.supabase_url, self.supabase_key)
    
    def list_all_keys(self):
        """List all product keys in the database"""
        print("\n" + "="*80)
        print("ALL PRODUCT KEYS")
        print("="*80)


        
        try:
            response = self.supabase.table('product_keys').select('*').execute()
            
            if not response.data:
                print("No product keys found in database.")
                return
            
            for idx, key in enumerate(response.data, 1):
                print(f"\n{idx}. Product Key: {key['product_key']}")
                print(f"   Type: {key['key_type']}")
                print(f"   Activated: {key['is_activated']}")
                print(f"   Machine ID: {key.get('machine_id', 'N/A')}")
                
                if key['activated_at']:
                    activated_at = datetime.fromisoformat(key['activated_at'].replace('Z', '+00:00'))
                    print(f"   Activated At: {activated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                else:
                    print(f"   Activated At: Not activated")
                
                if key['expires_at']:
                    expires_at = datetime.fromisoformat(key['expires_at'].replace('Z', '+00:00'))
                    now = datetime.utcnow()
                    
                    print(f"   Expires At: {expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                    
                    if expires_at > now:
                        time_left = expires_at - now
                        days_left = time_left.days
                        hours_left = time_left.seconds // 3600
                        print(f"   Status: ✅ ACTIVE ({days_left} days, {hours_left} hours remaining)")
                    else:
                        time_expired = now - expires_at
                        days_expired = time_expired.days
                        hours_expired = time_expired.seconds // 3600
                        print(f"   Status: ❌ EXPIRED ({days_expired} days, {hours_expired} hours ago)")
                else:
                    print(f"   Expires At: Not set")
                    print(f"   Status: Not activated")
        
        except Exception as e:
            print(f"Error: {e}")
    
    def set_expiration_date(self, product_key, days_from_now=None, minutes_from_now=None, 
                           hours_from_now=None, expired_days_ago=None):
        """
        Set custom expiration date for testing
        
        Args:
            product_key: The product key to modify
            days_from_now: Set expiration X days from now (positive number)
            minutes_from_now: Set expiration X minutes from now (for quick testing)
            hours_from_now: Set expiration X hours from now
            expired_days_ago: Set expiration X days in the past (to test expired keys)
        """
        try:
            # Calculate new expiration time
            now = datetime.utcnow()
            
            if expired_days_ago is not None:
                new_expiration = now - timedelta(days=expired_days_ago)
                status = f"EXPIRED {expired_days_ago} days ago"
            elif minutes_from_now is not None:
                new_expiration = now + timedelta(minutes=minutes_from_now)
                status = f"expires in {minutes_from_now} minutes"
            elif hours_from_now is not None:
                new_expiration = now + timedelta(hours=hours_from_now)
                status = f"expires in {hours_from_now} hours"
            elif days_from_now is not None:
                new_expiration = now + timedelta(days=days_from_now)
                status = f"expires in {days_from_now} days"
            else:
                print("Error: Please specify one of: days_from_now, minutes_from_now, hours_from_now, or expired_days_ago")
                return
            
            # Update the expiration date
            response = self.supabase.table('product_keys')\
                .update({'expires_at': new_expiration.isoformat()})\
                .eq('product_key', product_key)\
                .execute()
            
            if response.data:
                print(f"\n✅ Successfully updated expiration for key: {product_key}")
                print(f"   New expiration: {new_expiration.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                print(f"   Status: {status}")
            else:
                print(f"\n❌ Failed to update expiration. Key might not exist: {product_key}")
        
        except Exception as e:
            print(f"Error: {e}")
    
    def test_expired_key_scenario(self, product_key):
        """
        Quick test: Set a key to expire 1 day ago and verify it's detected as expired
        """
        print(f"\n🧪 TESTING EXPIRED KEY SCENARIO")
        print(f"Product Key: {product_key}")
        print("-" * 80)
        
        # Set expiration to 1 day ago
        self.set_expiration_date(product_key, expired_days_ago=1)
        
        # Import the product key manager to test
        from product_keys_supabase import SupabaseProductKeyManager
        
        manager = SupabaseProductKeyManager()
        
        print("\n📋 Testing validation...")
        success, key_type, message = manager.validate_key(product_key)
        
        print(f"\nValidation Result:")
        print(f"  Success: {success}")
        print(f"  Key Type: {key_type}")
        print(f"  Message: {message}")
        
        if not success and "expired" in message.lower():
            print("\n✅ TEST PASSED: Expired key was correctly detected!")
        else:
            print("\n❌ TEST FAILED: Expired key was not detected properly!")
    
    def test_expiring_soon_scenario(self, product_key, minutes=2):
        """
        Quick test: Set a key to expire in X minutes to test real-time expiration
        """
        print(f"\n🧪 TESTING EXPIRING SOON SCENARIO")
        print(f"Product Key: {product_key}")
        print(f"Will expire in: {minutes} minutes")
        print("-" * 80)
        
        # Set expiration to X minutes from now
        self.set_expiration_date(product_key, minutes_from_now=minutes)
        
        # Import the product key manager to test
        from product_keys_supabase import SupabaseProductKeyManager
        
        manager = SupabaseProductKeyManager()
        
        print("\n📋 Testing validation NOW (should be valid)...")
        success, key_type, message = manager.validate_key(product_key)
        
        print(f"\nCurrent Validation Result:")
        print(f"  Success: {success}")
        print(f"  Key Type: {key_type}")
        print(f"  Message: {message}")
        
        if success:
            print(f"\n✅ Key is currently VALID")
            print(f"⏰ Wait {minutes} minutes and test again to see it expire")
            print(f"\nTo test after waiting, run:")
            print(f"  python test_expiration.py --validate {product_key}")
        else:
            print(f"\n❌ Key validation failed unexpectedly")

    
    def validate_key_status(self, product_key):
        """Just validate and show current key status"""
        from product_keys_supabase import SupabaseProductKeyManager
        
        print(f"\n📋 VALIDATING KEY: {product_key}")
        print("-" * 80)
        
        manager = SupabaseProductKeyManager()
        success, key_type, message = manager.validate_key(product_key)
        
        print(f"\nValidation Result:")
        print(f"  Success: {success}")
        print(f"  Key Type: {key_type}")
        print(f"  Message: {message}")
        
        if success:
            print("\n✅ Key is VALID and ACTIVE")
        else:
            print("\n❌ Key is INVALID or EXPIRED")
    
    def reset_to_one_year(self, product_key):
        """Reset a key back to standard 1 year expiration"""
        print(f"\n🔄 RESETTING KEY TO 1 YEAR EXPIRATION")
        print(f"Product Key: {product_key}")
        print("-" * 80)
        
        self.set_expiration_date(product_key, days_from_now=365)


def print_menu():
    """Print the testing menu"""
    print("\n" + "="*80)
    print("PRODUCT KEY EXPIRATION TESTING UTILITY")
    print("="*80)
    print("\nOptions:")
    print("  1. List all product keys")
    print("  2. Set key to expire in X minutes (quick test)")
    print("  3. Set key to expired (1 day ago)")
    print("  4. Set custom expiration")
    print("  5. Validate key status")
    print("  6. Reset key to 1 year expiration")
    print("  7. Run automated expired key test")
    print("  0. Exit")
    print("-" * 80)




def main():
    """Main testing interface"""
    tester = ExpirationTester()
    
    while True:
        print_menu()
        choice = input("\nEnter your choice (0-7): ").strip()
        
        if choice == "0":
            print("\n👋 Goodbye!")
            break
        
        elif choice == "1":
            tester.list_all_keys()
        
        elif choice == "2":
            product_key = input("\nEnter product key: ").strip()
            minutes = input("Enter minutes until expiration (default 2): ").strip()
            minutes = int(minutes) if minutes else 2
            tester.test_expiring_soon_scenario(product_key, minutes)
        
        elif choice == "3":
            product_key = input("\nEnter product key: ").strip()
            tester.set_expiration_date(product_key, expired_days_ago=1)
        
        elif choice == "4":
            product_key = input("\nEnter product key: ").strip()
            print("\nChoose expiration type:")
            print("  1. Days from now")
            print("  2. Hours from now")
            print("  3. Minutes from now")
            print("  4. Days ago (expired)")
            
            exp_type = input("Enter type (1-4): ").strip()
            
            if exp_type == "1":
                days = int(input("Enter days from now: ").strip())
                tester.set_expiration_date(product_key, days_from_now=days)
            elif exp_type == "2":
                hours = int(input("Enter hours from now: ").strip())
                tester.set_expiration_date(product_key, hours_from_now=hours)
            elif exp_type == "3":
                minutes = int(input("Enter minutes from now: ").strip())
                tester.set_expiration_date(product_key, minutes_from_now=minutes)
            elif exp_type == "4":
                days = int(input("Enter days ago: ").strip())
                tester.set_expiration_date(product_key, expired_days_ago=days)
        
        elif choice == "5":
            product_key = input("\nEnter product key: ").strip()
            tester.validate_key_status(product_key)
        
        elif choice == "6":
            product_key = input("\nEnter product key: ").strip()
            tester.reset_to_one_year(product_key)
        
        elif choice == "7":
            product_key = input("\nEnter product key: ").strip()
            tester.test_expired_key_scenario(product_key)
        
        else:
            print("\n❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()

