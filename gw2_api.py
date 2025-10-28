import requests
import time
from typing import Dict, List, Optional

class GW2API:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.guildwars2.com/v2"
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.rate_limit_delay = 0.2  # 200ms between requests to respect rate limits
        
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a request to the GW2 API with rate limiting"""
        url = f"{self.base_url}/{endpoint}"
        
        print(f"Making API request to: {url}")
        time.sleep(self.rate_limit_delay)  # Rate limiting
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            print(f"API request successful: {endpoint}")
            return response.json()
        except requests.exceptions.Timeout:
            print(f"API request timed out: {endpoint}")
            raise Exception(f"GW2 API request timed out for {endpoint}")
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {endpoint} - {str(e)}")
            raise Exception(f"GW2 API request failed for {endpoint}: {str(e)}")
    
    def get_account_info(self) -> Dict:
        """Get basic account information"""
        return self._make_request("account")
    
    def get_bank(self) -> List[Dict]:
        """Get bank contents"""
        return self._make_request("account/bank")
    
    def get_materials(self) -> List[Dict]:
        """Get material storage contents"""
        return self._make_request("account/materials")
    
    def get_characters(self) -> List[str]:
        """Get list of character names"""
        return self._make_request("characters")
    
    def get_character_inventory(self, character_name: str) -> Dict:
        """Get character's inventory"""
        return self._make_request(f"characters/{character_name}/inventory")
    
    def get_character_equipment(self, character_name: str) -> Dict:
        """Get character's equipment"""
        return self._make_request(f"characters/{character_name}/equipment")
    
    def get_shared_inventory(self) -> List[Dict]:
        """Get shared inventory slots"""
        return self._make_request("account/inventory")
    
    def get_legendary_armory(self) -> Dict:
        """Get legendary armory contents"""
        return self._make_request("account/legendaryarmory")
    
    def get_item_info(self, item_ids: List[int]) -> List[Dict]:
        """Get information about specific items"""
        if not item_ids:
            return []
        
        # GW2 API can handle up to 200 IDs at once
        all_items = []
        for i in range(0, len(item_ids), 200):
            batch = item_ids[i:i+200]
            params = {"ids": ",".join(map(str, batch))}
            items = self._make_request("items", params)
            all_items.extend(items)
        
        return all_items
    
    def get_account_achievements(self) -> List[Dict]:
        """Get account achievement progress"""
        return self._make_request("account/achievements")
    
    def get_wallet(self) -> List[Dict]:
        """Get account wallet (currencies)"""
        return self._make_request("account/wallet")
    
    def get_unlocks(self) -> List[int]:
        """Get account unlocks (recipes, skins, etc.)"""
        return self._make_request("account/unlocks")
    
    def search_items_by_name(self, name: str) -> List[Dict]:
        """Search for items by name (helper method)"""
        # This is a simplified search - in practice you'd want to cache item data
        # or use a more sophisticated search mechanism
        all_items = self._make_request("items")
        matching_items = []
        
        # Get item details for items that might match
        # This is inefficient but works for demonstration
        for item_id in all_items[:100]:  # Limit to first 100 for demo
            try:
                item_info = self.get_item_info([item_id])[0]
                if name.lower() in item_info.get('name', '').lower():
                    matching_items.append(item_info)
            except:
                continue
                
        return matching_items