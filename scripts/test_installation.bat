@echo off
setlocal enabledelayedexpansion

:: Set color codes
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "CYAN=[96m"
set "BLUE=[94m"
set "RESET=[0m"

echo %CYAN%🧪 Testing Installation%RESET%
echo %YELLOW%This will test all components to ensure they work correctly%RESET%
echo.

:: Initialize test results
set "TESTS_PASSED=0"
set "TESTS_TOTAL=0"

:: Test 1: Check if virtual environment exists
echo %CYAN%Test 1: Virtual Environment%RESET%
set /a TESTS_TOTAL+=1
if exist "venv" (
    if exist "venv\Scripts\activate.bat" (
        echo %GREEN%✅ Virtual environment exists and is valid%RESET%
        set /a TESTS_PASSED+=1
    ) else (
        echo %RED%❌ Virtual environment exists but activation script missing%RESET%
    )
) else (
    echo %RED%❌ Virtual environment not found%RESET%
)

:: Test 2: Activate virtual environment
echo %CYAN%Test 2: Virtual Environment Activation%RESET%
set /a TESTS_TOTAL+=1
call venv\Scripts\activate.bat
if %errorlevel% equ 0 (
    echo %GREEN%✅ Virtual environment activated successfully%RESET%
    set /a TESTS_PASSED+=1
) else (
    echo %RED%❌ Failed to activate virtual environment%RESET%
)

:: Test 3: Check Python version
echo %CYAN%Test 3: Python Version%RESET%
set /a TESTS_TOTAL+=1
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo %GREEN%✅ Python %PYTHON_VERSION% is working%RESET%
    set /a TESTS_PASSED+=1
) else (
    echo %RED%❌ Python not accessible%RESET%
)

:: Test 4: Check pip
echo %CYAN%Test 4: Pip Package Manager%RESET%
set /a TESTS_TOTAL+=1
pip --version >nul 2>&1
if %errorlevel% equ 0 (
    echo %GREEN%✅ Pip is working%RESET%
    set /a TESTS_PASSED+=1
) else (
    echo %RED%❌ Pip not accessible%RESET%
)

:: Test 5: Check required packages
echo %CYAN%Test 5: Required Python Packages%RESET%
set /a TESTS_TOTAL+=1
set "MISSING_PACKAGES="

python -c "import fastapi" 2>nul || set "MISSING_PACKAGES=!MISSING_PACKAGES! fastapi"
python -c "import uvicorn" 2>nul || set "MISSING_PACKAGES=!MISSING_PACKAGES! uvicorn"
python -c "import sqlalchemy" 2>nul || set "MISSING_PACKAGES=!MISSING_PACKAGES! sqlalchemy"
python -c "import alembic" 2>nul || set "MISSING_PACKAGES=!MISSING_PACKAGES! alembic"
python -c "import telegram" 2>nul || set "MISSING_PACKAGES=!MISSING_PACKAGES! python-telegram-bot"
python -c "import openai" 2>nul || set "MISSING_PACKAGES=!MISSING_PACKAGES! openai"
python -c "import dotenv" 2>nul || set "MISSING_PACKAGES=!MISSING_PACKAGES! python-dotenv"
python -c "import loguru" 2>nul || set "MISSING_PACKAGES=!MISSING_PACKAGES! loguru"
python -c "import rich" 2>nul || set "MISSING_PACKAGES=!MISSING_PACKAGES! rich"

if defined MISSING_PACKAGES (
    echo %RED%❌ Missing packages: %MISSING_PACKAGES%%RESET%
) else (
    echo %GREEN%✅ All required packages are installed%RESET%
    set /a TESTS_PASSED+=1
)

:: Test 6: Check database
echo %CYAN%Test 6: Database Setup%RESET%
set /a TESTS_TOTAL+=1
if exist "runtime\data\trade.sqlite3" (
    echo %GREEN%✅ Database file exists%RESET%
    set /a TESTS_PASSED+=1
) else (
    echo %RED%❌ Database file not found%RESET%
)

