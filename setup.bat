@echo off
setlocal enabledelayedexpansion

:: Set console title
title Telegram AI Trade - Setup & Installation

:: Set color codes
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "BLUE=[94m"
set "CYAN=[96m"
set "WHITE=[97m"
set "RESET=[0m"

:: Clear screen
cls

echo %CYAN%╔══════════════════════════════════════════════════════════════╗
echo ║                    TELEGRAM AI TRADE SETUP                        ║
echo ║                        Installation Wizard                         ║
echo ╚══════════════════════════════════════════════════════════════╝%RESET%
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%❌ Python is not installed or not in PATH%RESET%
    echo %YELLOW%Please install Python 3.8+ from https://python.org%RESET%
    echo.
    pause
    exit /b 1
)

:: Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo %GREEN%✅ Python %PYTHON_VERSION% detected%RESET%

:: Check if Git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%❌ Git is not installed or not in PATH%RESET%
    echo %YELLOW%Please install Git from https://git-scm.com%RESET%
    echo.
    pause
    exit /b 1
)

echo %GREEN%✅ Git detected%RESET%
echo.

:MAIN_MENU
echo %WHITE%Choose an option:%RESET%
echo.
echo %CYAN%1.%RESET% %YELLOW%Complete Setup (Recommended for first time)%RESET%
echo %CYAN%2.%RESET% %YELLOW%Install Dependencies Only%RESET%
echo %CYAN%3.%RESET% %YELLOW%Setup Database%RESET%
echo %CYAN%4.%RESET% %YELLOW%Configure Environment%RESET%
echo %CYAN%5.%RESET% %YELLOW%Test Installation%RESET%
echo %CYAN%6.%RESET% %YELLOW%Run Application%RESET%
echo %CYAN%7.%RESET% %YELLOW%Clean & Reset%RESET%
echo %CYAN%8.%RESET% %YELLOW%Exit%RESET%
echo.

set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" goto COMPLETE_SETUP
if "%choice%"=="2" goto INSTALL_DEPS
if "%choice%"=="3" goto SETUP_DB
if "%choice%"=="4" goto CONFIG_ENV
if "%choice%"=="5" goto TEST_INSTALL
if "%choice%"=="6" goto RUN_APP
if "%choice%"=="7" goto CLEAN_RESET
if "%choice%"=="8" goto EXIT
goto INVALID_CHOICE

:COMPLETE_SETUP
echo.
echo %CYAN%🚀 Starting Complete Setup...%RESET%
echo.
call scripts\complete_setup.bat
if %errorlevel% equ 0 (
    echo.
    echo %GREEN%✅ Complete setup finished successfully!%RESET%
) else (
    echo.
    echo %RED%❌ Setup failed. Check the logs above.%RESET%
)
echo.
pause
goto MAIN_MENU

:INSTALL_DEPS
echo.
echo %CYAN%📦 Installing Dependencies...%RESET%
echo.
call scripts\install_dependencies.bat
if %errorlevel% equ 0 (
    echo.
    echo %GREEN%✅ Dependencies installed successfully!%RESET%
) else (
    echo.
    echo %RED%❌ Dependency installation failed.%RESET%
)
echo.
pause
goto MAIN_MENU

:SETUP_DB
echo.
echo %CYAN%🗄️  Setting up Database...%RESET%
echo.
call scripts\setup_database.bat
if %errorlevel% equ 0 (
    echo.
    echo %GREEN%✅ Database setup completed!%RESET%
) else (
    echo.
    echo %RED%❌ Database setup failed.%RESET%
)
echo.
pause
goto MAIN_MENU

:CONFIG_ENV
echo.
echo %CYAN%⚙️  Configuring Environment...%RESET%
echo.
call scripts\configure_environment.bat
if %errorlevel% equ 0 (
    echo.
    echo %GREEN%✅ Environment configured successfully!%RESET%
) else (
    echo.
    echo %RED%❌ Environment configuration failed.%RESET%
)
echo.
pause
goto MAIN_MENU

:TEST_INSTALL
echo.
echo %CYAN%🧪 Testing Installation...%RESET%
echo.
call scripts\test_installation.bat
if %errorlevel% equ 0 (
    echo.
    echo %GREEN%✅ All tests passed! Installation is working correctly.%RESET%
) else (
    echo.
    echo %RED%❌ Some tests failed. Check the output above.%RESET%
)
echo.
pause
goto MAIN_MENU

:RUN_APP
echo.
echo %CYAN%🚀 Starting Telegram AI Trade Application...%RESET%
echo.
call scripts\run_application.bat
goto MAIN_MENU

:CLEAN_RESET
echo.
echo %YELLOW%⚠️  WARNING: This will remove all installed packages and reset the project.%RESET%
set /p confirm="Are you sure? Type 'YES' to confirm: "
if /i "%confirm%"=="YES" (
    echo.
    echo %CYAN%🧹 Cleaning and resetting project...%RESET%
    call scripts\clean_reset.bat
    if %errorlevel% equ 0 (
        echo.
        echo %GREEN%✅ Project cleaned and reset successfully!%RESET%
    ) else (
        echo.
        echo %RED%❌ Clean and reset failed.%RESET%
    )
) else (
    echo %YELLOW%Clean and reset cancelled.%RESET%
)
echo.
pause
goto MAIN_MENU

:INVALID_CHOICE
echo.
echo %RED%❌ Invalid choice. Please enter a number between 1-8.%RESET%
echo.
pause
goto MAIN_MENU

:EXIT
echo.
echo %CYAN%👋 Thank you for using Telegram AI Trade Setup!%RESET%
echo %YELLOW%If you need help, check the documentation in the docs/ folder.%RESET%
echo.
pause
exit /b 0
