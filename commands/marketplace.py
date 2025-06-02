import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional

from utils.validators import Validators, ValidationError
from config import Config

logger = logging.getLogger(__name__)

class MarketplaceCommands(commands.Cog):
    """User marketplace commands for buying and selling items"""
    
    def __init__(self, db_manager, item_cache, matching_service):
        self.db_manager = db_manager
        self.item_cache = item_cache
        self.matching_service = matching_service
    
    @app_commands.command(name="buy", description="Add an item to your buying list")
    @app_commands.describe(
        item="The name of the item you want to buy",
        price="The maximum price you're willing to pay"
    )
    async def buy_item(self, interaction: discord.Interaction, item: str, price: str):
        """Add item to user's buying list"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validate inputs
            valid_item, clean_item = Validators.validate_item_name(item)
            if not valid_item:
                await interaction.followup.send(f"❌ {clean_item}", ephemeral=True)
                return
            
            valid_price, price_value, price_error = Validators.validate_price(price)
            if not valid_price:
                await interaction.followup.send(f"❌ {price_error}", ephemeral=True)
                return
            
            # Check if item exists in game items
            if not self.item_cache.is_valid_item(clean_item):
                # Suggest similar items
                suggestions = self.item_cache.search_items(clean_item, 5)
                if suggestions:
                    suggestion_text = "\n".join([f"• {s}" for s in suggestions[:5]])
                    await interaction.followup.send(
                        f"❌ Item '{clean_item}' not found.\n\n**Did you mean:**\n{suggestion_text}",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"❌ Item '{clean_item}' not found. Use `/items` to see available items.",
                        ephemeral=True
                    )
                return
            
            # Ensure user exists in database
            await self.db_manager.ensure_user_exists(interaction.user.id, interaction.user.display_name)
            
            # Get item ID and add listing
            item_id = self.item_cache.get_item_id(clean_item)
            success = await self.db_manager.add_listing(
                interaction.user.id, item_id, "buying", price_value
            )
            
            if not success:
                await interaction.followup.send("❌ Failed to add item to buying list.", ephemeral=True)
                return
            
            # Check for matches
            thread_ids = await self.matching_service.process_new_listing(
                interaction.user.id, item_id, "buying", price_value, interaction.guild
            )
            
            # Send response
            embed = discord.Embed(
                title="✅ Added to Buying List",
                description=f"**{clean_item}**\nMax Price: **${price_value:.2f}**",
                color=0x00ff00
            )
            
            if thread_ids:
                embed.add_field(
                    name="🎯 Matches Found!",
                    value=f"Created {len(thread_ids)} match thread(s). Check your DMs!",
                    inline=False
                )
            else:
                # Get price suggestions
                suggestions = await self.matching_service.get_price_suggestions(item_id, "buying")
                if "suggestion" in suggestions:
                    embed.add_field(
                        name="💡 Market Info",
                        value=suggestions["suggestion"],
                        inline=False
                    )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in buy_item command: {e}")
            await interaction.followup.send("❌ An error occurred. Please try again.", ephemeral=True)
    
    @app_commands.command(name="sell", description="Add an item to your selling list")
    @app_commands.describe(
        item="The name of the item you want to sell",
        price="The minimum price you want to receive"
    )
    async def sell_item(self, interaction: discord.Interaction, item: str, price: str):
        """Add item to user's selling list"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validate inputs
            valid_item, clean_item = Validators.validate_item_name(item)
            if not valid_item:
                await interaction.followup.send(f"❌ {clean_item}", ephemeral=True)
                return
            
            valid_price, price_value, price_error = Validators.validate_price(price)
            if not valid_price:
                await interaction.followup.send(f"❌ {price_error}", ephemeral=True)
                return
            
            # Check if item exists in game items
            if not self.item_cache.is_valid_item(clean_item):
                # Suggest similar items
                suggestions = self.item_cache.search_items(clean_item, 5)
                if suggestions:
                    suggestion_text = "\n".join([f"• {s}" for s in suggestions[:5]])
                    await interaction.followup.send(
                        f"❌ Item '{clean_item}' not found.\n\n**Did you mean:**\n{suggestion_text}",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"❌ Item '{clean_item}' not found. Use `/items` to see available items.",
                        ephemeral=True
                    )
                return
            
            # Ensure user exists in database
            await self.db_manager.ensure_user_exists(interaction.user.id, interaction.user.display_name)
            
            # Get item ID and add listing
            item_id = self.item_cache.get_item_id(clean_item)
            success = await self.db_manager.add_listing(
                interaction.user.id, item_id, "selling", price_value
            )
            
            if not success:
                await interaction.followup.send("❌ Failed to add item to selling list.", ephemeral=True)
                return
            
            # Check for matches
            thread_ids = await self.matching_service.process_new_listing(
                interaction.user.id, item_id, "selling", price_value, interaction.guild
            )
            
            # Send response
            embed = discord.Embed(
                title="✅ Added to Selling List",
                description=f"**{clean_item}**\nMin Price: **${price_value:.2f}**",
                color=0x00ff00
            )
            
            if thread_ids:
                embed.add_field(
                    name="🎯 Matches Found!",
                    value=f"Created {len(thread_ids)} match thread(s). Check your DMs!",
                    inline=False
                )
            else:
                # Get price suggestions
                suggestions = await self.matching_service.get_price_suggestions(item_id, "selling")
                if "suggestion" in suggestions:
                    embed.add_field(
                        name="💡 Market Info",
                        value=suggestions["suggestion"],
                        inline=False
                    )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in sell_item command: {e}")
            await interaction.followup.send("❌ An error occurred. Please try again.", ephemeral=True)
    
    @app_commands.command(name="remove", description="Remove an item from your buying or selling list")
    @app_commands.describe(
        item="The name of the item to remove",
        list_type="Whether to remove from buying or selling list"
    )
    @app_commands.choices(list_type=[
        app_commands.Choice(name="Buying", value="buying"),
        app_commands.Choice(name="Selling", value="selling")
    ])
    async def remove_item(self, interaction: discord.Interaction, item: str, list_type: str):
        """Remove item from user's listing"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validate inputs
            valid_item, clean_item = Validators.validate_item_name(item)
            if not valid_item:
                await interaction.followup.send(f"❌ {clean_item}", ephemeral=True)
                return
            
            # Get item ID
            item_id = self.item_cache.get_item_id(clean_item)
            if not item_id:
                await interaction.followup.send(f"❌ Item '{clean_item}' not found.", ephemeral=True)
                return
            
            # Remove listing
            success = await self.db_manager.remove_listing(
                interaction.user.id, item_id, list_type
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Item Removed",
                    description=f"**{clean_item}** removed from your {list_type} list.",
                    color=0xff9900
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(
                    f"❌ Item '{clean_item}' not found in your {list_type} list.",
                    ephemeral=True
                )
            
        except Exception as e:
            logger.error(f"Error in remove_item command: {e}")
            await interaction.followup.send("❌ An error occurred. Please try again.", ephemeral=True)
    
    @app_commands.command(name="mylistings", description="View your current buying and selling listings")
    async def my_listings(self, interaction: discord.Interaction):
        """Show user's current listings"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Get user's listings
            buying_listings = await self.db_manager.get_user_listings(interaction.user.id, "buying")
            selling_listings = await self.db_manager.get_user_listings(interaction.user.id, "selling")
            
            embed = discord.Embed(
                title=f"📋 {interaction.user.display_name}'s Listings",
                color=0x0099ff
            )
            
            # Add buying listings
            if buying_listings:
                buying_text = []
                for listing in buying_listings[:10]:  # Limit to 10 items
                    buying_text.append(f"• **{listing['item_name']}** - ${listing['price']:.2f}")
                
                embed.add_field(
                    name=f"🛒 Buying ({len(buying_listings)})",
                    value="\n".join(buying_text) if buying_text else "None",
                    inline=False
                )
                
                if len(buying_listings) > 10:
                    embed.add_field(
                        name="", 
                        value=f"... and {len(buying_listings) - 10} more",
                        inline=False
                    )
            else:
                embed.add_field(name="🛒 Buying", value="No items", inline=False)
            
            # Add selling listings
            if selling_listings:
                selling_text = []
                for listing in selling_listings[:10]:  # Limit to 10 items
                    selling_text.append(f"• **{listing['item_name']}** - ${listing['price']:.2f}")
                
                embed.add_field(
                    name=f"🏪 Selling ({len(selling_listings)})",
                    value="\n".join(selling_text) if selling_text else "None",
                    inline=False
                )
                
                if len(selling_listings) > 10:
                    embed.add_field(
                        name="", 
                        value=f"... and {len(selling_listings) - 10} more",
                        inline=False
                    )
            else:
                embed.add_field(name="🏪 Selling", value="No items", inline=False)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in my_listings command: {e}")
            await interaction.followup.send("❌ An error occurred. Please try again.", ephemeral=True)
    
    @app_commands.command(name="items", description="Search available items")
    @app_commands.describe(query="Search for items (optional)")
    async def search_items(self, interaction: discord.Interaction, query: Optional[str] = None):
        """Search for available items"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            if query:
                # Validate search query
                valid_query, clean_query = Validators.validate_search_query(query)
                if not valid_query:
                    await interaction.followup.send(f"❌ {clean_query}", ephemeral=True)
                    return
                
                # Search items
                items = self.item_cache.search_items(clean_query, 20)
                title = f"🔍 Search Results for '{clean_query}'"
            else:
                # Show all items (limited)
                items = self.item_cache.get_all_items()[:20]
                title = "📦 Available Items"
            
            if not items:
                await interaction.followup.send("❌ No items found.", ephemeral=True)
                return
            
            embed = discord.Embed(title=title, color=0x0099ff)
            
            # Group items in chunks
            chunks = [items[i:i+10] for i in range(0, len(items), 10)]
            
            for i, chunk in enumerate(chunks[:2]):  # Limit to 2 chunks (20 items)
                field_name = f"Items {i*10+1}-{i*10+len(chunk)}"
                field_value = "\n".join([f"• {item}" for item in chunk])
                embed.add_field(name=field_name, value=field_value, inline=True)
            
            if len(items) > 20:
                embed.set_footer(text=f"Showing first 20 of {len(items)} items. Use a more specific search.")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in search_items command: {e}")
            await interaction.followup.send("❌ An error occurred. Please try again.", ephemeral=True)
