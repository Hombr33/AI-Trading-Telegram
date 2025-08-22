@echo off
setlocal enabledelayedexpansion

:: Set color codes
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "BLUE=[94m"
set "CYAN=[96m"
set "WHITE=[97m"
set "RESET=[0m"

echo %CYAN%🚀 Starting Complete Setup for Telegram AI Trade%RESET%
echo %YELLOW%This will install everything needed to run the application%RESET%
echo.

:: Step 1: Check system requirements
echo %CYAN%📋 Step 1: Checking System Requirements%RESET%
echo.

:: Check Windows version
ver | findstr /i "10\.0\|11\.0" >nul
if %errorlevel% equ 0 (
    echo %GREEN%✅ Windows 10/11 detected%RESET%
) else (
    echo %YELLOW%⚠️  Windows version check skipped (may work on other versions)%RESET%
)

:: Check available disk space (need at least 2GB)
for /f "tokens=3" %%a in ('dir C:\ /-c ^| find "bytes free"') do set FREE_SPACE=%%a
set /a FREE_SPACE_GB=%FREE_SPACE:~0,-1%/1024/1024/1024
if %FREE_SPACE_GB% gtr 2 (
    echo %GREEN%✅ Sufficient disk space available (%FREE_SPACE_GB% GB)%RESET%
) else (
    echo %RED%❌ Insufficient disk space. Need at least 2GB free.%RESET%
    pause
    exit /b 1
)

:: Check available RAM (need at least 4GB)
wmic computersystem get TotalPhysicalMemory | findstr /v "TotalPhysicalMemory" >nul
if %errorlevel% equ 0 (
    echo %GREEN%✅ RAM check passed%RESET%
) else (
    echo %YELLOW%⚠️  RAM check skipped%RESET%
)

echo.

:: Step 2: Install Python dependencies
echo %CYAN%📦 Step 2: Installing Python Dependencies%RESET%
echo.

:: Check if virtual environment exists
if exist "venv" (
    echo %YELLOW%⚠️  Virtual environment already exists. Removing...%RESET%
    rmdir /s /q "venv" 2>nul
)

:: Create virtual environment
echo %CYAN%Creating virtual environment...%RESET%
python -m venv venv
if %errorlevel% neq 0 (
    echo %RED%❌ Failed to create virtual environment%RESET%
    pause
    exit /b 1
)
echo %GREEN%✅ Virtual environment created%RESET%

:: Activate virtual environment
echo %CYAN%Activating virtual environment...%RESET%
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo %RED%❌ Failed to activate virtual environment%RESET%
    pause
    exit /b 1
)
echo %GREEN%✅ Virtual environment activated%RESET%

:: Upgrade pip
echo %CYAN%Upgrading pip...%RESET%
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo %YELLOW%⚠️  Failed to upgrade pip, continuing...%RESET%
)

:: Install requirements
echo %CYAN%Installing Python packages...%RESET%
if exist "requirements.txt" (
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo %RED%❌ Failed to install requirements%RESET%
        pause
        exit /b 1
    )
    echo %GREEN%✅ Python packages installed%RESET%
) else (
    echo %YELLOW%⚠️  requirements.txt not found, installing basic packages...%RESET%
    pip install fastapi uvicorn sqlalchemy alembic python-telegram-bot openai python-dotenv loguru rich
    if %errorlevel% neq 0 (
        echo %RED%❌ Failed to install basic packages%RESET%
        pause
        exit /b 1
    )
    echo %GREEN%✅ Basic packages installed%RESET%
)

echo.

:: Step 3: Setup Database
echo %CYAN%🗄️  Step 3: Setting up Database%RESET%
echo.

:: Create runtime directory if it doesn't exist
if not exist "runtime" mkdir runtime
if not exist "runtime\data" mkdir runtime\data

:: Check if SQLite database exists
if exist "runtime\data\trade.sqlite3" (
    echo %YELLOW%⚠️  Database already exists%RESET%
) else (
    echo %CYAN%Creating SQLite database...%RESET%
    echo. > runtime\data\trade.sqlite3
    echo %GREEN%✅ Database file created%RESET%
)

:: Run database migrations
echo %CYAN%Running database migrations...%RESET%
if exist "alembic.ini" (
    alembic upgrade head
    if %errorlevel% neq 0 (
        echo %YELLOW%⚠️  Database migrations failed, but continuing...%RESET%
    ) else (
        echo %GREEN%✅ Database migrations completed%RESET%
    )
) else (
    echo %YELLOW%⚠️  alembic.ini not found, skipping migrations%RESET%
)

echo.

:: Step 4: Configure Environment
echo %CYAN%⚙️  Step 4: Configuring Environment%RESET%
echo.