:: Test 7: Test database connection
echo %CYAN%Test 7: Database Connection%RESET%
set /a TESTS_TOTAL+=1
python -c "
import sqlite3
try:
    conn = sqlite3.connect('runtime/data/trade.sqlite3')
    cursor = conn.cursor()
    cursor.execute('SELECT sqlite_version()')
    version = cursor.fetchone()
    print(f'SQLite version: {version[0]}')
    conn.close()
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
" 2>nul

if %errorlevel% equ 0 (
    echo %GREEN%✅ Database connection test passed%RESET%
    set /a TESTS_PASSED+=1
) else (
    echo %RED%❌ Database connection test failed%RESET%
)

:: Test 8: Check environment files
echo %CYAN%Test 8: Environment Configuration%RESET%
set /a TESTS_TOTAL+=1
set "ENV_FILES_OK=0"
if exist ".env" set /a ENV_FILES_OK+=1
if exist ".env.example" set /a ENV_FILES_OK+=1
if exist ".env.local" set /a ENV_FILES_OK+=1

if %ENV_FILES_OK% gte 2 (
    echo %GREEN%✅ Environment files are present%RESET%
    set /a TESTS_PASSED+=1
) else (
    echo %RED%❌ Missing environment files%RESET%
)

:: Test 9: Check source code
echo %CYAN%Test 9: Source Code Structure%RESET%
set /a TESTS_TOTAL+=1
set "SOURCE_FILES_OK=0"
if exist "src\main.py" set /a SOURCE_FILES_OK+=1
if exist "src\models" set /a SOURCE_FILES_OK+=1
if exist "src\api" set /a SOURCE_FILES_OK+=1
if exist "src\telegram_bot" set /a SOURCE_FILES_OK+=1

if %SOURCE_FILES_OK% gte 3 (
    echo %GREEN%✅ Source code structure is correct%RESET%
    set /a TESTS_PASSED+=1
) else (
    echo %RED%❌ Source code structure incomplete%RESET%
)

:: Test 10: Check configuration files
echo %CYAN%Test 10: Configuration Files%RESET%
set /a TESTS_TOTAL+=1
set "CONFIG_FILES_OK=0"
if exist "alembic.ini" set /a CONFIG_FILES_OK+=1
if exist "requirements.txt" set /a CONFIG_FILES_OK+=1
if exist "config" set /a CONFIG_FILES_OK+=1

if %CONFIG_FILES_OK% gte 2 (
    echo %GREEN%✅ Configuration files are present%RESET%
    set /a TESTS_PASSED+=1
) else (
    echo %RED%❌ Missing configuration files%RESET%
)

:: Test 11: Test Python imports
echo %CYAN%Test 11: Python Module Imports%RESET%
set /a TESTS_TOTAL+=1
python -c "
import sys
import os

# Add src to path
sys.path.insert(0, 'src')

try:
    # Test basic imports
    from core.config import get_settings
    print('Core config import successful')

    # Test models
    from models.base import Base
    print('Models import successful')

    # Test API
    from api.routes import health
    print('API routes import successful')

    print('All module imports successful')
except ImportError as e:
    print(f'Import error: {e}')
    exit(1)
except Exception as e:
    print(f'Unexpected error: {e}')
    exit(1)
" 2>nul

if %errorlevel% equ 0 (
    echo %GREEN%✅ Python module imports successful%RESET%
    set /a TESTS_PASSED+=1
) else (
    echo %YELLOW%⚠️  Some module imports failed (this might be normal for incomplete setup)%RESET%
)

:: Test 12: Check runtime directories
echo %CYAN%Test 12: Runtime Directories%RESET%
set /a TESTS_TOTAL+=1
set "RUNTIME_DIRS_OK=0"
if exist "runtime" set /a RUNTIME_DIRS_OK+=1
if exist "runtime\data" set /a RUNTIME_DIRS_OK+=1
if exist "runtime\logs" set /a RUNTIME_DIRS_OK+=1

