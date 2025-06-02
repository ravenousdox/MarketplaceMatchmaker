@echo off
echo Discord Marketplace Bot - Windows Setup
echo ========================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

REM Activate virtual environment and install packages
echo Installing dependencies...
call venv\Scripts\activate.bat
pip install discord.py==2.5.2 aiosqlite==0.21.0 python-dotenv

REM Create .env file if it doesn't exist
if not exist ".env" (
    copy .env.example .env
    echo .env file created from template.
    echo Please edit .env file and add your Discord bot token.
) else (
    echo .env file already exists.
)

echo.
echo Setup completed successfully!
echo.
echo Next steps:
echo 1. Edit the .env file and add your Discord bot token
echo 2. Open the project in VS Code
echo 3. Select Python interpreter from venv\Scripts\python.exe
echo 4. Press F5 to run the bot
echo.
pause