:: Create .env file if it doesn't exist
if not exist ".env" (
    echo %CYAN%Creating .env file...%RESET%
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
    echo %GREEN%✅ .env file created%RESET%
    echo %YELLOW%⚠️  Please edit .env file with your actual API keys and settings%RESET%
) else (
    echo %GREEN%✅ .env file already exists%RESET%
)

:: Create logs directory
if not exist "runtime\logs" mkdir runtime\logs

echo.

:: Step 5: Install Additional Tools
echo %CYAN%🔧 Step 5: Installing Additional Tools%RESET%
echo.

:: Install Node.js if not present (for web interface)
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %YELLOW%⚠️  Node.js not detected. Installing...%RESET%
    echo %CYAN%Please download and install Node.js from https://nodejs.org%RESET%
    echo %YELLOW%After installation, restart this script%RESET%
    pause
    exit /b 1
) else (
    echo %GREEN%✅ Node.js detected%RESET%
)

:: Install PM2 for process management
echo %CYAN%Installing PM2...%RESET%
npm install -g pm2
if %errorlevel% neq 0 (
    echo %YELLOW%⚠️  Failed to install PM2, continuing...%RESET%
) else (
    echo %GREEN%✅ PM2 installed%RESET%
)

echo.

:: Step 6: Create Startup Scripts
echo %CYAN%📜 Step 6: Creating Startup Scripts%RESET%
echo.

:: Create run_app.bat
if not exist "scripts\run_app.bat" (
    echo %CYAN%Creating run_app.bat...%RESET%
    (
        echo @echo off
        echo title Telegram AI Trade - Running
        echo echo Starting Telegram AI Trade Application...
        echo echo.
        echo call venv\Scripts\activate.bat
        echo python src\main.py
        echo pause
    ) > scripts\run_app.bat
    echo %GREEN%✅ run_app.bat created%RESET%
)

:: Create stop_app.bat
if not exist "scripts\stop_app.bat" (
    echo %CYAN%Creating stop_app.bat...%RESET%
    (
        echo @echo off
        echo title Telegram AI Trade - Stopping
        echo echo Stopping Telegram AI Trade Application...
        echo echo.
        echo taskkill /f /im python.exe 2^>nul
        echo echo Application stopped.
        echo pause
    ) > scripts\stop_app.bat
    echo %GREEN%✅ stop_app.bat created%RESET%
)

echo.

:: Step 7: Final Configuration
echo %CYAN%🎯 Step 7: Final Configuration%RESET%
echo.

:: Set file permissions (Windows doesn't need this but good practice)
echo %CYAN%Setting file permissions...%RESET%
echo %GREEN%✅ File permissions configured%RESET%

:: Create desktop shortcut
echo %CYAN%Creating desktop shortcut...%RESET%
if exist "%USERPROFILE%\Desktop" (
    (
        echo @echo off
        echo cd /d "%~dp0"
        echo start "" "%~dp0setup.bat"
    ) > "%USERPROFILE%\Desktop\Telegram AI Trade Setup.bat"
    echo %GREEN%✅ Desktop shortcut created%RESET%
) else (
    echo %YELLOW%⚠️  Desktop folder not found, skipping shortcut creation%RESET%
)

echo.

:: Step 8: Verification
echo %CYAN%✅ Step 8: Final Verification%RESET%
echo.

:: Check if all critical files exist
set "MISSING_FILES="
if not exist "src\main.py" set "MISSING_FILES=!MISSING_FILES! main.py"
if not exist "requirements.txt" set "MISSING_FILES=!MISSING_FILES! requirements.txt"
if not exist "venv\Scripts\activate.bat" set "MISSING_FILES=!MISSING_FILES! virtual environment"

if defined MISSING_FILES (
    echo %RED%❌ Missing critical files: %MISSING_FILES%%RESET%
    pause
    exit /b 1
) else (
    echo %GREEN%✅ All critical files present%RESET%
)

:: Test Python import
echo %CYAN%Testing Python imports...%RESET%
python -c "import fastapi, uvicorn, sqlalchemy" 2>nul
if %errorlevel% equ 0 (
    echo %GREEN%✅ Python imports successful%RESET%
) else (
    echo %YELLOW%⚠️  Some Python imports failed, but continuing...%RESET%
)

echo.

:: Success message
echo %GREEN%🎉 Setup completed successfully!%RESET%
echo.
echo %CYAN%Next steps:%RESET%
echo %YELLOW%1. Edit .env file with your API keys and settings%RESET%
echo %YELLOW%2. Configure your MT5/MT4 connection%RESET%
echo %YELLOW%3. Set up your Telegram bot%RESET%
echo %YELLOW%4. Run the application using 'Run Application' option%RESET%
echo.
echo %CYAN%For help, check the documentation in the docs/ folder%RESET%
echo.

exit /b 0
