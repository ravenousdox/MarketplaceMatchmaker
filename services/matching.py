import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class MatchingService:
    """Handles real-time marketplace matching between buyers and sellers"""
    
    def __init__(self, db_manager, item_cache, thread_manager):
        self.db_manager = db_manager
        self.item_cache = item_cache
        self.thread_manager = thread_manager
    
    async def check_for_matches(self, user_id: int, item_id: int, listing_type: str, price: float) -> List[Dict]:
        """
        Check for potential matches when a new listing is added
        Returns list of matches found
        """
        try:
            matches = await self.db_manager.find_matching_listings(item_id, listing_type, user_id)
            
            if not matches:
                logger.info(f"No matches found for user {user_id}, item {item_id}, type {listing_type}")
                return []
            
            # Filter matches based on price compatibility
            compatible_matches = []
            for match in matches:
                if self._is_price_compatible(listing_type, price, match['price']):
                    compatible_matches.append(match)
            
            logger.info(f"Found {len(compatible_matches)} compatible matches for user {user_id}")
            return compatible_matches
            
        except Exception as e:
            logger.error(f"Error checking for matches: {e}")
            return []
    
    def _is_price_compatible(self, listing_type: str, user_price: float, match_price: float) -> bool:
        """
        Check if prices are compatible for a trade
        - Buyer's max price >= Seller's min price
        """
        if listing_type == "buying":
            # User is buying, match is selling
            # User willing to pay user_price, seller wants match_price
            return user_price >= match_price
        else:
            # User is selling, match is buying  
            # User wants user_price, buyer willing to pay match_price
            return match_price >= user_price
    
    async def create_match_thread(self, user_id: int, match_user_id: int, item_id: int, 
                                 user_price: float, match_price: float, listing_type: str, 
                                 guild) -> Optional[int]:
        """
        Create a private thread for matched users
        Returns thread ID if successful
        """
        try:
            item_name = self.item_cache.get_item_name(item_id)
            if not item_name:
                logger.error(f"Item name not found for ID {item_id}")
                return None
            
            # Determine buyer and seller
            if listing_type == "buying":
                buyer_id = user_id
                seller_id = match_user_id
                buyer_price = user_price
                seller_price = match_price
            else:
                buyer_id = match_user_id
                seller_id = user_id
                buyer_price = match_price
                seller_price = user_price
            
            # Create the thread
            thread_id = await self.thread_manager.create_marketplace_thread(
                guild, buyer_id, seller_id, item_name, buyer_price, seller_price
            )
            
            if thread_id:
                # Record the match in database
                match_id = await self.db_manager.create_match(
                    buyer_id, seller_id, item_id, buyer_price, seller_price, thread_id
                )
                
                if match_id:
                    logger.info(f"Created match {match_id} with thread {thread_id}")
                    return thread_id
                else:
                    logger.error("Failed to record match in database")
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating match thread: {e}")
            return None
    
    async def process_new_listing(self, user_id: int, item_id: int, listing_type: str, 
                                 price: float, guild) -> List[int]:
        """
        Process a new listing and create threads for any matches
        Returns list of created thread IDs
        """
        created_threads = []
        
        try:
            # Find potential matches
            matches = await self.check_for_matches(user_id, item_id, listing_type, price)
            
            # Create threads for each match
            for match in matches:
                thread_id = await self.create_match_thread(
                    user_id, match['user_id'], item_id, 
                    price, match['price'], listing_type, guild
                )
                
                if thread_id:
                    created_threads.append(thread_id)
            
            if created_threads:
                logger.info(f"Created {len(created_threads)} match threads for user {user_id}")
            
            return created_threads
            
        except Exception as e:
            logger.error(f"Error processing new listing: {e}")
            return []
    
    async def get_price_suggestions(self, item_id: int, listing_type: str) -> Dict:
        """Get price suggestions based on existing listings"""
        try:
            opposite_type = "selling" if listing_type == "buying" else "buying"
            matches = await self.db_manager.find_matching_listings(item_id, listing_type, -1)
            
            if not matches:
                return {"message": "No existing listings found for price comparison"}
            
            prices = [match['price'] for match in matches]
            
            suggestions = {
                "count": len(prices),
                "min_price": min(prices),
                "max_price": max(prices),
                "avg_price": sum(prices) / len(prices)
            }
            
            if listing_type == "buying":
                suggestions["suggestion"] = f"Consider offering ${suggestions['avg_price']:.2f} or higher"
            else:
                suggestions["suggestion"] = f"Consider pricing at ${suggestions['avg_price']:.2f} or lower"
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting price suggestions: {e}")
            return {"error": "Unable to get price suggestions"}
