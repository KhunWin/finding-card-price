"""
Server-Based Product Key Manager using Supabase
This module handles product key validation with cross-machine protection
"""

import os
import hashlib
import platform
import uuid
from datetime import datetime, timedelta
from typing import Tuple, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SupabaseProductKeyManager:
    """Manages product keys with server-based validation using Supabase"""
    
    KEY_TYPE_SCRAPING = "scraping_only"
    KEY_TYPE_FULL = "full_access"
    
    def __init__(self):
        """Initialize Supabase connection"""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SECRET_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials not found in .env file")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.machine_id = self._generate_machine_id()
        self.machine_name = self._get_machine_name()
        
        # Cache for activated keys (to reduce API calls)
        self._cache = {}
        self._cache_loaded = False
    
    def _generate_machine_id(self) -> str:
        """Generate a unique machine identifier"""
        # Combine multiple hardware identifiers for uniqueness
        identifiers = []
        
        # Get MAC address
        try:
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                           for elements in range(0, 2*6, 2)][::-1])
            identifiers.append(mac)
        except:
            pass
        
        # Get hostname
        try:
            identifiers.append(platform.node())
        except:
            pass
        
        # Get platform info
        try:
            identifiers.append(platform.platform())
        except:
            pass
        
        # Create hash of combined identifiers
        combined = '|'.join(identifiers)
        machine_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        return machine_hash
    
    def _get_machine_name(self) -> str:
        """Get a human-readable machine name"""
        try:
            hostname = platform.node()
            system = platform.system()
            return f"{hostname} ({system})"
        except:
            return "Unknown Machine"
    
    def _load_cache(self):
        """Load activated keys for this machine from Supabase"""
        if self._cache_loaded:
            return
        
        try:
            # Query keys activated on this machine
            response = self.supabase.table('product_keys')\
                .select('*')\
                .eq('machine_id', self.machine_id)\
                .eq('is_activated', True)\
                .execute()
            
            if response.data:
                for key_data in response.data:
                    self._cache[key_data['product_key']] = {
                        'type': key_data['key_type'],
                        'activated_at': key_data['activated_at'],
                        'expires_at': key_data['expires_at']
                    }
            
            self._cache_loaded = True
        except Exception as e:
            print(f"Warning: Could not load cache from Supabase: {e}")
            self._cache_loaded = True  # Mark as loaded to avoid repeated failures
    
    def validate_key(self, product_key: str) -> Tuple[bool, str]:
        """
        Validate product key format and existence
        
        Returns:
            Tuple[bool, str]: (is_valid, message)
        """
        # Normalize key
        product_key = product_key.strip().upper()
        
        # Check format
        if not product_key:
            return False, "Product key cannot be empty."
        
        # Check if it matches expected format
        parts = product_key.split('-')
        if len(parts) != 5:
            return False, "Invalid product key format. Expected format: XXXX-XXXX-XXXX-XXXX-XXXX"
        
        # Check prefix
        if not (product_key.startswith('SCRP-') or product_key.startswith('FULL-')):
            return False, "Invalid product key. Key must start with SCRP- or FULL-"
        
        try:
            # Check if key exists in database
            response = self.supabase.table('product_keys')\
                .select('product_key')\
                .eq('product_key', product_key)\
                .execute()
            
            if not response.data or len(response.data) == 0:
                return False, "Invalid product key. Please check and try again."
            
            return True, "Product key is valid!"
        
        except Exception as e:
            return False, f"Error validating key: {str(e)}"
    
    def activate_key(self, product_key: str) -> Tuple[bool, str, str]:
        """
        Activate a product key for this machine
        
        Returns:
            Tuple[bool, str, str]: (success, key_type, message)
        """
        # Normalize key
        product_key = product_key.strip().upper()
        
        # Validate format first
        is_valid, message = self.validate_key(product_key)
        if not is_valid:
            return False, "", message
        
        try:
            # Check if key exists and get its current status
            response = self.supabase.table('product_keys')\
                .select('*')\
                .eq('product_key', product_key)\
                .execute()
            
            if not response.data or len(response.data) == 0:
                return False, "", "Product key not found in database."
            
            key_data = response.data[0]
            
            # Check if key is already activated
            if key_data['is_activated']:
                # Check if it's activated on THIS machine
                if key_data['machine_id'] == self.machine_id:
                    # Already activated on this machine
                    self._cache[product_key] = {
                        'type': key_data['key_type'],
                        'activated_at': key_data['activated_at'],
                        'expires_at': key_data['expires_at']
                    }
                    return False, key_data['key_type'], "This product key has already been activated on this system."
                else:
                    # Activated on a different machine
                    return False, "", f"This product key has already been activated on another machine ({key_data['machine_name']})."
            
            # Key is not activated, activate it now
            activation_time = datetime.utcnow()
            expiration_time = activation_time + timedelta(days=365)  # 1 year expiration
            
            update_data = {
                'is_activated': True,
                'machine_id': self.machine_id,
                'machine_name': self.machine_name,
                'activated_at': activation_time.isoformat(),
                'expires_at': expiration_time.isoformat()
            }
            
            # Update the key in database
            update_response = self.supabase.table('product_keys')\
                .update(update_data)\
                .eq('product_key', product_key)\
                .execute()
            
            if not update_response.data:
                return False, "", "Failed to activate product key. Please try again."
            
            # Update cache
            self._cache[product_key] = {
                'type': key_data['key_type'],
                'activated_at': activation_time.isoformat(),
                'expires_at': expiration_time.isoformat()
            }
            
            return True, key_data['key_type'], f"Product key activated successfully! Type: {key_data['key_type']}\nExpires: {expiration_time.strftime('%Y-%m-%d')}"
        
        except Exception as e:
            return False, "", f"Error activating key: {str(e)}"
    
    def has_scraping_access(self) -> bool:
        """Check if user has scraping access (either scraping_only or full_access key)"""
        self._load_cache()
        
        for key, data in self._cache.items():
            # Check if key is not expired
            try:
                expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
                if expires_at > datetime.utcnow().replace(tzinfo=expires_at.tzinfo):
                    if data['type'] in [self.KEY_TYPE_SCRAPING, self.KEY_TYPE_FULL]:
                        return True
            except:
                pass
        
        return False
    
    def has_upload_access(self) -> bool:
        """Check if user has upload access (full_access key only)"""
        self._load_cache()
        
        for key, data in self._cache.items():
            # Check if key is not expired
            try:
                expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
                if expires_at > datetime.utcnow().replace(tzinfo=expires_at.tzinfo):
                    if data['type'] == self.KEY_TYPE_FULL:
                        return True
            except:
                pass
        
        return False
    
    def get_activated_keys(self) -> dict:
        """Get all activated keys for this machine"""
        self._load_cache()
        return self._cache.copy()
    
    def check_connection(self) -> Tuple[bool, str]:
        """Check if connection to Supabase is working"""
        try:
            # Try to query the table
            response = self.supabase.table('product_keys').select('count', count='exact').limit(1).execute()
            return True, "Connected to Supabase successfully!"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"


# For backward compatibility, create an alias
ProductKeyManager = SupabaseProductKeyManager
