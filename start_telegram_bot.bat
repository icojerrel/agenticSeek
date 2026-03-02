@echo off
REM Start AgenticSeek Telegram Bot
REM Usage: start_telegram_bot.bat

echo ============================================================
echo   AgenticSeek Telegram Bot - Starting...
echo ============================================================
echo.

REM Check if .env exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Copy .env.example to .env and configure your bot token.
    pause
    exit /b 1
)

REM Activate virtual environment if exists
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Install flask if not installed
pip show flask >nul 2>&1 || pip install flask requests python-dotenv

echo.
echo Starting Telegram bot in polling mode...
echo Press Ctrl+C to stop
echo.

REM Start the bot
python sources\telegram_bot.py

pause
