import os
import asyncio
import logging
import aiosqlite
import discord
from discord.ext import commands

from database.schema import initialize_database
from database.operations import DatabaseManager
from commands.marketplace import MarketplaceCommands
from commands.admin import AdminCommands
from services.matching import MatchingService
from services.thread_manager import ThreadManager
from utils.cache import ItemCache
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class MarketplaceBot(commands.Bot):
    """
    Discord marketplace bot with real-time matching and thread creation
    """
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = False  # Not needed for slash commands
        intents.guilds = True
        intents.members = False  # Not needed for marketplace functionality
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        self.db_manager = None
        self.item_cache = None
        self.matching_service = None
        self.thread_manager = None
        
    async def setup_hook(self):
        """Initialize bot components"""
        logger.info("Setting up bot components...")
        
        try:
            # Initialize database
            await initialize_database(Config.DATABASE_PATH)
            self.db_manager = DatabaseManager(Config.DATABASE_PATH)
            
            # Initialize item cache
            self.item_cache = ItemCache()
            await self.item_cache.load_items(self.db_manager)
            
            # Initialize services
            self.thread_manager = ThreadManager(self)
            self.matching_service = MatchingService(
                self.db_manager, 
                self.item_cache, 
                self.thread_manager
            )
            
            # Add command cogs
            await self.add_cog(MarketplaceCommands(
                self.db_manager, 
                self.item_cache, 
                self.matching_service
            ))
            await self.add_cog(AdminCommands(
                self.db_manager, 
                self.item_cache
            ))
            
            # Sync commands
            await self.tree.sync()
            logger.info("Commands synced successfully")
            
        except Exception as e:
            logger.error(f"Error during setup: {e}")
            raise
    
    async def on_ready(self):
        """Bot ready event"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="the marketplace"
            )
        )
    
    async def on_error(self, event, *args, **kwargs):
        """Global error handler"""
        logger.error(f"Error in event {event}: {args}, {kwargs}")
    
    async def close(self):
        """Cleanup on bot shutdown"""
        if self.db_manager:
            await self.db_manager.close()
        await super().close()

async def main():
    """Main bot entry point"""
    bot = MarketplaceBot()
    
    try:
        # Get token from environment
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            raise ValueError("DISCORD_TOKEN environment variable not set")
        
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
