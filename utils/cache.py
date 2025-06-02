import logging
from typing import Dict, Set, Optional, List

logger = logging.getLogger(__name__)

class ItemCache:
    """In-memory cache for O(1) item validation"""
    
    def __init__(self):
        self.items_by_name: Dict[str, int] = {}  # item_name -> item_id
        self.items_by_id: Dict[int, str] = {}    # item_id -> item_name
        self.categories: Dict[int, str] = {}     # item_id -> category
        self._loaded = False
    
    async def load_items(self, db_manager):
        """Load all items from database into memory"""
        try:
            items = await db_manager.get_all_game_items()
            
            self.items_by_name.clear()
            self.items_by_id.clear()
            self.categories.clear()
            
            for item in items:
                item_id = item["id"]
                item_name = item["name"].lower()  # Case-insensitive lookup
                category = item["category"]
                
                self.items_by_name[item_name] = item_id
                self.items_by_id[item_id] = item["name"]
                self.categories[item_id] = category
            
            self._loaded = True
            logger.info(f"Loaded {len(items)} items into cache")
            
        except Exception as e:
            logger.error(f"Error loading items into cache: {e}")
            self._loaded = False
    
    def is_valid_item(self, item_name: str) -> bool:
        """Check if item exists in O(1) time"""
        return item_name.lower() in self.items_by_name
    
    def get_item_id(self, item_name: str) -> Optional[int]:
        """Get item ID by name in O(1) time"""
        return self.items_by_name.get(item_name.lower())
    
    def get_item_name(self, item_id: int) -> Optional[str]:
        """Get item name by ID in O(1) time"""
        return self.items_by_id.get(item_id)
    
    def get_item_category(self, item_id: int) -> Optional[str]:
        """Get item category by ID"""
        return self.categories.get(item_id)
    
    def add_item(self, item_id: int, item_name: str, category: str = None):
        """Add item to cache"""
        name_lower = item_name.lower()
        self.items_by_name[name_lower] = item_id
        self.items_by_id[item_id] = item_name
        if category:
            self.categories[item_id] = category
        logger.info(f"Added item to cache: {item_name}")
    
    def remove_item(self, item_name: str) -> bool:
        """Remove item from cache"""
        name_lower = item_name.lower()
        if name_lower in self.items_by_name:
            item_id = self.items_by_name[name_lower]
            del self.items_by_name[name_lower]
            del self.items_by_id[item_id]
            if item_id in self.categories:
                del self.categories[item_id]
            logger.info(f"Removed item from cache: {item_name}")
            return True
        return False
    
    def get_all_items(self) -> List[str]:
        """Get all item names"""
        return list(self.items_by_id.values())
    
    def search_items(self, query: str, limit: int = 10) -> List[str]:
        """Search items by partial name match"""
        query_lower = query.lower()
        matches = []
        
        for name_lower, item_id in self.items_by_name.items():
            if query_lower in name_lower:
                matches.append(self.items_by_id[item_id])
                if len(matches) >= limit:
                    break
        
        return matches
    
    @property
    def is_loaded(self) -> bool:
        """Check if cache is loaded"""
        return self._loaded
    
    @property
    def size(self) -> int:
        """Get cache size"""
        return len(self.items_by_name)
