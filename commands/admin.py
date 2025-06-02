import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional

from utils.validators import Validators, is_admin

logger = logging.getLogger(__name__)

class AdminCommands(commands.Cog):
    """Administrator-only commands for managing the marketplace"""
    
    def __init__(self, db_manager, item_cache):
        self.db_manager = db_manager
        self.item_cache = item_cache
    
    @app_commands.command(name="admin_add_item", description="[ADMIN] Add a new item to the marketplace")
    @app_commands.describe(
        name="The name of the item",
        category="The category of the item",
        description="A description of the item (optional)"
    )
    async def add_item(self, interaction: discord.Interaction, name: str, 
                      category: str, description: Optional[str] = None):
        """Add a new item to the game items list (admin only)"""
        
        # Check admin permissions
        if not is_admin(interaction):
            await interaction.response.send_message(
                "❌ You need administrator permissions to use this command.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validate inputs
            valid_name, clean_name = Validators.validate_item_name(name)
            if not valid_name:
                await interaction.followup.send(f"❌ {clean_name}", ephemeral=True)
                return
            
            valid_category, clean_category = Validators.validate_category(category)
            if not valid_category:
                await interaction.followup.send(f"❌ {clean_category}", ephemeral=True)
                return
            
            # Check if item already exists
            if self.item_cache.is_valid_item(clean_name):
                await interaction.followup.send(
                    f"❌ Item '{clean_name}' already exists in the marketplace.",
                    ephemeral=True
                )
                return
            
            # Sanitize description
            clean_description = Validators.sanitize_input(description) if description else None
            
            # Ensure admin user exists in database
            await self.db_manager.ensure_user_exists(
                interaction.user.id, 
                interaction.user.display_name
            )
            
            # Add item to database
            item_id = await self.db_manager.add_game_item(
                clean_name, clean_category, clean_description, interaction.user.id
            )
            
            if item_id:
                # Add to cache
                self.item_cache.add_item(item_id, clean_name, clean_category)
                
                # Log admin action
                await self.db_manager.log_admin_action(
                    interaction.user.id, 
                    "ADD_ITEM", 
                    item_id, 
                    details=f"Added item: {clean_name}"
                )
                
                embed = discord.Embed(
                    title="✅ Item Added Successfully",
                    description=f"**{clean_name}** has been added to the marketplace.",
                    color=0x00ff00
                )
                embed.add_field(name="Category", value=clean_category, inline=True)
                embed.add_field(name="Item ID", value=str(item_id), inline=True)
                
                if clean_description:
                    embed.add_field(name="Description", value=clean_description, inline=False)
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                logger.info(f"Admin {interaction.user.id} added item: {clean_name}")
                
            else:
                await interaction.followup.send(
                    "❌ Failed to add item. It may already exist.",
                    ephemeral=True
                )
            
        except Exception as e:
            logger.error(f"Error in admin add_item command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while adding the item.",
                ephemeral=True
            )
    
    @app_commands.command(name="admin_remove_item", description="[ADMIN] Remove an item from the marketplace")
    @app_commands.describe(name="The name of the item to remove")
    async def remove_item(self, interaction: discord.Interaction, name: str):
        """Remove an item from the game items list (admin only)"""
        
        # Check admin permissions
        if not is_admin(interaction):
            await interaction.response.send_message(
                "❌ You need administrator permissions to use this command.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validate input
            valid_name, clean_name = Validators.validate_item_name(name)
            if not valid_name:
                await interaction.followup.send(f"❌ {clean_name}", ephemeral=True)
                return
            
            # Check if item exists
            item_id = self.item_cache.get_item_id(clean_name)
            if not item_id:
                await interaction.followup.send(
                    f"❌ Item '{clean_name}' not found in the marketplace.",
                    ephemeral=True
                )
                return
            
            # Remove from database (this will cascade delete listings)
            success = await self.db_manager.remove_game_item(clean_name)
            
            if success:
                # Remove from cache
                self.item_cache.remove_item(clean_name)
                
                # Log admin action
                await self.db_manager.log_admin_action(
                    interaction.user.id,
                    "REMOVE_ITEM",
                    item_id,
                    details=f"Removed item: {clean_name}"
                )
                
                embed = discord.Embed(
                    title="✅ Item Removed Successfully",
                    description=f"**{clean_name}** has been removed from the marketplace.\n\n"
                               f"⚠️ All associated listings have been deleted.",
                    color=0xff9900
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                
                logger.info(f"Admin {interaction.user.id} removed item: {clean_name}")
                
            else:
                await interaction.followup.send(
                    "❌ Failed to remove item from database.",
                    ephemeral=True
                )
            
        except Exception as e:
            logger.error(f"Error in admin remove_item command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while removing the item.",
                ephemeral=True
            )
    
    @app_commands.command(name="admin_stats", description="[ADMIN] View marketplace statistics")
    async def marketplace_stats(self, interaction: discord.Interaction):
        """Show marketplace statistics (admin only)"""
        
        # Check admin permissions
        if not is_admin(interaction):
            await interaction.response.send_message(
                "❌ You need administrator permissions to use this command.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            from database.schema import get_database_stats
            stats = await get_database_stats(self.db_manager.db_path)
            
            embed = discord.Embed(
                title="📊 Marketplace Statistics",
                color=0x0099ff
            )
            
            embed.add_field(
                name="👥 Users",
                value=f"{stats.get('users', 0):,}",
                inline=True
            )
            
            embed.add_field(
                name="📦 Items",
                value=f"{stats.get('game_items', 0):,}",
                inline=True
            )
            
            embed.add_field(
                name="📋 Active Listings",
                value=f"{stats.get('listings', 0):,}",
                inline=True
            )
            
            embed.add_field(
                name="🤝 Total Matches",
                value=f"{stats.get('matches', 0):,}",
                inline=True
            )
            
            embed.add_field(
                name="📝 Admin Actions",
                value=f"{stats.get('admin_activity_log', 0):,}",
                inline=True
            )
            
            embed.add_field(
                name="💾 Cache Status",
                value=f"Loaded: {self.item_cache.is_loaded}\nSize: {self.item_cache.size:,}",
                inline=True
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in admin stats command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while fetching statistics.",
                ephemeral=True
            )
    
    @app_commands.command(name="admin_reload_cache", description="[ADMIN] Reload the item cache from database")
    async def reload_cache(self, interaction: discord.Interaction):
        """Reload item cache from database (admin only)"""
        
        # Check admin permissions
        if not is_admin(interaction):
            await interaction.response.send_message(
                "❌ You need administrator permissions to use this command.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Reload cache
            await self.item_cache.load_items(self.db_manager)
            
            # Log admin action
            await self.db_manager.log_admin_action(
                interaction.user.id,
                "RELOAD_CACHE",
                details="Reloaded item cache"
            )
            
            embed = discord.Embed(
                title="✅ Cache Reloaded",
                description=f"Item cache reloaded successfully.\n\n"
                           f"**Items loaded:** {self.item_cache.size:,}",
                color=0x00ff00
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            logger.info(f"Admin {interaction.user.id} reloaded item cache")
            
        except Exception as e:
            logger.error(f"Error in admin reload_cache command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while reloading the cache.",
                ephemeral=True
            )
    
    @app_commands.command(name="admin_list_items", description="[ADMIN] List all items with details")
    @app_commands.describe(category="Filter by category (optional)")
    async def list_items(self, interaction: discord.Interaction, category: Optional[str] = None):
        """List all items with admin details"""
        
        # Check admin permissions
        if not is_admin(interaction):
            await interaction.response.send_message(
                "❌ You need administrator permissions to use this command.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            items = await self.db_manager.get_all_game_items()
            
            if category:
                items = [item for item in items if item.get('category', '').lower() == category.lower()]
            
            if not items:
                await interaction.followup.send(
                    f"❌ No items found{f' in category {category}' if category else ''}.",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title=f"📦 Admin Item List{f' - {category}' if category else ''}",
                description=f"Total items: {len(items)}",
                color=0x0099ff
            )
            
            # Group items by category
            categories = {}
            for item in items:
                cat = item.get('category', 'Uncategorized')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(f"• **{item['name']}** (ID: {item['id']})")
            
            # Add fields for each category
            for cat, item_list in categories.items():
                if len(item_list) <= 10:
                    embed.add_field(
                        name=f"📂 {cat}",
                        value="\n".join(item_list),
                        inline=False
                    )
                else:
                    # Split long lists
                    embed.add_field(
                        name=f"📂 {cat} (showing first 10)",
                        value="\n".join(item_list[:10]) + f"\n... and {len(item_list) - 10} more",
                        inline=False
                    )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in admin list_items command: {e}")
            await interaction.followup.send(
                "❌ An error occurred while listing items.",
                ephemeral=True
            )
