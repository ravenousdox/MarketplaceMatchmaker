import aiosqlite
import logging

logger = logging.getLogger(__name__)

async def initialize_database(db_path: str):
    """
    Initialize the SQLite database with normalized tables and proper indexing
    """
    logger.info(f"Initializing database at {db_path}")
    
    async with aiosqlite.connect(db_path) as db:
        # Enable foreign keys
        await db.execute("PRAGMA foreign_keys = ON")
        
        # Users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                discord_username TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Game items table (admin-managed)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS game_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL UNIQUE,
                category TEXT,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users (user_id)
            )
        """)
        
        # Listings table (buying/selling)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                listing_type TEXT NOT NULL CHECK (listing_type IN ('buying', 'selling')),
                price REAL NOT NULL CHECK (price > 0),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
                FOREIGN KEY (item_id) REFERENCES game_items (item_id) ON DELETE CASCADE,
                UNIQUE(user_id, item_id, listing_type)
            )
        """)
        
        # Admin activity log
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admin_activity_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_user_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                target_item_id INTEGER,
                target_user_id INTEGER,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_user_id) REFERENCES users (user_id),
                FOREIGN KEY (target_item_id) REFERENCES game_items (item_id),
                FOREIGN KEY (target_user_id) REFERENCES users (user_id)
            )
        """)
        
        # Matches table (track successful matches)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                buyer_user_id INTEGER NOT NULL,
                seller_user_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                buyer_price REAL NOT NULL,
                seller_price REAL NOT NULL,
                thread_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (buyer_user_id) REFERENCES users (user_id),
                FOREIGN KEY (seller_user_id) REFERENCES users (user_id),
                FOREIGN KEY (item_id) REFERENCES game_items (item_id)
            )
        """)
        
        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_listings_user_type ON listings (user_id, listing_type)",
            "CREATE INDEX IF NOT EXISTS idx_listings_item_type ON listings (item_id, listing_type)",
            "CREATE INDEX IF NOT EXISTS idx_listings_type_price ON listings (listing_type, price)",
            "CREATE INDEX IF NOT EXISTS idx_game_items_name ON game_items (item_name)",
            "CREATE INDEX IF NOT EXISTS idx_admin_log_timestamp ON admin_activity_log (timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_matches_users ON matches (buyer_user_id, seller_user_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_last_activity ON users (last_activity)"
        ]
        
        for index in indexes:
            await db.execute(index)
        
        await db.commit()
        logger.info("Database initialized successfully")

async def get_database_stats(db_path: str) -> dict:
    """Get database statistics for monitoring"""
    async with aiosqlite.connect(db_path) as db:
        stats = {}
        
        tables = ['users', 'game_items', 'listings', 'admin_activity_log', 'matches']
        for table in tables:
            cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
            count = await cursor.fetchone()
            stats[table] = count[0] if count else 0
        
        return stats
