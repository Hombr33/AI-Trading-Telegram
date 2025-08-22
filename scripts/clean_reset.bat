@echo off
setlocal enabledelayedexpansion

:: Set color codes
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "CYAN=[96m"
set "BLUE=[94m"
set "RESET=[0m"

echo %CYAN%🧹 Cleaning and Resetting Project%RESET%
echo %YELLOW%This will remove all installed packages and reset the project%RESET%
echo.

:: Final confirmation
echo %RED%⚠️  WARNING: This action cannot be undone!%RESET%
echo %YELLOW%The following will be removed:%RESET%
echo %YELLOW%• Virtual environment (venv folder)%RESET%
echo %YELLOW%• Installed Python packages%RESET%
echo %YELLOW%• Database files%RESET%
echo %YELLOW%• Log files%RESET%
echo %YELLOW%• Runtime data%RESET%
echo.
set /p final_confirm="Type 'YES' to confirm: "
if /i "%final_confirm%" neq "YES" (
    echo %CYAN%Clean and reset cancelled.%RESET%
    pause
    exit /b 0
)

echo.
echo %CYAN%Starting cleanup process...%RESET%
echo.

:: Step 1: Stop any running processes
echo %CYAN%Step 1: Stopping running processes...%RESET%
taskkill /f /im python.exe 2>nul
if %errorlevel% equ 0 (
    echo %GREEN%✅ Python processes stopped%RESET%
) else (
    echo %YELLOW%⚠️  No Python processes were running%RESET%
)

:: Step 2: Remove virtual environment
echo %CYAN%Step 2: Removing virtual environment...%RESET%
if exist "venv" (
    rmdir /s /q "venv" 2>nul
    if %errorlevel% equ 0 (
        echo %GREEN%✅ Virtual environment removed%RESET%
    ) else (
        echo %RED%❌ Failed to remove virtual environment%RESET%
        echo %YELLOW%You may need to close any applications using it%RESET%
    )
) else (
    echo %YELLOW%⚠️  Virtual environment not found%RESET%
)

:: Step 3: Remove runtime directories
echo %CYAN%Step 3: Removing runtime directories...%RESET%
if exist "runtime" (
    rmdir /s /q "runtime" 2>nul
    if %errorlevel% equ 0 (
        echo %GREEN%✅ Runtime directories removed%RESET%
    ) else (
        echo %RED%❌ Failed to remove runtime directories%RESET%
    )
) else (
    echo %YELLOW%⚠️  Runtime directories not found%RESET%
)

:: Step 4: Remove environment files
echo %CYAN%Step 4: Removing environment files...%RESET%
set "ENV_FILES_REMOVED=0"

if exist ".env.local" (
    del ".env.local" 2>nul
    if %errorlevel% equ 0 (
        echo %GREEN%✅ .env.local removed%RESET%
        set /a ENV_FILES_REMOVED+=1
    ) else (
        echo %RED%❌ Failed to remove .env.local%RESET%
    )
)

if exist ".env" (
    del ".env" 2>nul
    if %errorlevel% equ 0 (
        echo %GREEN%✅ .env removed%RESET%
        set /a ENV_FILES_REMOVED+=1
    ) else (
        echo %RED%❌ Failed to remove .env%RESET%
    )
)

if %ENV_FILES_REMOVED% gte 1 (
    echo %GREEN%✅ Environment files cleaned%RESET%
) else (
    echo %YELLOW%⚠️  No environment files found%RESET%
)

:: Step 5: Remove Python cache files
echo %CYAN%Step 5: Removing Python cache files...%RESET%
set "CACHE_FILES_REMOVED=0"

:: Remove __pycache__ directories
for /d /r . %%d in (__pycache__) do @if exist "%%d" (
    rmdir /s /q "%%d" 2>nul
    if %errorlevel% equ 0 (
        set /a CACHE_FILES_REMOVED+=1
    )
)

:: Remove .pyc files
for /r . %%f in (*.pyc) do @if exist "%%f" (
    del "%%f" 2>nul
    if %errorlevel% equ 0 (
        set /a CACHE_FILES_REMOVED+=1
    )
)

if %CACHE_FILES_REMOVED% gte 1 (
    echo %GREEN%✅ Python cache files removed%RESET%
) else (
    echo %YELLOW%⚠️  No Python cache files found%RESET%
)

:: Step 6: Remove log files
echo %CYAN%Step 6: Removing log files...%RESET%
set "LOG_FILES_REMOVED=0"

if exist "*.log" (
    del "*.log" 2>nul
    if %errorlevel% equ 0 (
        echo %GREEN%✅ Log files removed%RESET%
        set /a LOG_FILES_REMOVED+=1
    )
)

if exist "logs" (
    rmdir /s /q "logs" 2>nul
    if %errorlevel% equ 0 (
        echo %GREEN%✅ Logs directory removed%RESET%
        set /a LOG_FILES_REMOVED+=1
    )
)

if %LOG_FILES_REMOVED% gte 1 (
    echo %GREEN%✅ Log files cleaned%RESET%
) else (
    echo %YELLOW%⚠️  No log files found%RESET%
)

:: Step 7: Remove temporary files
echo %CYAN%Step 7: Removing temporary files...%RESET%
set "TEMP_FILES_REMOVED=0"

