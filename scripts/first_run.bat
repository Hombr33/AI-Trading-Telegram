@echo off
echo AI Trading Bot - First Run Setup
echo ================================

REM Check if .env file exists
if not exist .env (
    echo Creating .env file...
    echo BRIDGE_TOKEN=please-change-me> .env
    echo TELEGRAM_BOT_TOKEN=>> .env
    echo TELEGRAM_CHAT_ID=>> .env
    echo OPENAI_API_KEY=>> .env
    echo DATABASE_URL=sqlite:///./runtime/data/trade.sqlite3>> .env
    echo.
    echo IMPORTANT: Please edit .env file and set your BRIDGE_TOKEN to a strong random string!
    echo.
    pause
) else (
    echo .env file already exists.
)

echo.
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting AI Trading Bot...
set PYTHONUTF8=1
python -m src.app
pause
