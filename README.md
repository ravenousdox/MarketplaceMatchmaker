# Discord Marketplace Bot

A persistent Discord bot for managing a digital marketplace with real-time buyer-seller matching and automated thread creation.

## Features

- **Real-time Matching**: Automatically matches buyers and sellers when compatible listings are found
- **Private Threads**: Creates private Discord threads for matched users to negotiate trades
- **Admin Management**: Administrator commands to manage the global item catalog
- **SQLite Database**: Persistent storage with normalized tables and proper indexing
- **O(1) Validation**: Fast item validation using in-memory cache
- **Slash Commands**: Modern Discord slash command interface

## Local Setup Instructions

### Prerequisites

- Python 3.8 or higher
- VS Code (recommended)
- Discord Bot Token

### Step 1: Create Discord Bot

1. Go to https://discord.com/developers/applications
2. Click "New Application" and give it a name
3. Go to the "Bot" section in the left sidebar
4. Click "Add Bot"
5. Under the "Token" section, click "Copy" to get your bot token
6. Save this token - you'll need it later

### Step 2: Set Up VS Code Environment

1. **Download/Clone the project files** to your computer
2. **Open VS Code** and open the project folder
3. **Create a virtual environment**:
   - Open VS Code terminal (Terminal > New Terminal)
   - Run: `python -m venv venv`
   - Activate it:
     - Windows: `venv\Scripts\activate`
     - Mac/Linux: `source venv/bin/activate`

4. **Install dependencies**:
   ```bash
   pip install -r setup_requirements.txt
   ```

### Step 3: Configure Environment

1. **Create a `.env` file** in the project root:
   ```
   DISCORD_TOKEN=your_bot_token_here
   DATABASE_PATH=marketplace.db
   LOG_LEVEL=INFO
   ```

2. **Update main.py** to load environment variables:
   - Add at the top: `from dotenv import load_dotenv`
   - Add after imports: `load_dotenv()`
   - Install python-dotenv: `pip install python-dotenv`

### Step 4: VS Code Configuration

1. **Select Python Interpreter**:
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type "Python: Select Interpreter"
   - Choose the interpreter from your `venv` folder

2. **Create launch configuration** (`.vscode/launch.json`):
   ```json
   {
       "version": "0.2.0",
       "configurations": [
           {
               "name": "Discord Bot",
               "type": "python",
               "request": "launch",
               "program": "main.py",
               "console": "integratedTerminal",
               "cwd": "${workspaceFolder}"
           }
       ]
   }
   ```

### Step 5: Run the Bot

1. **Start the bot**:
   - Press `F5` in VS Code, or
   - Run in terminal: `python main.py`

2. **Verify connection**:
   - Check console for "Bot has connected to Discord!"
   - Look for "Commands synced successfully"

### Step 6: Invite Bot to Server

1. Go to Discord Developer Portal > Your App > OAuth2 > URL Generator
2. Select scopes: `bot`, `applications.commands`
3. Select bot permissions:
   - Send Messages
   - Create Private Threads
   - Manage Threads
   - Use Slash Commands
4. Copy the generated URL and open it to invite the bot

## Available Commands

### User Commands
- `/buy [item] [price]` - Add item to buying list
- `/sell [item] [price]` - Add item to selling list
- `/remove [item] [buying/selling]` - Remove item from list
- `/mylistings` - View your current listings
- `/items [query]` - Search available items

### Admin Commands (Requires Administrator Permission)
- `/admin_add_item [name] [category] [description]` - Add new item to catalog
- `/admin_remove_item [name]` - Remove item from catalog
- `/admin_stats` - View marketplace statistics
- `/admin_reload_cache` - Reload item cache
- `/admin_list_items [category]` - List all items with details

## Database Structure

The bot uses SQLite with the following tables:
- `users` - Discord user information
- `game_items` - Global item catalog (admin-managed)
- `listings` - User buy/sell listings
- `matches` - Successful match records
- `admin_activity_log` - Admin action logging

## Troubleshooting

1. **Bot won't start**: Check your Discord token in the `.env` file
2. **Commands not showing**: Wait a few minutes for Discord to sync commands
3. **No matches found**: Ensure items exist in the admin catalog first
4. **Thread creation fails**: Check bot permissions in your Discord server

## File Structure

```
discord-marketplace-bot/
├── commands/
│   ├── admin.py          # Admin commands
│   └── marketplace.py    # User marketplace commands
├── database/
│   ├── operations.py     # Database operations
│   └── schema.py         # Database schema and initialization
├── services/
│   ├── matching.py       # Real-time matching logic
│   └── thread_manager.py # Discord thread management
├── utils/
│   ├── cache.py          # In-memory item cache
│   └── validators.py     # Input validation utilities
├── config.py             # Configuration settings
├── main.py               # Main bot entry point
├── setup_requirements.txt # Python dependencies
└── .env                  # Environment variables (create this)
```

## Running 24/7

For persistent operation, consider using:
- **PM2** (Node.js process manager that works with Python)
- **systemd** service (Linux)
- **Windows Service** (Windows)
- **Cloud hosting** (Heroku, VPS, etc.)

## Support

The bot includes comprehensive error handling and logging. Check `bot.log` for detailed information about any issues.