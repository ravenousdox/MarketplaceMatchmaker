import discord
import logging
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)

class ThreadManager:
    """Manages Discord thread creation and management for matches"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def create_marketplace_thread(self, guild, buyer_id: int, seller_id: int, 
                                       item_name: str, buyer_price: float, 
                                       seller_price: float) -> Optional[int]:
        """
        Create a private thread for matched buyers and sellers
        """
        try:
            # Find a suitable channel for creating threads (first text channel)
            channel = None
            for ch in guild.text_channels:
                if ch.permissions_for(guild.me).create_private_threads:
                    channel = ch
                    break
            
            if not channel:
                logger.error("No suitable channel found for creating threads")
                return None
            
            # Get user objects
            buyer = guild.get_member(buyer_id)
            seller = guild.get_member(seller_id)
            
            if not buyer or not seller:
                logger.error(f"Could not find buyer ({buyer_id}) or seller ({seller_id}) in guild")
                return None
            
            # Create thread name
            thread_name = f"🤝 {item_name} - {buyer.display_name} & {seller.display_name}"
            if len(thread_name) > 100:  # Discord thread name limit
                thread_name = f"🤝 {item_name[:50]}... - Trade"
            
            # Create private thread
            thread = await channel.create_thread(
                name=thread_name,
                type=discord.ChannelType.private_thread,
                auto_archive_duration=Config.THREAD_AUTO_ARCHIVE_DURATION
            )
            
            # Add both users to the thread
            await thread.add_user(buyer)
            await thread.add_user(seller)
            
            # Create match details embed
            embed = discord.Embed(
                title="🎯 Marketplace Match Found!",
                description=f"A match has been found for **{item_name}**",
                color=0x00ff00
            )
            
            embed.add_field(
                name="🛒 Buyer",
                value=f"{buyer.mention}\nOffering: **${buyer_price:.2f}**",
                inline=True
            )
            
            embed.add_field(
                name="🏪 Seller", 
                value=f"{seller.mention}\nAsking: **${seller_price:.2f}**",
                inline=True
            )
            
            embed.add_field(
                name="💰 Price Difference",
                value=f"${abs(buyer_price - seller_price):.2f}",
                inline=True
            )
            
            embed.add_field(
                name="📋 Next Steps",
                value="• Discuss trade details\n• Agree on final price\n• Coordinate the exchange\n• Report any issues to admins",
                inline=False
            )
            
            embed.set_footer(text="This thread will auto-archive in 24 hours if inactive")
            
            # Send the match message
            await thread.send(
                content=f"🎉 {buyer.mention} {seller.mention} You've been matched!",
                embed=embed
            )
            
            logger.info(f"Created match thread {thread.id} for {buyer_id} and {seller_id}")
            return thread.id
            
        except discord.Forbidden:
            logger.error("Bot lacks permissions to create threads")
            return None
        except discord.HTTPException as e:
            logger.error(f"HTTP error creating thread: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating thread: {e}")
            return None
    
    async def send_match_notification(self, thread_id: int, message: str) -> bool:
        """Send a notification message to a match thread"""
        try:
            thread = self.bot.get_channel(thread_id)
            if not thread:
                logger.error(f"Thread {thread_id} not found")
                return False
            
            await thread.send(message)
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification to thread {thread_id}: {e}")
            return False
    
    async def archive_thread(self, thread_id: int) -> bool:
        """Archive a match thread"""
        try:
            thread = self.bot.get_channel(thread_id)
            if not thread:
                logger.error(f"Thread {thread_id} not found")
                return False
            
            await thread.edit(archived=True)
            logger.info(f"Archived thread {thread_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error archiving thread {thread_id}: {e}")
            return False
    
    async def add_user_to_thread(self, thread_id: int, user_id: int) -> bool:
        """Add a user to an existing thread"""
        try:
            thread = self.bot.get_channel(thread_id)
            if not thread:
                logger.error(f"Thread {thread_id} not found")
                return False
            
            user = thread.guild.get_member(user_id)
            if not user:
                logger.error(f"User {user_id} not found in guild")
                return False
            
            await thread.add_user(user)
            logger.info(f"Added user {user_id} to thread {thread_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding user {user_id} to thread {thread_id}: {e}")
            return False
