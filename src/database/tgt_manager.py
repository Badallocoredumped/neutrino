"""
TGT Manager for EPİAŞ Authentication
Handles TGT lifecycle - caching, validation, and renewal
"""

import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests

load_dotenv()

class TGTManager:
    """Manages TGT lifecycle - caching, validation, and renewal"""
    
    def __init__(self, cache_file="./src/database/cache/tgt_cache.json"):
        self.cache_file = cache_file
        self.tgt = None
        self.expiry_time = None
        
        # EPİAŞ authentication config
        self.cas_url = os.getenv("CAS_URL")
        self.username = os.getenv("EPIAS_USERNAME")
        self.password = os.getenv("EPIAS_PASSWORD")
        
        # Headers for TGT requests
        self.headers_tgt = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/plain"
        }
        
        # Ensure cache directory exists
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
        # Load cached TGT on initialization
        self.load_cached_tgt()
    
    def save_tgt_to_cache(self, tgt):
        """Save TGT and expiry time to cache file"""
        try:
            # Set expiry time: 2 hours minus 5 minutes buffer
            expiry_time = datetime.now() + timedelta(hours=1, minutes=55)
            
            cache_data = {
                "tgt": tgt,
                "expiry_time": expiry_time.isoformat(),
                "created_at": datetime.now().isoformat()
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            self.tgt = tgt
            self.expiry_time = expiry_time
            
            print(f"✅ TGT saved to cache, expires at: {expiry_time}")
            
        except Exception as e:
            print(f"❌ Error saving TGT to cache: {e}")
    
    def load_cached_tgt(self):
        """Load TGT from cache if it exists and is valid"""
        try:
            if not os.path.exists(self.cache_file):
                print("📝 No TGT cache file found")
                return False
            
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            tgt = cache_data.get('tgt')
            expiry_str = cache_data.get('expiry_time')
            
            if not tgt or not expiry_str:
                print("⚠️ Invalid cache data")
                return False
            
            expiry_time = datetime.fromisoformat(expiry_str)
            
            # Check if TGT is still valid
            if datetime.now() < expiry_time:
                self.tgt = tgt
                self.expiry_time = expiry_time
                print(f"✅ Loaded valid TGT from cache, expires at: {expiry_time}")
                return True
            else:
                print(f"⏰ Cached TGT expired at: {expiry_time}")
                return False
                
        except Exception as e:
            print(f"❌ Error loading TGT from cache: {e}")
            return False
    
    def is_tgt_valid(self):
        """Check if current TGT is still valid"""
        if not self.tgt or not self.expiry_time:
            return False
        return datetime.now() < self.expiry_time
    
    def get_fresh_tgt(self):
        """Get a fresh TGT from EPİAŞ"""
        try:
            print("🔄 Getting fresh TGT from EPİAŞ...")
            
            if not self.username or not self.password:
                print("❌ EPİAŞ credentials not found in environment variables")
                return None
            
            data = {
                "username": self.username,
                "password": self.password
            }
            
            response = requests.post(self.cas_url, headers=self.headers_tgt, data=data)
            print(f"TGT request status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                tgt = response.text.strip()
                self.save_tgt_to_cache(tgt)
                return tgt
            else:
                print(f"❌ TGT request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting fresh TGT: {e}")
            return None
    
    def get_valid_tgt(self):
        """Get a valid TGT - use cached if valid, otherwise get fresh"""
        if self.is_tgt_valid():
            print(f"✅ Using cached TGT (expires: {self.expiry_time})")
            return self.tgt
        else:
            print("🔄 TGT invalid or expired, getting fresh one...")
            return self.get_fresh_tgt()
    
    def clear_cache(self):
        """Clear TGT cache (force fresh TGT on next request)"""
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
            self.tgt = None
            self.expiry_time = None
            print("🗑️ TGT cache cleared")
        except Exception as e:
            print(f"❌ Error clearing cache: {e}")
    
    def get_tgt_status(self):
        """Get current TGT status information"""
        if self.is_tgt_valid():
            time_remaining = self.expiry_time - datetime.now()
            return {
                "valid": True,
                "expires_at": self.expiry_time.isoformat(),
                "time_remaining": str(time_remaining),
                "tgt_preview": f"{self.tgt[:20]}..." if self.tgt else None
            }
        else:
            return {
                "valid": False,
                "expires_at": None,
                "time_remaining": None,
                "tgt_preview": None
            }


# Test the TGT Manager
if __name__ == "__main__":
    print("🧪 Testing TGT Manager...")
    
    tgt_manager = TGTManager()
    
    # Get TGT status
    status = tgt_manager.get_tgt_status()
    print(f"📊 TGT Status: {status}")
    
    # Try to get a valid TGT
    tgt = tgt_manager.get_valid_tgt()
    if tgt:
        print(f"✅ Got valid TGT: {tgt[:20]}...")
        
        # Show updated status
        status = tgt_manager.get_tgt_status()
        print(f"📊 Updated TGT Status: {status}")
    else:
        print("❌ Failed to get valid TGT")