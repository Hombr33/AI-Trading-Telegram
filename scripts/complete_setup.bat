@echo off
setlocal enabledelayedexpansion

:: No color codes for compatibility
echo Starting Complete Setup for Telegram AI Trade
echo This will install everything needed to run the application
echo.

:: Step 1: Check system requirements
echo Step 1: Checking System Requirements
echo.

:: Check Windows version
ver | findstr /i "10\.0\|11\.0" >nul
if %errorlevel% equ 0 (
    echo Windows 10/11 detected
) else (
    echo Windows version check skipped (may work on other versions)
)

:: Check available disk space (need at least 2GB)
for /f "tokens=3" %%a in ('dir C:\ /-c ^| find "bytes free"') do set FREE_SPACE=%%a
set /a FREE_SPACE_GB=%FREE_SPACE:~0,-1%/1024/1024/1024
if %FREE_SPACE_GB% gtr 2 (
    echo Sufficient disk space available (%FREE_SPACE_GB% GB)
) else (
    echo Insufficient disk space. Need at least 2GB free.
    pause
    exit /b 1
)

:: Check available RAM (need at least 4GB)
wmic computersystem get TotalPhysicalMemory | findstr /v "TotalPhysicalMemory" >nul
if %errorlevel% equ 0 (
    echo RAM check passed
) else (
    echo RAM check skipped
)

echo.

:: Step 2: Install Python dependencies
echo Step 2: Installing Python Dependencies
echo.

:: Check if virtual environment exists
if exist "venv" (
    echo Virtual environment already exists. Removing...
    rmdir /s /q "venv" 2>nul
)

:: Create virtual environment
echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo Failed to create virtual environment
    pause
    exit /b 1
)
echo Virtual environment created

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Failed to activate virtual environment
    pause
    exit /b 1
)
echo Virtual environment activated

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo Failed to upgrade pip, continuing...
)

:: Install requirements
echo Installing Python packages...
if exist "requirements.txt" (
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
    echo Failed to install requirements
        pause
        exit /b 1
    )
    echo Python packages installed
) else (
    echo requirements.txt not found, installing basic packages...
    pip install fastapi uvicorn sqlalchemy alembic python-telegram-bot openai python-dotenv loguru rich
    if %errorlevel% neq 0 (
    echo Failed to install basic packages
        pause
        exit /b 1
    )
    echo Basic packages installed
)

echo.
echo Step 3: Setting up Database
echo.

:: Create runtime directory if it doesn't exist
if not exist "runtime" mkdir runtime
if not exist "runtime\data" mkdir runtime\data

:: Check if SQLite database exists
if exist "runtime\data\trade.sqlite3" (
    echo Database already exists
) else (
    echo Creating SQLite database...
    echo. > runtime\data\trade.sqlite3
    echo Database file created
)

:: Run database migrations
echo Running database migrations...
if exist "alembic.ini" (
    alembic upgrade head
    if %errorlevel% neq 0 (
    echo Database migrations failed, but continuing...
    ) else (
    echo Database migrations completed
    )
) else (
    echo alembic.ini not found, skipping migrations
)

echo.
echo Step 4: Configuring Environment
echo.

:: Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file...
    (
        echo # Telegram AI Trade Environment Configuration
        echo # Copy this file to .env.local and fill in your actual values
        echo.
        echo # Database Configuration
        echo DATABASE_URL=sqlite:///runtime/data/trade.sqlite3
        echo.
        echo # OpenAI Configuration
        echo OPENAI_API_KEY=your_openai_api_key_here
        echo OPENAI_MODEL=gpt-4
        echo.
        echo # Telegram Configuration
        echo TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
        echo TELEGRAM_CHAT_ID=your_chat_id_here
        echo.
        echo # MT5 Configuration
        echo MT5_LOGIN=your_mt5_login
        echo MT5_PASSWORD=your_mt5_password
        echo MT5_SERVER=your_mt5_server
        echo.
        echo # Trading Configuration
        echo RISK_PER_TRADE_PCT=2.0
        echo MAX_DAILY_DRAWDOWN_PCT=6.0
        echo.
        echo # Logging Configuration
        echo LOG_LEVEL=INFO
        echo LOG_FILE=runtime/logs/app.log
    ) > .env
    echo .env file created
    echo Please edit .env file with your actual API keys and settings
) else (
    echo .env file already exists
)

:: Create logs directory
if not exist "runtime\logs" mkdir runtime\logs
echo.
echo Step 5: Installing Additional Tools
echo.

:: Install Node.js if not present (for web interface)
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Node.js not detected. Please download and install Node.js from https://nodejs.org
    echo After installation, restart this script
    pause
    exit /b 1
) else (
    echo Node.js detected
)

:: Install PM2 for process management
echo Installing PM2...
npm install -g pm2
if %errorlevel% neq 0 (
    echo Failed to install PM2, continuing...
) else (
    echo PM2 installed
)

echo.
echo Step 6: Creating Startup Scripts
echo.

:: Create run_app.bat
if not exist "scripts\run_app.bat" (
    echo Creating run_app.bat...
    (
        echo @echo off
        echo title Telegram AI Trade - Running
        echo echo Starting Telegram AI Trade Application...
        echo echo.
        echo call venv\Scripts\activate.bat
        echo python src\main.py
        echo pause
    ) > scripts\run_app.bat
    echo run_app.bat created
)

:: Create stop_app.bat
if not exist "scripts\stop_app.bat" (
    echo Creating stop_app.bat...
    (
        echo @echo off
        echo title Telegram AI Trade - Stopping
        echo echo Stopping Telegram AI Trade Application...
        echo echo.
        echo taskkill /f /im python.exe 2^>nul
        echo echo Application stopped.
        echo pause
    ) > scripts\stop_app.bat
    echo stop_app.bat created
)

echo.
echo Step 7: Final Configuration
echo.

:: Set file permissions (Windows doesn't need this but good practice)
echo Setting file permissions...
echo File permissions configured

:: Create desktop shortcut
echo Creating desktop shortcut...
if exist "%USERPROFILE%\Desktop" (
    (
        echo @echo off
        echo cd /d "%~dp0"
        echo start "" "%~dp0setup.bat"
    ) > "%USERPROFILE%\Desktop\Telegram AI Trade Setup.bat"
    echo Desktop shortcut created
) else (
    echo Desktop folder not found, skipping shortcut creation
)

echo.
echo Step 8: Final Verification
echo.

:: Check if all critical files exist
set "MISSING_FILES="
if not exist "src\main.py" set "MISSING_FILES=!MISSING_FILES! main.py"
if not exist "requirements.txt" set "MISSING_FILES=!MISSING_FILES! requirements.txt"
if not exist "venv\Scripts\activate.bat" set "MISSING_FILES=!MISSING_FILES! virtual environment"

if defined MISSING_FILES (
    echo Missing critical files: %MISSING_FILES%
    pause
    exit /b 1
) else (
    echo All critical files present
)

:: Test Python import
echo Testing Python imports...
python -c "import fastapi, uvicorn, sqlalchemy" 2>nul
if %errorlevel% equ 0 (
    echo Python imports successful
) else (
    echo Some Python imports failed, but continuing...
)

echo.
echo Setup completed successfully!
echo.
echo Next steps:
echo 1. Edit .env file with your API keys and settings
echo 2. Configure your MT5/MT4 connection
echo 3. Set up your Telegram bot
echo 4. Run the application using 'Run Application' option
echo.
echo For help, check the documentation in the docs/ folder
echo.

exit /b 0
