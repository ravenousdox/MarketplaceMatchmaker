import aiosqlite
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Handles all database operations for the marketplace bot"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get_connection(self):
        """Get database connection with foreign keys enabled"""
        return aiosqlite.connect(self.db_path)
    
    async def close(self):
        """Close database connections"""
        pass  # aiosqlite handles connection cleanup automatically
    
    # User operations
    async def ensure_user_exists(self, user_id: int, username: str) -> bool:
        """Ensure user exists in database, create if not"""
        try:
            async with self.get_connection() as db:
                await db.execute("PRAGMA foreign_keys = ON")
                await db.execute("""
                    INSERT OR REPLACE INTO users (user_id, discord_username, last_activity)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (user_id, username))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Error ensuring user exists: {e}")
            return False
    
    # Game items operations
    async def add_game_item(self, item_name: str, category: str, description: str, created_by: int) -> Optional[int]:
        """Add a new game item (admin only)"""
        try:
            async with self.get_connection() as db:
                await db.execute("PRAGMA foreign_keys = ON")
                cursor = await db.execute("""
                    INSERT INTO game_items (item_name, category, description, created_by)
                    VALUES (?, ?, ?, ?)
                """, (item_name, category, description, created_by))
                await db.commit()
                return cursor.lastrowid
        except aiosqlite.IntegrityError:
            return None  # Item already exists
        except Exception as e:
            logger.error(f"Error adding game item: {e}")
            return None
    
    async def remove_game_item(self, item_name: str) -> bool:
        """Remove a game item (admin only)"""
        try:
            async with self.get_connection() as db:
                cursor = await db.execute("DELETE FROM game_items WHERE item_name = ?", (item_name,))
                await db.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error removing game item: {e}")
            return False
    
    async def get_all_game_items(self) -> List[Dict]:
        """Get all game items for cache loading"""
        try:
            async with self.get_connection() as db:
                await db.execute("PRAGMA foreign_keys = ON")
                cursor = await db.execute("SELECT item_id, item_name, category FROM game_items")
                rows = await cursor.fetchall()
                return [{"id": row[0], "name": row[1], "category": row[2]} for row in rows]
        except Exception as e:
            logger.error(f"Error getting game items: {e}")
            return []
    
    async def get_item_by_name(self, item_name: str) -> Optional[Dict]:
        """Get item details by name"""
        try:
            async with self.get_connection() as db:
                cursor = await db.execute("""
                    SELECT item_id, item_name, category, description 
                    FROM game_items WHERE item_name = ?
                """, (item_name,))
                row = await cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "name": row[1],
                        "category": row[2],
                        "description": row[3]
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting item by name: {e}")
            return None
    
    # Listing operations
    async def add_listing(self, user_id: int, item_id: int, listing_type: str, price: float) -> bool:
        """Add or update a user listing"""
        try:
            async with self.get_connection() as db:
                await db.execute("""
                    INSERT OR REPLACE INTO listings (user_id, item_id, listing_type, price, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, item_id, listing_type, price))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding listing: {e}")
            return False
    
    async def remove_listing(self, user_id: int, item_id: int, listing_type: str) -> bool:
        """Remove a user listing"""
        try:
            async with self.get_connection() as db:
                cursor = await db.execute("""
                    DELETE FROM listings 
                    WHERE user_id = ? AND item_id = ? AND listing_type = ?
                """, (user_id, item_id, listing_type))
                await db.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error removing listing: {e}")
            return False
    
    async def get_user_listings(self, user_id: int, listing_type: str = None) -> List[Dict]:
        """Get all listings for a user"""
        try:
            async with self.get_connection() as db:
                query = """
                    SELECT l.listing_id, l.listing_type, l.price, l.created_at, g.item_name
                    FROM listings l
                    JOIN game_items g ON l.item_id = g.item_id
                    WHERE l.user_id = ?
                """
                params = [user_id]
                
                if listing_type:
                    query += " AND l.listing_type = ?"
                    params.append(listing_type)
                
                query += " ORDER BY l.created_at DESC"
                
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                return [{
                    "listing_id": row[0],
                    "type": row[1],
                    "price": row[2],
                    "created_at": row[3],
                    "item_name": row[4]
                } for row in rows]
        except Exception as e:
            logger.error(f"Error getting user listings: {e}")
            return []
    
    async def find_matching_listings(self, item_id: int, listing_type: str, exclude_user: int) -> List[Dict]:
        """Find matching listings for an item (opposite type)"""
        try:
            opposite_type = "selling" if listing_type == "buying" else "buying"
            
            async with self.get_connection() as db:
                cursor = await db.execute("""
                    SELECT l.user_id, l.price, u.discord_username
                    FROM listings l
                    JOIN users u ON l.user_id = u.user_id
                    WHERE l.item_id = ? AND l.listing_type = ? AND l.user_id != ?
                    ORDER BY l.price ASC
                """, (item_id, opposite_type, exclude_user))
                
                rows = await cursor.fetchall()
                return [{
                    "user_id": row[0],
                    "price": row[1],
                    "username": row[2]
                } for row in rows]
        except Exception as e:
            logger.error(f"Error finding matching listings: {e}")
            return []
    
    # Match operations
    async def create_match(self, buyer_id: int, seller_id: int, item_id: int, 
                          buyer_price: float, seller_price: float, thread_id: int) -> Optional[int]:
        """Record a successful match"""
        try:
            async with self.get_connection() as db:
                cursor = await db.execute("""
                    INSERT INTO matches (buyer_user_id, seller_user_id, item_id, 
                                       buyer_price, seller_price, thread_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (buyer_id, seller_id, item_id, buyer_price, seller_price, thread_id))
                await db.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error creating match: {e}")
            return None
    
    # Admin logging
    async def log_admin_action(self, admin_id: int, action_type: str, 
                              target_item_id: int = None, target_user_id: int = None, 
                              details: str = None) -> bool:
        """Log admin activity"""
        try:
            async with self.get_connection() as db:
                await db.execute("""
                    INSERT INTO admin_activity_log (admin_user_id, action_type, 
                                                   target_item_id, target_user_id, details)
                    VALUES (?, ?, ?, ?, ?)
                """, (admin_id, action_type, target_item_id, target_user_id, details))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Error logging admin action: {e}")
            return False
