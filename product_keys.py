#!/usr/bin/env python3
"""
Product Key Management System
Handles validation and storage of product keys for TCG Card Scraper Pro
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta


class ProductKeyManager:
    """Manages product key validation and usage tracking"""
    
    # Key types
    KEY_TYPE_SCRAPING = "scraping_only"  # Key 1: Only for scraping
    KEY_TYPE_FULL = "full_access"        # Key 2: For both scraping and upload
    
    def __init__(self):
        """Initialize the product key manager"""
        # Get the directory where the executable/script is located
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            self.app_dir = os.path.dirname(sys.executable)
        else:
            # Running as script
            self.app_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.keys_file = os.path.join(self.app_dir, '.product_keys.dat')
        self.valid_keys = self._load_valid_keys()
        self.used_keys = self._load_used_keys()
    
    def _load_valid_keys(self):
        """Load the list of valid product keys (embedded in code)"""
        # These are the valid keys - 50 for scraping only, 50 for full access
        return {
            # SCRAPING ONLY KEYS (Key Type 1) - 50 keys
            "SCRP-A7K9-M2X4-P8Q1-W5E3": self.KEY_TYPE_SCRAPING,
            "SCRP-B3N6-L9Y2-R4T7-U1I8": self.KEY_TYPE_SCRAPING,
            "SCRP-C8H5-K1M3-V6B9-N2J4": self.KEY_TYPE_SCRAPING,
            "SCRP-D4F7-G2A5-S9D1-F3H6": self.KEY_TYPE_SCRAPING,
            "SCRP-E1J8-K5L2-Z7X4-C9V6": self.KEY_TYPE_SCRAPING,
            "SCRP-F6M3-N9B1-Q4W7-E2R5": self.KEY_TYPE_SCRAPING,
            "SCRP-G2P8-H4K6-T1Y3-U9I7": self.KEY_TYPE_SCRAPING,
            "SCRP-H9L4-J7M2-A5S8-D1F3": self.KEY_TYPE_SCRAPING,
            "SCRP-I5K1-L8N6-G3H9-J2K4": self.KEY_TYPE_SCRAPING,
            "SCRP-J3X7-Z2C5-V8B1-N4M6": self.KEY_TYPE_SCRAPING,
            "SCRP-K8Q2-W5E9-R1T4-Y7U3": self.KEY_TYPE_SCRAPING,
            "SCRP-L4I6-O9P3-A2S5-D8F1": self.KEY_TYPE_SCRAPING,
            "SCRP-M1G7-H3J9-K6L2-Z5X8": self.KEY_TYPE_SCRAPING,
            "SCRP-N9C4-V6B2-N8M1-Q3W5": self.KEY_TYPE_SCRAPING,
            "SCRP-O5E7-R2T9-Y4U1-I6O8": self.KEY_TYPE_SCRAPING,
            "SCRP-P2A3-S6D8-F1G4-H7J9": self.KEY_TYPE_SCRAPING,
            "SCRP-Q8K5-L1Z3-X7C9-V2B4": self.KEY_TYPE_SCRAPING,
            "SCRP-R4N6-M2Q8-W1E3-R5T7": self.KEY_TYPE_SCRAPING,
            "SCRP-S1Y9-U4I6-O8P2-A5S7": self.KEY_TYPE_SCRAPING,
            "SCRP-T7D3-F5G1-H9J2-K4L6": self.KEY_TYPE_SCRAPING,
            "SCRP-U3Z8-X6C2-V4B7-N1M9": self.KEY_TYPE_SCRAPING,
            "SCRP-V9Q5-W2E8-R4T1-Y3U6": self.KEY_TYPE_SCRAPING,
            "SCRP-W6I2-O4P7-A9S1-D3F5": self.KEY_TYPE_SCRAPING,
            "SCRP-X2G8-H1J4-K7L9-Z3X5": self.KEY_TYPE_SCRAPING,
            "SCRP-Y8C4-V7B1-N3M6-Q9W2": self.KEY_TYPE_SCRAPING,
            "SCRP-Z5E1-R3T6-Y8U2-I4O7": self.KEY_TYPE_SCRAPING,
            "SCRP-A1S9-D4F2-G6H8-J3K5": self.KEY_TYPE_SCRAPING,
            "SCRP-B7L3-Z5X8-C1V4-B6N9": self.KEY_TYPE_SCRAPING,
            "SCRP-C4M2-Q6W9-E1R3-T5Y7": self.KEY_TYPE_SCRAPING,
            "SCRP-D9U8-I1O3-P5A7-S2D4": self.KEY_TYPE_SCRAPING,
            "SCRP-E6F1-G4H7-J9K2-L5Z8": self.KEY_TYPE_SCRAPING,
            "SCRP-F2X3-C6V9-B1N4-M7Q8": self.KEY_TYPE_SCRAPING,
            "SCRP-G8W5-E2R7-T9Y1-U4I6": self.KEY_TYPE_SCRAPING,
            "SCRP-H4O3-P6A9-S1D2-F5G7": self.KEY_TYPE_SCRAPING,
            "SCRP-I1H8-J3K5-L7Z9-X2C4": self.KEY_TYPE_SCRAPING,
            "SCRP-J7V6-B9N1-M3Q5-W8E2": self.KEY_TYPE_SCRAPING,
            "SCRP-K3R4-T7Y9-U1I2-O6P8": self.KEY_TYPE_SCRAPING,
            "SCRP-L9A5-S2D4-F6G8-H1J3": self.KEY_TYPE_SCRAPING,
            "SCRP-M6K7-L9Z1-X3C5-V8B2": self.KEY_TYPE_SCRAPING,
            "SCRP-N2N4-M6Q8-W1E3-R7T9": self.KEY_TYPE_SCRAPING,
            "SCRP-O8Y5-U2I4-O6P9-A1S3": self.KEY_TYPE_SCRAPING,
            "SCRP-P5D7-F1G3-H5J8-K9L2": self.KEY_TYPE_SCRAPING,
            "SCRP-Q1Z4-X6C8-V2B5-N9M3": self.KEY_TYPE_SCRAPING,
            "SCRP-R7Q6-W9E1-R3T5-Y8U2": self.KEY_TYPE_SCRAPING,
            "SCRP-S4I1-O3P6-A8S2-D5F7": self.KEY_TYPE_SCRAPING,
            "SCRP-T9G9-H2J4-K6L8-Z1X3": self.KEY_TYPE_SCRAPING,
            "SCRP-U6C5-V8B2-N4M7-Q1W9": self.KEY_TYPE_SCRAPING,
            "SCRP-V2E3-R5T7-Y9U1-I4O6": self.KEY_TYPE_SCRAPING,
            "SCRP-W8A8-S1D3-F5G7-H9J2": self.KEY_TYPE_SCRAPING,
            "SCRP-X5K4-L6Z8-X1C3-V5B7": self.KEY_TYPE_SCRAPING,
            
            # FULL ACCESS KEYS (Key Type 2) - 50 keys
            "FULL-A9M7-K3X5-P2Q8-W6E4": self.KEY_TYPE_FULL,
            "FULL-B5N8-L2Y4-R6T9-U3I1": self.KEY_TYPE_FULL,
            "FULL-C1H6-K9M4-V2B7-N5J8": self.KEY_TYPE_FULL,
            "FULL-D7F3-G5A8-S2D6-F9H1": self.KEY_TYPE_FULL,
            "FULL-E4J1-K8L5-Z3X7-C2V9": self.KEY_TYPE_FULL,
            "FULL-F9M6-N2B4-Q8W1-E5R7": self.KEY_TYPE_FULL,
            "FULL-G5P1-H7K9-T3Y6-U2I8": self.KEY_TYPE_FULL,
            "FULL-H2L8-J1M5-A9S3-D6F4": self.KEY_TYPE_FULL,
            "FULL-I8K4-L1N9-G6H2-J5K7": self.KEY_TYPE_FULL,
            "FULL-J6X3-Z5C8-V1B4-N9M2": self.KEY_TYPE_FULL,
            "FULL-K1Q5-W8E2-R6T9-Y3U4": self.KEY_TYPE_FULL,
            "FULL-L7I9-O2P6-A4S8-D1F3": self.KEY_TYPE_FULL,
            "FULL-M4G2-H6J8-K1L5-Z9X3": self.KEY_TYPE_FULL,
            "FULL-N2C7-V9B3-N1M5-Q8W4": self.KEY_TYPE_FULL,
            "FULL-O8E4-R5T1-Y9U6-I2O7": self.KEY_TYPE_FULL,
            "FULL-P5A6-S1D9-F4G7-H2J8": self.KEY_TYPE_FULL,
            "FULL-Q1K8-L4Z6-X2C5-V9B3": self.KEY_TYPE_FULL,
            "FULL-R7N3-M5Q1-W9E4-R2T6": self.KEY_TYPE_FULL,
            "FULL-S4Y2-U7I9-O1P5-A8S3": self.KEY_TYPE_FULL,
            "FULL-T9D6-F8G2-H4J7-K1L5": self.KEY_TYPE_FULL,
            "FULL-U6Z1-X9C4-V7B2-N5M8": self.KEY_TYPE_FULL,
            "FULL-V2Q8-W5E1-R7T4-Y9U3": self.KEY_TYPE_FULL,
            "FULL-W9I5-O7P2-A4S6-D8F1": self.KEY_TYPE_FULL,
            "FULL-X5G3-H8J1-K4L6-Z2X9": self.KEY_TYPE_FULL,
            "FULL-Y1C7-V4B8-N2M5-Q6W9": self.KEY_TYPE_FULL,
            "FULL-Z8E9-R6T2-Y4U7-I1O5": self.KEY_TYPE_FULL,
            "FULL-A4S2-D7F9-G1H5-J8K3": self.KEY_TYPE_FULL,
            "FULL-B9L6-Z8X1-C4V7-B2N5": self.KEY_TYPE_FULL,
            "FULL-C7M9-Q3W6-E8R1-T4Y5": self.KEY_TYPE_FULL,
            "FULL-D2U1-I6O8-P3A5-S9D7": self.KEY_TYPE_FULL,
            "FULL-E9F4-G7H2-J5K8-L1Z6": self.KEY_TYPE_FULL,
            "FULL-F5X6-C9V2-B4N7-M1Q8": self.KEY_TYPE_FULL,
            "FULL-G1W8-E5R3-T7Y9-U2I4": self.KEY_TYPE_FULL,
            "FULL-H7O6-P9A1-S4D7-F2G5": self.KEY_TYPE_FULL,
            "FULL-I4H1-J8K3-L6Z9-X5C2": self.KEY_TYPE_FULL,
            "FULL-J9V8-B2N5-M7Q1-W4E6": self.KEY_TYPE_FULL,
            "FULL-K6R7-T1Y4-U8I3-O9P2": self.KEY_TYPE_FULL,
            "FULL-L2A8-S5D1-F9G3-H6J4": self.KEY_TYPE_FULL,
            "FULL-M8K9-L2Z4-X6C8-V1B5": self.KEY_TYPE_FULL,
            "FULL-N5N7-M9Q2-W4E6-R8T1": self.KEY_TYPE_FULL,
            "FULL-O1Y3-U5I7-O9P2-A4S6": self.KEY_TYPE_FULL,
            "FULL-P7D8-F2G5-H9J1-K3L6": self.KEY_TYPE_FULL,
            "FULL-Q4Z5-X1C7-V9B3-N2M4": self.KEY_TYPE_FULL,
            "FULL-R9Q1-W3E6-R8T2-Y5U7": self.KEY_TYPE_FULL,
            "FULL-S6I4-O8P1-A3S5-D7F9": self.KEY_TYPE_FULL,
            "FULL-T2G2-H5J7-K9L1-Z4X6": self.KEY_TYPE_FULL,
            "FULL-U8C8-V1B4-N6M9-Q2W5": self.KEY_TYPE_FULL,
            "FULL-V5E7-R9T3-Y1U4-I6O8": self.KEY_TYPE_FULL,
            "FULL-W1A1-S4D6-F8G2-H5J9": self.KEY_TYPE_FULL,
            "FULL-X7K3-L5Z9-X2C4-V6B8": self.KEY_TYPE_FULL,
        }
    
    def _load_used_keys(self):
        """Load previously used keys from file"""
        if os.path.exists(self.keys_file):
            try:
                with open(self.keys_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_used_keys(self):
        """Save used keys to file"""
        try:
            with open(self.keys_file, 'w') as f:
                json.dump(self.used_keys, f)
        except Exception as e:
            print(f"Warning: Could not save key usage data: {e}")
    
    def validate_key(self, key, required_type=None):
        """
        Validate a product key
        
        Args:
            key: The product key to validate
            required_type: The required key type (KEY_TYPE_SCRAPING or KEY_TYPE_FULL)
                          If None, any valid key is accepted
        
        Returns:
            tuple: (is_valid, key_type, message)
        """
        # Normalize key (remove spaces, convert to uppercase)
        key = key.strip().upper().replace(" ", "")
        
        # Check if key exists in valid keys
        if key not in self.valid_keys:
            return (False, None, "Invalid product key. Please check and try again.")
        
        # Check if key has already been used
        if key in self.used_keys:
            return (False, None, "This product key has already been used.")
        
        # Get key type
        key_type = self.valid_keys[key]
        
        # Check if key type matches requirement
        if required_type and key_type != required_type:
            if required_type == self.KEY_TYPE_FULL:
                return (False, key_type, "This key only allows scraping. Please use a Full Access key for upload functionality.")
            else:
                return (False, key_type, "Invalid key type for this operation.")
        
        return (True, key_type, "Product key is valid!")
    
    def activate_key(self, key):
        """
        Activate a product key (mark it as used)
        
        Args:
            key: The product key to activate
        
        Returns:
            tuple: (success, key_type, message)
        """
        is_valid, key_type, message = self.validate_key(key)
        
        if is_valid:
            # Normalize key
            key = key.strip().upper().replace(" ", "")
            
            # Get current timestamp and calculate expiration (1 year from now)
            activation_time = datetime.now()
            expiration_time = activation_time + timedelta(days=365)
            
            # Mark as used with activation and expiration timestamps
            self.used_keys[key] = {
                "type": key_type,
                "activated_at": activation_time.isoformat(),
                "expires_at": expiration_time.isoformat()
            }
            self._save_used_keys()
            
            return (True, key_type, f"Product key activated successfully! Type: {key_type}\nExpires: {expiration_time.strftime('%Y-%m-%d')}")
        
        return (False, None, message)
    
    def _is_key_expired(self, key_data):
        """Check if a key has expired"""
        expires_at = key_data.get("expires_at")
        if not expires_at:
            # Old keys without expiration - consider them expired
            return True
        
        try:
            expiration_date = datetime.fromisoformat(expires_at)
            return datetime.now() > expiration_date
        except:
            # Invalid date format - consider expired
            return True
    
    def has_scraping_access(self):
        """Check if user has activated any key that allows scraping and is not expired"""
        for key, data in self.used_keys.items():
            # Check if key is expired
            if self._is_key_expired(data):
                continue
            
            key_type = data.get("type")
            if key_type in [self.KEY_TYPE_SCRAPING, self.KEY_TYPE_FULL]:
                return True
        return False
    
    def has_upload_access(self):
        """Check if user has activated a full access key and is not expired"""
        for key, data in self.used_keys.items():
            # Check if key is expired
            if self._is_key_expired(data):
                continue
            
            if data.get("type") == self.KEY_TYPE_FULL:
                return True
        return False
    
    def get_activated_key_type(self):
        """Get the type of activated key (if any)"""
        for key, data in self.used_keys.items():
            return data.get("type")
        return None


# Import sys for frozen executable detection
import sys
