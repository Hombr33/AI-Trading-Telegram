@echo off
setlocal enabledelayedexpansion

:: Set color codes
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "CYAN=[96m"
set "RESET=[0m"

echo %CYAN%📦 Installing Python Dependencies%RESET%
echo.

:: Check if virtual environment exists
if not exist "venv" (
    echo %CYAN%Creating virtual environment...%RESET%
    python -m venv venv
    if %errorlevel% neq 0 (
        echo %RED%❌ Failed to create virtual environment%RESET%
        pause
        exit /b 1
    )
    echo %GREEN%✅ Virtual environment created%RESET%
) else (
    echo %GREEN%✅ Virtual environment already exists%RESET%
)

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
) else (
    echo %GREEN%✅ Pip upgraded%RESET%
)

:: Install wheel and setuptools first
echo %CYAN%Installing build tools...%RESET%
pip install wheel setuptools
if %errorlevel% neq 0 (
    echo %YELLOW%⚠️  Failed to install build tools, continuing...%RESET%
) else (
    echo %GREEN%✅ Build tools installed%RESET%
)

:: Install requirements
echo %CYAN%Installing Python packages from requirements.txt...%RESET%
if exist "requirements.txt" (
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo %RED%❌ Failed to install requirements%RESET%
        echo %YELLOW%Trying to install packages individually...%RESET%
        
        :: Install core packages individually
        pip install fastapi
        pip install uvicorn[standard]
        pip install sqlalchemy
        pip install alembic
        pip install python-telegram-bot
        pip install openai
        pip install python-dotenv
        pip install loguru
        pip install rich
        pip install pydantic
        pip install asyncio-mqtt
        pip install websockets
        
        echo %GREEN%✅ Individual package installation completed%RESET%
    ) else (
        echo %GREEN%✅ All requirements installed successfully%RESET%
    )
) else (
    echo %YELLOW%⚠️  requirements.txt not found, installing basic packages...%RESET%
    pip install fastapi uvicorn[standard] sqlalchemy alembic python-telegram-bot openai python-dotenv loguru rich pydantic asyncio-mqtt websockets
    if %errorlevel% neq 0 (
        echo %RED%❌ Failed to install basic packages%RESET%
        pause
        exit /b 1
    )
    echo %GREEN%✅ Basic packages installed%RESET%
)

:: Verify installation
echo %CYAN%Verifying installation...%RESET%
python -c "import fastapi, uvicorn, sqlalchemy, telegram, openai, dotenv, loguru, rich" 2>nul
if %errorlevel% equ 0 (
    echo %GREEN%✅ All packages imported successfully%RESET%
) else (
    echo %YELLOW%⚠️  Some packages failed to import%RESET%
    echo %CYAN%Testing individual imports...%RESET%
    
    python -c "import fastapi" 2>nul && echo %GREEN%✅ FastAPI OK%RESET% || echo %RED%❌ FastAPI failed%RESET%
    python -c "import uvicorn" 2>nul && echo %GREEN%✅ Uvicorn OK%RESET% || echo %RED%❌ Uvicorn failed%RESET%
    python -c "import sqlalchemy" 2>nul && echo %GREEN%✅ SQLAlchemy OK%RESET% || echo %RED%❌ SQLAlchemy failed%RESET%
    python -c "import telegram" 2>nul && echo %GREEN%✅ Python-telegram-bot OK%RESET% || echo %RED%❌ Python-telegram-bot failed%RESET%
    python -c "import openai" 2>nul && echo %GREEN%✅ OpenAI OK%RESET% || echo %RED%❌ OpenAI failed%RESET%
    python -c "import dotenv" 2>nul && echo %GREEN%✅ Python-dotenv OK%RESET% || echo %RED%❌ Python-dotenv failed%RESET%
    python -c "import loguru" 2>nul && echo %GREEN%✅ Loguru OK%RESET% || echo %RED%❌ Loguru failed%RESET%
    python -c "import rich" 2>nul && echo %GREEN%✅ Rich OK%RESET% || echo %RED%❌ Rich failed%RESET%
)

echo.
echo %GREEN%🎉 Dependency installation completed!%RESET%
echo %CYAN%You can now run the application or continue with other setup steps.%RESET%
echo.

exit /b 0
