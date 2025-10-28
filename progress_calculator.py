from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from legendary_data import LEGENDARY_REQUIREMENTS, MATERIAL_IDS, CURRENCY_IDS
import math

class ProgressCalculator:
    def __init__(self, gw2_api, progress_tracker=None, task_id=None):
        self.api = gw2_api
        self.progress_tracker = progress_tracker
        self.task_id = task_id
    
    def _update_progress(self, progress: int, message: str, step: str = None, substep: str = None):
        """Update progress if tracker is available"""
        if self.progress_tracker and self.task_id:
            self.progress_tracker.update_progress(self.task_id, progress, message, step, substep)
        
    def calculate_progress(self, legendary_name: str) -> Dict:
        """Calculate progress towards a specific legendary weapon"""
        if legendary_name not in LEGENDARY_REQUIREMENTS:
            raise ValueError(f"Unknown legendary: {legendary_name}")
        
        requirements = LEGENDARY_REQUIREMENTS[legendary_name]
        progress = {
            "legendary_name": legendary_name,
            "overall_progress": 0.0,
            "precursor": self._check_precursor_progress(requirements),
            "gifts": {},
            "time_gated": self._calculate_time_gated_progress(requirements),
            "estimated_days": 0,
            "total_cost_estimate": requirements.get("estimated_cost_gold", 0)
        }
        
        # Get account data
        try:
            self._update_progress(5, "Fetching bank items...", "bank", "Scanning bank slots")
            bank_items = self._get_all_items()
            print(f"Found {len(bank_items)} unique items in inventories")
            
            self._update_progress(25, "Fetching material storage...", "materials", "Scanning material storage")
            materials = self._get_material_storage()
            print(f"Found {len(materials)} materials in storage")
            
            self._update_progress(40, "Fetching wallet currencies...", "wallet", "Scanning currencies")
            wallet = self._get_wallet()
            print(f"Found {len(wallet)} currencies in wallet")
            
            self._update_progress(60, "Fetching achievement progress...", "achievements", "Checking world completion")
            achievements = self._get_achievement_progress()
            print(f"Achievement data: {achievements}")
        except Exception as e:
            print(f"Error fetching account data: {e}")
            # Use empty data if API calls fail
            bank_items = {}
            materials = {}
            wallet = {}
            achievements = {"world_completion": False}
        
        # Calculate gift progress
        self._update_progress(70, "Calculating legendary progress...", "calculation", "Analyzing materials")
        total_gift_progress = 0
        gift_count = 0
        
        for gift_name, gift_requirements in requirements["gifts"].items():
            gift_progress = self._calculate_gift_progress(gift_name, gift_requirements, 
                                                        bank_items, materials, wallet, achievements)
            progress["gifts"][gift_name] = gift_progress
            total_gift_progress += gift_progress["progress"]
            gift_count += 1
        
        self._update_progress(85, "Finalizing calculations...", "calculation", "Computing completion time")
        
        # Calculate overall progress
        precursor_weight = 0.4  # Precursor is 40% of the work
        gifts_weight = 0.6      # Gifts are 60% of the work
        
        avg_gift_progress = total_gift_progress / gift_count if gift_count > 0 else 0
        progress["overall_progress"] = (progress["precursor"]["progress"] * precursor_weight + 
                                      avg_gift_progress * gifts_weight)
        
        # Calculate estimated completion time
        progress["estimated_days"] = self._calculate_estimated_days(progress)
        
        self._update_progress(95, "Almost done...", "calculation", "Preparing results")
        
        return progress
    
    def calculate_progress_from_cache(self, legendary_name: str, cached_data: Dict) -> Dict:
        """Calculate progress using cached account data"""
        if legendary_name not in LEGENDARY_REQUIREMENTS:
            raise ValueError(f"Unknown legendary: {legendary_name}")
        
        requirements = LEGENDARY_REQUIREMENTS[legendary_name]
        progress = {
            "legendary_name": legendary_name,
            "overall_progress": 0.0,
            "precursor": self._check_precursor_progress_from_cache(requirements, cached_data),
            "gifts": {},
            "time_gated": self._calculate_time_gated_progress_from_cache(requirements, cached_data),
            "estimated_days": 0,
            "total_cost_estimate": requirements.get("estimated_cost_gold", 0)
        }
        
        # Use cached data directly
        bank_items = cached_data.get('bank_items', {})
        materials = cached_data.get('materials', {})
        wallet = cached_data.get('wallet', {})
        achievements = cached_data.get('achievements', {"world_completion": False})
        
        # Calculate gift progress
        total_gift_progress = 0
        gift_count = 0
        
        for gift_name, gift_requirements in requirements["gifts"].items():
            gift_progress = self._calculate_gift_progress(gift_name, gift_requirements, 
                                                        bank_items, materials, wallet, achievements)
            progress["gifts"][gift_name] = gift_progress
            total_gift_progress += gift_progress["progress"]
            gift_count += 1
        
        # Calculate overall progress
        precursor_weight = 0.4  # Precursor is 40% of the work
        gifts_weight = 0.6      # Gifts are 60% of the work
        
        avg_gift_progress = total_gift_progress / gift_count if gift_count > 0 else 0
        progress["overall_progress"] = (progress["precursor"]["progress"] * precursor_weight + 
                                      avg_gift_progress * gifts_weight)
        
        # Calculate estimated completion time
        progress["estimated_days"] = self._calculate_estimated_days(progress)
        
        return progress
    
    def _check_precursor_progress_from_cache(self, requirements: Dict, cached_data: Dict) -> Dict:
        """Check if user has the precursor using cached data"""
        precursor_id = requirements.get("precursor_id")
        if not precursor_id:
            return {"progress": 0.0, "has_precursor": False, "name": requirements.get("precursor", "Unknown")}
        
        items = cached_data.get('bank_items', {})
        has_precursor = precursor_id in items and items[precursor_id] > 0
        
        return {
            "progress": 1.0 if has_precursor else 0.0,
            "has_precursor": has_precursor,
            "name": requirements.get("precursor", "Unknown"),
            "id": precursor_id
        }
    
    def _calculate_time_gated_progress_from_cache(self, requirements: Dict, cached_data: Dict) -> Dict:
        """Calculate progress on time-gated materials using cached data"""
        time_gated = requirements.get("time_gated_materials", {})
        materials = cached_data.get('materials', {})
        items = cached_data.get('bank_items', {})
        
        progress = {
            "materials": {},
            "total_days_needed": 0,
            "max_days_for_completion": 0
        }
        
        max_days = 0
        for material_name, info in time_gated.items():
            material_id = MATERIAL_IDS.get(material_name)
            if not material_id:
                continue
            
            current_count = materials.get(material_id, 0) + items.get(material_id, 0)
            needed_count = info["needed"]
            daily_craft = info["daily_craft"]
            
            remaining = max(0, needed_count - current_count)
            days_needed = math.ceil(remaining / daily_craft) if daily_craft > 0 else 0
            
            progress["materials"][material_name] = {
                "current": current_count,
                "needed": needed_count,
                "remaining": remaining,
                "days_needed": days_needed,
                "daily_craft": daily_craft,
                "recipe_cost": info.get("recipe_cost", "Unknown")
            }
            
            max_days = max(max_days, days_needed)
        
        progress["max_days_for_completion"] = max_days
        progress["total_days_needed"] = max_days  # Since you can craft all in parallel
        
        return progress
    
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
                    10 + (i * 15 // total_chars), 
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
    
    def _check_precursor_progress(self, requirements: Dict) -> Dict:
        """Check if user has the precursor"""
        precursor_id = requirements.get("precursor_id")
        if not precursor_id:
            return {"progress": 0.0, "has_precursor": False, "name": requirements.get("precursor", "Unknown")}
        
        items = self._get_all_items()
        has_precursor = precursor_id in items and items[precursor_id] > 0
        
        return {
            "progress": 1.0 if has_precursor else 0.0,
            "has_precursor": has_precursor,
            "name": requirements.get("precursor", "Unknown"),
            "id": precursor_id
        }
    
    def _calculate_gift_progress(self, gift_name: str, gift_requirements: Dict, 
                               items: Dict, materials: Dict, wallet: Dict, achievements: Dict) -> Dict:
        """Calculate progress for a specific gift"""
        if gift_name == "Gift of Mastery":
            return self._calculate_mastery_gift_progress(gift_requirements, achievements)
        
        progress = {
            "name": gift_name,
            "progress": 0.0,
            "materials": {},
            "missing_materials": {}
        }
        
        total_materials = 0
        completed_materials = 0
        
        for material_name, needed_count in gift_requirements.get("materials", {}).items():
            material_id = MATERIAL_IDS.get(material_name)
            if not material_id:
                continue
            
            # Check items and materials storage
            current_count = items.get(material_id, 0) + materials.get(material_id, 0)
            
            progress["materials"][material_name] = {
                "needed": needed_count,
                "current": current_count,
                "progress": min(1.0, current_count / needed_count) if needed_count > 0 else 1.0
            }
            
            if current_count >= needed_count:
                completed_materials += 1
            else:
                progress["missing_materials"][material_name] = needed_count - current_count
            
            total_materials += 1
        
        if total_materials > 0:
            progress["progress"] = completed_materials / total_materials
        
        return progress
    
    def _calculate_mastery_gift_progress(self, requirements: Dict, achievements: Dict) -> Dict:
        """Calculate Gift of Mastery progress"""
        progress = {
            "name": "Gift of Mastery",
            "progress": 0.0,
            "requirements": {},
            "missing_requirements": []
        }
        
        total_requirements = len(requirements.get("requirements", []))
        completed_requirements = 0
        
        for requirement in requirements.get("requirements", []):
            if requirement == "World Completion":
                completed = achievements.get("world_completion", False)
                progress["requirements"][requirement] = {
                    "completed": completed,
                    "progress": 1.0 if completed else 0.0
                }
                if completed:
                    completed_requirements += 1
                else:
                    progress["missing_requirements"].append(requirement)
            else:
                # For other requirements, assume not completed for now
                # In a full implementation, you'd check for specific items/achievements
                progress["requirements"][requirement] = {
                    "completed": False,
                    "progress": 0.0
                }
                progress["missing_requirements"].append(requirement)
        
        if total_requirements > 0:
            progress["progress"] = completed_requirements / total_requirements
        
        return progress
    
    def _calculate_time_gated_progress(self, requirements: Dict) -> Dict:
        """Calculate progress on time-gated materials"""
        time_gated = requirements.get("time_gated_materials", {})
        materials = self._get_material_storage()
        items = self._get_all_items()
        
        progress = {
            "materials": {},
            "total_days_needed": 0,
            "max_days_for_completion": 0
        }
        
        max_days = 0
        for material_name, info in time_gated.items():
            material_id = MATERIAL_IDS.get(material_name)
            if not material_id:
                continue
            
            current_count = materials.get(material_id, 0) + items.get(material_id, 0)
            needed_count = info["needed"]
            daily_craft = info["daily_craft"]
            
            remaining = max(0, needed_count - current_count)
            days_needed = math.ceil(remaining / daily_craft) if daily_craft > 0 else 0
            
            progress["materials"][material_name] = {
                "current": current_count,
                "needed": needed_count,
                "remaining": remaining,
                "days_needed": days_needed,
                "daily_craft": daily_craft,
                "recipe_cost": info.get("recipe_cost", "Unknown")
            }
            
            max_days = max(max_days, days_needed)
        
        progress["max_days_for_completion"] = max_days
        progress["total_days_needed"] = max_days  # Since you can craft all in parallel
        
        return progress
    
    def _calculate_estimated_days(self, progress: Dict) -> int:
        """Calculate estimated days to completion"""
        # Time-gated materials are usually the bottleneck
        time_gated_days = progress["time_gated"]["total_days_needed"]
        
        # Add buffer for gathering other materials (rough estimate)
        other_materials_days = 0
        if progress["overall_progress"] < 0.5:
            other_materials_days = 14  # 2 weeks for materials gathering
        elif progress["overall_progress"] < 0.8:
            other_materials_days = 7   # 1 week
        
        return max(time_gated_days, other_materials_days)