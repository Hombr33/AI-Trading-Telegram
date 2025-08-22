@echo off
setlocal

REM Check if python is installed
python --version >nul 2>&1
if %errorlevel%==0 (
    echo Python is already installed.
    exit /b 0
)

REM Download latest Python 3.x installer (64-bit)
set PYTHON_URL=https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe
set PYTHON_INSTALLER=python-installer.exe

if exist %PYTHON_INSTALLER% del %PYTHON_INSTALLER%

echo Downloading Python installer...
powershell -Command "try { Invoke-WebRequest -Uri %PYTHON_URL% -OutFile %PYTHON_INSTALLER% -ErrorAction Stop } catch { Write-Host 'Download failed.'; exit 1 }"

if not exist %PYTHON_INSTALLER% (
    echo Failed to download Python installer.
    pause
    exit /b 1
)


echo Running Python installer (this may require admin rights)...
%PYTHON_INSTALLER% /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 > installer.log 2>&1
set INSTALL_EXIT=%errorlevel%

if %INSTALL_EXIT% neq 0 (
    echo Silent install failed or was blocked. Trying interactive install...
    echo If you see a Windows prompt, please approve the installation.
    start /wait %PYTHON_INSTALLER%
    set INSTALL_EXIT=%errorlevel%
    if %INSTALL_EXIT% neq 0 (
        echo Python installer failed to run. You may need to run this script as Administrator.
        pause
        exit /b 1
    )
)

REM Remove installer
if exist %PYTHON_INSTALLER% del %PYTHON_INSTALLER%

REM Verify installation
python --version >nul 2>&1
if %errorlevel%==0 (
    echo Python installed successfully.
    exit /b 0
) else (
    echo Python installation failed.
    pause
    exit /b 1
)
