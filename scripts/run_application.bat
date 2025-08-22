@echo off
setlocal enabledelayedexpansion

:: Set color codes
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "CYAN=[96m"
set "BLUE=[94m"
set "RESET=[0m"

echo %CYAN%🚀 Starting Telegram AI Trade Application%RESET%
echo.

:: Check if virtual environment exists
if not exist "venv" (
    echo %RED%❌ Virtual environment not found%RESET%
    echo %YELLOW%Please run 'Install Dependencies' first%RESET%
    pause
    exit /b 1
)

:: Check if .env.local exists
if not exist ".env.local" (
    echo %YELLOW%⚠️  .env.local file not found%RESET%
    echo %CYAN%Creating from template...%RESET%
    if exist ".env" (
        copy ".env" ".env.local" >nul
        echo %GREEN%✅ .env.local created from template%RESET%
        echo %YELLOW%⚠️  Please edit .env.local with your actual API keys before continuing%RESET%
        echo.
        set /p continue="Do you want to continue anyway? (y/N): "
        if /i "!continue!" neq "y" (
            echo %CYAN%Setup cancelled. Please configure your environment first.%RESET%
            pause
            exit /b 0
        )
    ) else (
        echo %RED%❌ No environment template found%RESET%
        echo %YELLOW%Please run 'Configure Environment' first%RESET%
        pause
        exit /b 1
    )
)

:: Check if main.py exists
if not exist "src\main.py" (
    echo %RED%❌ Main application file not found%RESET%
    echo %YELLOW%Please ensure the source code is properly installed%RESET%
    pause
    exit /b 1
)

:: Check if database exists
if not exist "runtime\data\trade.sqlite3" (
    echo %YELLOW%⚠️  Database not found, creating...%RESET%
    if not exist "runtime\data" mkdir "runtime\data"
    echo. > "runtime\data\trade.sqlite3"
    echo %GREEN%✅ Database created%RESET%
)

:: Create logs directory if it doesn't exist
if not exist "runtime\logs" mkdir "runtime\logs"

:: Activate virtual environment
echo %CYAN%Activating virtual environment...%RESET%
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo %RED%❌ Failed to activate virtual environment%RESET%
    pause
    exit /b 1
)
echo %GREEN%✅ Virtual environment activated%RESET%

:: Load environment variables
echo %CYAN%Loading environment configuration...%RESET%
if exist "scripts\load_env.bat" (
    call scripts\load_env.bat
    echo %GREEN%✅ Environment loaded%RESET%
) else (
    echo %YELLOW%⚠️  Environment loader not found, using default values%RESET%
)

:: Check if required packages are installed
echo %CYAN%Checking required packages...%RESET%
python -c "import fastapi, uvicorn, sqlalchemy" 2>nul
if %errorlevel% neq 0 (
    echo %RED%❌ Required packages not installed%RESET%
    echo %YELLOW%Please run 'Install Dependencies' first%RESET%
    pause
    exit /b 1
)
echo %GREEN%✅ Required packages are available%RESET%

:: Check if database is accessible
echo %CYAN%Testing database connection...%RESET%
python -c "
import sqlite3
try:
    conn = sqlite3.connect('runtime/data/trade.sqlite3')
    conn.close()
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
" 2>nul

if %errorlevel% neq 0 (
    echo %RED%❌ Database connection failed%RESET%
    echo %YELLOW%Please run 'Setup Database' first%RESET%
    pause
    exit /b 1
)
echo %GREEN%✅ Database connection successful%RESET%

:: Display startup information
echo.
echo %BLUE%══════════════════════════════════════════════════════════════%RESET%
echo %CYAN%📱 TELEGRAM AI TRADE APPLICATION%RESET%
echo %BLUE%══════════════════════════════════════════════════════════════%RESET%
echo.
echo %CYAN%Application will start with the following configuration:%RESET%
echo %YELLOW%• Host: 0.0.0.0 (accessible from any IP)%RESET%
echo %YELLOW%• Port: 8000%RESET%
echo %YELLOW%• Database: SQLite (runtime/data/trade.sqlite3)%RESET%
echo %YELLOW%• Logs: runtime/logs/app.log%RESET%
echo.
echo %CYAN%Access URLs:%RESET%
echo %GREEN%• Main API: http://localhost:8000%RESET%
echo %GREEN%• API Docs: http://localhost:8000/docs%RESET%
echo %GREEN%• Health Check: http://localhost:8000/health%RESET%
echo %GREEN%• Metrics: http://localhost:8000/metrics%RESET%
echo.

:: Check if port 8000 is available
echo %CYAN%Checking if port 8000 is available...%RESET%
netstat -an | findstr ":8000" | findstr "LISTENING" >nul
if %errorlevel% equ 0 (
    echo %RED%❌ Port 8000 is already in use%RESET%
    echo %YELLOW%Please stop any other applications using port 8000%RESET%
    echo %CYAN%Or change the port in your .env file%RESET%
    pause
    exit /b 1
)
echo %GREEN%✅ Port 8000 is available%RESET%

:: Start the application
echo.
echo %CYAN%🚀 Starting application...%RESET%
echo %YELLOW%Press Ctrl+C to stop the application%RESET%
echo.

:: Set environment variables for the application
set PYTHONPATH=%CD%\src;%PYTHONPATH%
set PYTHONUNBUFFERED=1

:: Start the application
python src\main.py

:: Check if application started successfully
if %errorlevel% equ 0 (
    echo.
    echo %GREEN%✅ Application stopped normally%RESET%
) else (
    echo.
    echo %RED%❌ Application stopped with error code %errorlevel%%RESET%
    echo %YELLOW%Check the logs above for error details%RESET%
)

echo.
echo %CYAN%Application has stopped.%RESET%
echo %YELLOW%Press any key to return to the main menu...%RESET%
pause >nul

exit /b 0
