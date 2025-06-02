import os

class Config:
    """Configuration settings for the marketplace bot"""
    
    # Database configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'marketplace.db')
    
    # Bot configuration
    COMMAND_PREFIX = '!'
    
    # Thread configuration
    THREAD_AUTO_ARCHIVE_DURATION = 1440  # 24 hours in minutes
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'bot.log')
    
    # Cache configuration
    CACHE_REFRESH_INTERVAL = 300  # 5 minutes
    
    # Marketplace configuration
    MAX_LISTINGS_PER_USER = 50
    MAX_ITEM_NAME_LENGTH = 100
    MAX_PRICE = 999999999
    MIN_PRICE = 0.01