if %RUNTIME_DIRS_OK% equ 3 (
    echo %GREEN%✅ Runtime directories are properly set up%RESET%
    set /a TESTS_PASSED+=1
) else (
    echo %RED%❌ Runtime directories incomplete%RESET%
)

:: Test 13: Check scripts directory
echo %CYAN%Test 13: Scripts Directory%RESET%
set /a TESTS_TOTAL+=1
set "SCRIPTS_OK=0"
if exist "scripts" set /a SCRIPTS_OK+=1
if exist "scripts\complete_setup.bat" set /a SCRIPTS_OK+=1
if exist "scripts\install_dependencies.bat" set /a SCRIPTS_OK+=1

if %SCRIPTS_OK% equ 3 (
    echo %GREEN%✅ Scripts directory is properly set up%RESET%
    set /a TESTS_PASSED+=1
) else (
    echo %RED%❌ Scripts directory incomplete%RESET%
)

:: Test 14: Check documentation
echo %CYAN%Test 14: Documentation%RESET%
set /a TESTS_TOTAL+=1
if exist "docs" (
    if exist "README.md" (
        echo %GREEN%✅ Documentation is present%RESET%
        set /a TESTS_PASSED+=1
    ) else (
        echo %YELLOW%⚠️  Documentation directory exists but README.md missing%RESET%
    )
) else (
    echo %YELLOW%⚠️  Documentation directory not found%RESET%
)

:: Test 15: Final system check
echo %CYAN%Test 15: System Resources%RESET%
set /a TESTS_TOTAL+=1

:: Check disk space
for /f "tokens=3" %%a in ('dir C:\ /-c ^| find "bytes free"') do set FREE_SPACE=%%a
set /a FREE_SPACE_GB=%FREE_SPACE:~0,-1%/1024/1024/1024
if %FREE_SPACE_GB% gtr 1 (
    echo %GREEN%✅ Sufficient disk space available (%FREE_SPACE_GB% GB)%RESET%
    set /a TESTS_PASSED+=1
) else (
    echo %RED%❌ Insufficient disk space (%FREE_SPACE_GB% GB)%RESET%
)

:: Calculate and display results
echo.
echo %BLUE%══════════════════════════════════════════════════════════════%RESET%
echo %CYAN%📊 TEST RESULTS SUMMARY%RESET%
echo %BLUE%══════════════════════════════════════════════════════════════%RESET%
echo.

set /a SUCCESS_RATE=(%TESTS_PASSED% * 100) / %TESTS_TOTAL%

echo %CYAN%Tests Passed:%RESET% %GREEN%%TESTS_PASSED%/%TESTS_TOTAL%%RESET%
echo %CYAN%Success Rate:%RESET% %GREEN%%SUCCESS_RATE%%%RESET%
echo.

if %SUCCESS_RATE% gte 80 (
    echo %GREEN%🎉 Excellent! Your installation is working correctly.%RESET%
    echo %CYAN%You can now run the application.%RESET%
) else if %SUCCESS_RATE% gte 60 (
    echo %YELLOW%⚠️  Good! Most components are working, but some issues need attention.%RESET%
    echo %CYAN%Check the failed tests above and fix them before running the application.%RESET%
) else (
    echo %RED%❌ Poor! Many components are not working correctly.%RESET%
    echo %CYAN%Please run the complete setup again or fix the issues manually.%RESET%
)

echo.
echo %CYAN%Next steps:%RESET%
if %SUCCESS_RATE% gte 80 (
    echo %GREEN%✅ Run the application using 'Run Application' option%RESET%
) else (
    echo %YELLOW%⚠️  Fix the failed tests first%RESET%
    echo %YELLOW%⚠️  Run 'Complete Setup' again if needed%RESET%
)

echo %CYAN%For help, check the documentation in the docs/ folder%RESET%
echo.

exit /b 0
