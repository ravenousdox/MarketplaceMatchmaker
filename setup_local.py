#!/usr/bin/env python3
"""
Setup script for Discord Marketplace Bot - Local Development
This script helps set up the bot for local development on your computer.
"""

import os
import sys
import subprocess
import shutil

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]} is compatible")

def create_virtual_environment():
    """Create virtual environment if it doesn't exist"""
    if not os.path.exists("venv"):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✓ Virtual environment created")
    else:
        print("✓ Virtual environment already exists")

def get_pip_command():
    """Get the correct pip command for the platform"""
    if os.name == 'nt':  # Windows
        return os.path.join("venv", "Scripts", "pip")
    else:  # macOS/Linux
        return os.path.join("venv", "bin", "pip")

def install_dependencies():
    """Install required packages"""
    pip_cmd = get_pip_command()
    
    print("Installing dependencies...")
    packages = [
        "discord.py==2.5.2",
        "aiosqlite==0.21.0",
        "python-dotenv"
    ]
    
    for package in packages:
        subprocess.run([pip_cmd, "install", package], check=True)
    
    print("✓ All dependencies installed")

def create_env_file():
    """Create .env file from template"""
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            shutil.copy(".env.example", ".env")
            print("✓ Created .env file from template")
            print("⚠️  Please edit .env file and add your Discord bot token")
        else:
            with open(".env", "w") as f:
                f.write("DISCORD_TOKEN=your_discord_bot_token_here\n")
                f.write("DATABASE_PATH=marketplace.db\n")
                f.write("LOG_LEVEL=INFO\n")
                f.write("LOG_FILE=bot.log\n")
            print("✓ Created .env file")
            print("⚠️  Please edit .env file and add your Discord bot token")
    else:
        print("✓ .env file already exists")

def create_gitignore():
    """Create .gitignore file"""
    gitignore_content = """# Environment variables
.env

# Virtual environment
venv/
env/

# Database files
*.db
*.sqlite
*.sqlite3

# Log files
*.log

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# VS Code
.vscode/settings.json

# OS files
.DS_Store
Thumbs.db
"""
    
    if not os.path.exists(".gitignore"):
        with open(".gitignore", "w") as f:
            f.write(gitignore_content)
        print("✓ Created .gitignore file")
    else:
        print("✓ .gitignore file already exists")

def main():
    """Main setup function"""
    print("Discord Marketplace Bot - Local Setup")
    print("=" * 40)
    
    try:
        check_python_version()
        create_virtual_environment()
        install_dependencies()
        create_env_file()
        create_gitignore()
        
        print("\n" + "=" * 40)
        print("Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit the .env file and add your Discord bot token")
        print("2. Open the project in VS Code")
        print("3. Select the Python interpreter from the venv folder")
        print("4. Press F5 to run the bot")
        print("\nFor detailed instructions, see README.md")
        
    except subprocess.CalledProcessError as e:
        print(f"Error during setup: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()