from typing import Dict
from gw2_api import GW2API
from progress_tracker import progress_tracker

class DataFetcher:
    def __init__(self, api_key: str, progress_tracker_instance=None, task_id=None):
        self.api = GW2API(api_key)
        self.progress_tracker = progress_tracker_instance
        self.task_id = task_id
    
    def _update_progress(self, progress: int, message: str, step: str = None, substep: str = None):
        """Update progress if tracker is available"""
        if self.progress_tracker and self.task_id:
            self.progress_tracker.update_progress(self.task_id, progress, message, step, substep)
    
    def fetch_all_account_data(self) -> Dict:
        """Fetch all account data and return it as a structured dictionary"""
        data = {}
        
        try:
            # Account info
            self._update_progress(5, "Getting account information...", "account", "Basic account data")
            data['account_info'] = self.api.get_account_info()
            
            # Bank items
            self._update_progress(10, "Scanning bank...", "bank", "Bank slots")
            data['bank_items'] = self._get_all_items()
            
            # Material storage
            self._update_progress(40, "Scanning material storage...", "materials", "Material storage")
            data['materials'] = self._get_material_storage()
            
            # Wallet
            self._update_progress(60, "Scanning wallet...", "wallet", "Currencies")
            data['wallet'] = self._get_wallet()
            
            # Achievements
            self._update_progress(80, "Checking achievements...", "achievements", "World completion")
            data['achievements'] = self._get_achievement_progress()
            
            self._update_progress(95, "Finalizing data...", "finalize", "Organizing data")
            
            return data
            
        except Exception as e:
            print(f"Error fetching account data: {e}")
            raise e
    
    def _get_all_items(self) -> Dict[int, int]:
        """Get all items from bank, characters, and shared inventory"""
        items = {}
        
        # Bank items
        try:
            bank = self.api.get_bank()
            for slot in bank:
                if slot and slot.get('id'):
                    item_id = slot['id']
                    count = slot.get('count', 1)
                    items[item_id] = items.get(item_id, 0) + count
        except:
            pass
        
        # Shared inventory
        try:
            shared = self.api.get_shared_inventory()
            for slot in shared:
                if slot and slot.get('id'):
                    item_id = slot['id']
                    count = slot.get('count', 1)
                    items[item_id] = items.get(item_id, 0) + count
        except:
            pass
        
        # Character inventories
        try:
            characters = self.api.get_characters()
            total_chars = len(characters)
            
            for i, char_name in enumerate(characters):
                self._update_progress(
                    15 + (i * 20 // total_chars), 
                    f"Scanning character inventories...", 
                    "characters", 
                    f"Character {i+1}/{total_chars}: {char_name}"
                )
                try:
                    inventory = self.api.get_character_inventory(char_name)
                    for bag in inventory.get('bags', []):
                        if bag:
                            for slot in bag.get('inventory', []):
                                if slot and slot.get('id'):
                                    item_id = slot['id']
                                    count = slot.get('count', 1)
                                    items[item_id] = items.get(item_id, 0) + count
                except:
                    continue
        except:
            pass
        
        return items
    
    def _get_material_storage(self) -> Dict[int, int]:
        """Get material storage contents"""
        materials = {}
        try:
            material_storage = self.api.get_materials()
            for material in material_storage:
                if material.get('id') and material.get('count', 0) > 0:
                    materials[material['id']] = material['count']
        except:
            pass
        return materials
    
    def _get_wallet(self) -> Dict[int, int]:
        """Get wallet contents (currencies)"""
        wallet = {}
        try:
            wallet_data = self.api.get_wallet()
            for currency in wallet_data:
                if currency.get('id') and currency.get('value', 0) > 0:
                    wallet[currency['id']] = currency['value']
        except:
            pass
        return wallet
    
    def _get_achievement_progress(self) -> Dict:
        """Get achievement progress for world completion, etc."""
        try:
            achievements = self.api.get_account_achievements()
            # Look for world completion achievement (ID: 91)
            world_completion = False
            for achievement in achievements:
                if achievement.get('id') == 91 and achievement.get('done', False):
                    world_completion = True
                    break
            return {"world_completion": world_completion}
        except:
            return {"world_completion": False}