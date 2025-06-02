import re
import logging
from typing import Tuple, Optional
from config import Config

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class Validators:
    """Input validation utilities"""
    
    @staticmethod
    def validate_item_name(item_name: str) -> Tuple[bool, str]:
        """Validate item name format and length"""
        if not item_name:
            return False, "Item name cannot be empty"
        
        if len(item_name) > Config.MAX_ITEM_NAME_LENGTH:
            return False, f"Item name too long (max {Config.MAX_ITEM_NAME_LENGTH} characters)"
        
        # Check for valid characters (alphanumeric, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-Z0-9\s\-'\.]+$", item_name):
            return False, "Item name contains invalid characters"
        
        # Trim whitespace
        item_name = item_name.strip()
        if not item_name:
            return False, "Item name cannot be only whitespace"
        
        return True, item_name
    
    @staticmethod
    def validate_price(price_str: str) -> Tuple[bool, Optional[float], str]:
        """Validate price format and range"""
        try:
            # Remove currency symbols and whitespace
            price_str = price_str.replace('$', '').replace(',', '').strip()
            
            if not price_str:
                return False, None, "Price cannot be empty"
            
            price = float(price_str)
            
            if price < Config.MIN_PRICE:
                return False, None, f"Price too low (minimum ${Config.MIN_PRICE})"
            
            if price > Config.MAX_PRICE:
                return False, None, f"Price too high (maximum ${Config.MAX_PRICE:,})"
            
            # Round to 2 decimal places
            price = round(price, 2)
            
            return True, price, ""
            
        except ValueError:
            return False, None, "Invalid price format (use numbers only)"
    
    @staticmethod
    def validate_listing_type(listing_type: str) -> Tuple[bool, str]:
        """Validate listing type"""
        listing_type = listing_type.lower().strip()
        
        if listing_type not in ['buying', 'selling']:
            return False, "Listing type must be 'buying' or 'selling'"
        
        return True, listing_type
    
    @staticmethod
    def validate_category(category: str) -> Tuple[bool, str]:
        """Validate item category"""
        if not category:
            return False, "Category cannot be empty"
        
        category = category.strip()
        if len(category) > 50:
            return False, "Category name too long (max 50 characters)"
        
        if not re.match(r"^[a-zA-Z0-9\s\-]+$", category):
            return False, "Category contains invalid characters"
        
        return True, category
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input for database storage"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove potentially dangerous characters
        text = re.sub(r'[<>"\']', '', text)
        
        return text
    
    @staticmethod
    def validate_search_query(query: str) -> Tuple[bool, str]:
        """Validate search query"""
        if not query:
            return False, "Search query cannot be empty"
        
        query = query.strip()
        if len(query) < 2:
            return False, "Search query too short (minimum 2 characters)"
        
        if len(query) > 50:
            return False, "Search query too long (maximum 50 characters)"
        
        return True, query

def validate_discord_permissions(interaction, required_permissions: list) -> Tuple[bool, str]:
    """Validate Discord permissions for commands"""
    if not interaction.user.guild_permissions:
        return False, "Unable to check permissions"
    
    missing_perms = []
    for perm in required_permissions:
        if not getattr(interaction.user.guild_permissions, perm, False):
            missing_perms.append(perm.replace('_', ' ').title())
    
    if missing_perms:
        return False, f"Missing permissions: {', '.join(missing_perms)}"
    
    return True, ""

def is_admin(interaction) -> bool:
    """Check if user has administrator permissions"""
    return interaction.user.guild_permissions.administrator