if exist "*.tmp" (
    del "*.tmp" 2>nul
    if %errorlevel% equ 0 (
        echo %GREEN%✅ Temporary files removed%RESET%
        set /a TEMP_FILES_REMOVED+=1
    )
)

if exist "*.temp" (
    del "*.temp" 2>nul
    if %errorlevel% equ 0 (
        echo %GREEN%✅ Temporary files removed%RESET%
        set /a TEMP_FILES_REMOVED+=1
    )
)

if %TEMP_FILES_REMOVED% gte 1 (
    echo %GREEN%✅ Temporary files cleaned%RESET%
) else (
    echo %YELLOW%⚠️  No temporary files found%RESET%
)

:: Step 8: Remove desktop shortcuts
echo %CYAN%Step 8: Removing desktop shortcuts...%RESET%
if exist "%USERPROFILE%\Desktop\Telegram AI Trade Setup.bat" (
    del "%USERPROFILE%\Desktop\Telegram AI Trade Setup.bat" 2>nul
    if %errorlevel% equ 0 (
        echo %GREEN%✅ Desktop shortcut removed%RESET%
    ) else (
        echo %RED%❌ Failed to remove desktop shortcut%RESET%
    )
) else (
    echo %YELLOW%⚠️  Desktop shortcut not found%RESET%
)

:: Step 9: Clean npm packages if Node.js is installed
echo %CYAN%Step 9: Cleaning Node.js packages...%RESET%
node --version >nul 2>&1
if %errorlevel% equ 0 (
    echo %CYAN%Node.js detected, cleaning global packages...%RESET%
    npm uninstall -g pm2 2>nul
    if %errorlevel% equ 0 (
        echo %GREEN%✅ PM2 removed%RESET%
    ) else (
        echo %YELLOW%⚠️  Failed to remove PM2%RESET%
    )
) else (
    echo %YELLOW%⚠️  Node.js not detected, skipping npm cleanup%RESET%
)

:: Step 10: Verify cleanup
echo %CYAN%Step 10: Verifying cleanup...%RESET%
set "CLEANUP_VERIFIED=true"

if exist "venv" (
    echo %RED%❌ Virtual environment still exists%RESET%
    set "CLEANUP_VERIFIED=false"
)

if exist "runtime" (
    echo %RED%❌ Runtime directories still exist%RESET%
    set "CLEANUP_VERIFIED=false"
)

if exist ".env.local" (
    echo %RED%❌ .env.local still exists%RESET%
    set "CLEANUP_VERIFIED=false"
)

if exist ".env" (
    echo %RED%❌ .env still exists%RESET%
    set "CLEANUP_VERIFIED=false"
)

if "%CLEANUP_VERIFIED%"=="true" (
    echo %GREEN%✅ Cleanup verification passed%RESET%
) else (
    echo %YELLOW%⚠️  Some items could not be removed%RESET%
    echo %YELLOW%You may need to remove them manually%RESET%
)

:: Step 11: Create fresh directories
echo %CYAN%Step 11: Creating fresh directories...%RESET%
mkdir "runtime" 2>nul
mkdir "runtime\data" 2>nul
mkdir "runtime\logs" 2>nul
mkdir "runtime\config" 2>nul

if exist "runtime" (
    echo %GREEN%✅ Fresh runtime directories created%RESET%
) else (
    echo %RED%❌ Failed to create runtime directories%RESET%
)

:: Step 12: Summary
echo.
echo %BLUE%══════════════════════════════════════════════════════════════%RESET%
echo %CYAN%🧹 CLEANUP COMPLETED%RESET%
echo %BLUE%══════════════════════════════════════════════════════════════%RESET%
echo.

if "%CLEANUP_VERIFIED%"=="true" (
    echo %GREEN%🎉 Project has been successfully cleaned and reset!%RESET%
    echo.
    echo %CYAN%What was removed:%RESET%
    echo %YELLOW%✅ Virtual environment%RESET%
    echo %YELLOW%✅ Installed packages%RESET%
    echo %YELLOW%✅ Database files%RESET%
    echo %YELLOW%✅ Log files%RESET%
    echo %YELLOW%✅ Environment files%RESET%
    echo %YELLOW%✅ Cache files%RESET%
    echo %YELLOW%✅ Temporary files%RESET%
    echo %YELLOW%✅ Desktop shortcuts%RESET%
    echo.
    echo %CYAN%What was preserved:%RESET%
    echo %YELLOW%✅ Source code%RESET%
    echo %YELLOW%✅ Configuration files%RESET%
    echo %YELLOW%✅ Documentation%RESET%
    echo %YELLOW%✅ Scripts%RESET%
) else (
    echo %YELLOW%⚠️  Project cleanup completed with some issues%RESET%
    echo %CYAN%Some items may need manual removal%RESET%
)

echo.
echo %CYAN%Next steps:%RESET%
echo %YELLOW%1. Run 'Complete Setup' to reinstall everything%RESET%
echo %YELLOW%2. Or run individual setup steps as needed%RESET%
echo.
echo %CYAN%The project is now ready for a fresh installation.%RESET%
echo.

pause
exit /b 0
