import threading
import time
from typing import Dict, Optional
from datetime import datetime

class AccountDataCache:
    def __init__(self):
        self.cache: Dict[str, Dict] = {}  # api_key -> cached_data
        self.lock = threading.Lock()
    
    def get_cache_key(self, api_key: str) -> str:
        """Generate a cache key from API key (use first 8 chars for privacy)"""
        return api_key[:8] if api_key else ""
    
    def is_cached(self, api_key: str) -> bool:
        """Check if data is cached for this API key"""
        cache_key = self.get_cache_key(api_key)
        with self.lock:
            return cache_key in self.cache and self.cache[cache_key].get('valid', False)
    
    def get_cached_data(self, api_key: str) -> Optional[Dict]:
        """Get cached data for API key"""
        cache_key = self.get_cache_key(api_key)
        with self.lock:
            if cache_key in self.cache and self.cache[cache_key].get('valid', False):
                return self.cache[cache_key]['data']
        return None
    
    def set_cached_data(self, api_key: str, data: Dict):
        """Cache data for API key"""
        cache_key = self.get_cache_key(api_key)
        with self.lock:
            self.cache[cache_key] = {
                'data': data,
                'valid': True,
                'cached_at': datetime.now(),
                'account_name': data.get('account_info', {}).get('name', 'Unknown')
            }
    
    def invalidate_cache(self, api_key: str):
        """Invalidate cached data for API key"""
        cache_key = self.get_cache_key(api_key)
        with self.lock:
            if cache_key in self.cache:
                self.cache[cache_key]['valid'] = False
    
    def get_cache_info(self, api_key: str) -> Optional[Dict]:
        """Get cache metadata"""
        cache_key = self.get_cache_key(api_key)
        with self.lock:
            if cache_key in self.cache:
                cache_entry = self.cache[cache_key]
                return {
                    'valid': cache_entry.get('valid', False),
                    'cached_at': cache_entry.get('cached_at'),
                    'account_name': cache_entry.get('account_name', 'Unknown'),
                    'data_keys': list(cache_entry.get('data', {}).keys()) if cache_entry.get('data') else []
                }
        return None
    
    def cleanup_old_cache(self, max_age_hours: int = 24):
        """Remove cache entries older than max_age_hours"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        with self.lock:
            expired_keys = []
            for cache_key, cache_entry in self.cache.items():
                cached_at = cache_entry.get('cached_at')
                if cached_at and cached_at.timestamp() < cutoff_time:
                    expired_keys.append(cache_key)
            
            for key in expired_keys:
                del self.cache[key]
                
        return len(expired_keys)

# Global cache instance
account_cache = AccountDataCache()