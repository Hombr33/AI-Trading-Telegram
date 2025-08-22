@echo off
setlocal enabledelayedexpansion

:: Set color codes
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "CYAN=[96m"
set "BLUE=[94m"
set "RESET=[0m"

echo %CYAN%⚙️  Configuring Environment%RESET%
echo.

:: Check if virtual environment exists and activate it
if exist "venv" (
    echo %CYAN%Activating virtual environment...%RESET%
    call venv\Scripts\activate.bat
    if %errorlevel% neq 0 (
        echo %RED%❌ Failed to activate virtual environment%RESET%
        pause
        exit /b 1
    )
    echo %GREEN%✅ Virtual environment activated%RESET%
) else (
    echo %RED%❌ Virtual environment not found. Please run 'Install Dependencies' first.%RESET%
    pause
    exit /b 1
)

:: Create runtime directories
echo %CYAN%Creating runtime directories...%RESET%
if not exist "runtime" mkdir runtime
if not exist "runtime\logs" mkdir runtime\logs
if not exist "runtime\data" mkdir runtime\data
if not exist "runtime\config" mkdir runtime\config
echo %GREEN%✅ Runtime directories created%RESET%

:: Check if .env file exists
if exist ".env" (
    echo %YELLOW%⚠️  .env file already exists%RESET%
    set /p overwrite="Do you want to recreate it? (y/N): "
    if /i "!overwrite!"=="y" (
        echo %CYAN%Removing existing .env file...%RESET%
        del ".env"
        echo %GREEN%✅ Existing .env file removed%RESET%
    ) else (
        echo %CYAN%Using existing .env file%RESET%
        goto :SHOW_ENV_CONTENTS
    )
)

:: Create .env file
echo %CYAN%Creating .env file...%RESET%
(
    echo # Telegram AI Trade Environment Configuration
    echo # ===========================================
    echo # Copy this file to .env.local and fill in your actual values
    echo # NEVER commit the actual .env file with real API keys to version control
    echo.
    echo # Database Configuration
    echo # =====================
    echo DATABASE_URL=sqlite:///runtime/data/trade.sqlite3
    echo DATABASE_ECHO=false
    echo DATABASE_POOL_SIZE=10
    echo DATABASE_MAX_OVERFLOW=20
    echo.
    echo # OpenAI Configuration
    echo # ===================
    echo OPENAI_API_KEY=your_openai_api_key_here
    echo OPENAI_MODEL=gpt-4
    echo OPENAI_MAX_TOKENS=4000
    echo OPENAI_TEMPERATURE=0.7
    echo OPENAI_TIMEOUT=30
    echo.
    echo # Telegram Configuration
    echo # =====================
    echo TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
    echo TELEGRAM_CHAT_ID=your_chat_id_here
    echo TELEGRAM_WEBHOOK_URL=
    echo TELEGRAM_POLLING_TIMEOUT=30
    echo.
    echo # MT5/MT4 Configuration
    echo # =====================
    echo MT5_LOGIN=your_mt5_login
    echo MT5_PASSWORD=your_mt5_password
    echo MT5_SERVER=your_mt5_server
    echo MT5_TIMEOUT=30000
    echo MT5_HEARTBEAT_INTERVAL=60
    echo.
    echo # Trading Configuration
    echo # ====================
    echo RISK_PER_TRADE_PCT=2.0
    echo MAX_DAILY_DRAWDOWN_PCT=6.0
    echo MAX_DAILY_TRADES=50
    echo MAX_OPEN_POSITIONS=10
    echo MAX_CORRELATION_EXPOSURE=0.7
    echo.
    echo # Position Management
    echo # ===================
    echo TRAILING_STOP_ENABLED=true
    echo TRAILING_START_POINTS=250
    echo TRAILING_STOP_POINTS=200
    echo TRAILING_STEP_POINTS=50
    echo BREAKEVEN_AT_RR=1.0
    echo.
    echo # Take Profit Configuration
    echo # =========================
    echo TP1_RR_RATIO=1.5
    echo TP2_RR_RATIO=3.0
    echo TP1_CLOSE_PCT=0.5
    echo TP2_CLOSE_PCT=0.5
    echo.
    echo # Session Management
    echo # ==================
    echo PREFER_LONDON_NY_OVERLAP=true
    echo ASIAN_SESSION_RISK_REDUCTION=0.5
    echo NEWS_EVENT_RISK_REDUCTION=0.3
    echo.
    echo # Logging Configuration
    echo # =====================
    echo LOG_LEVEL=INFO
    echo LOG_FILE=runtime/logs/app.log
    echo LOG_MAX_SIZE=100MB
    echo LOG_BACKUP_COUNT=5
    echo LOG_FORMAT=json
    echo.
    echo # API Configuration
    echo # =================
    echo API_HOST=0.0.0.0
    echo API_PORT=8000
    echo API_WORKERS=4
    echo API_RELOAD=true
    echo.
    echo # Security Configuration
    echo # =====================
    echo SECRET_KEY=your_secret_key_here_change_this_in_production
    echo ACCESS_TOKEN_EXPIRE_MINUTES=60
    echo REFRESH_TOKEN_EXPIRE_DAYS=7
    echo.
    echo # Monitoring Configuration
    echo # =======================
    echo ENABLE_METRICS=true
    echo METRICS_PORT=9090
    echo HEALTH_CHECK_INTERVAL=30
    echo ALERT_EMAIL=your_email@example.com
    echo.
    echo # Development Configuration
    echo # =========================
    echo DEBUG=false
    echo TESTING=false
    echo ENVIRONMENT=development
    echo.
    echo # External Services
    echo # ==================
    echo NEWS_API_KEY=your_news_api_key_here
    echo ECONOMIC_CALENDAR_URL=https://www.investing.com/economic-calendar
    echo.
    echo # Backup Configuration
    echo # ===================
    echo BACKUP_ENABLED=true
    echo BACKUP_INTERVAL_HOURS=24
    echo BACKUP_RETENTION_DAYS=30
    echo BACKUP_PATH=runtime/backups
) > .env

if %errorlevel% equ 0 (
    echo %GREEN%✅ .env file created successfully%RESET%
) else (
    echo %RED%❌ Failed to create .env file%RESET%
    pause
    exit /b 1
)

:SHOW_ENV_CONTENTS
echo.
echo %CYAN%📋 Current .env file contents:%RESET%
echo %BLUE%================================%RESET%
type .env
echo %BLUE%================================%RESET%

echo.
echo %YELLOW%⚠️  IMPORTANT: You need to edit the .env file with your actual values:%RESET%
echo.
echo %CYAN%Required configurations:%RESET%
echo %YELLOW%1. OPENAI_API_KEY - Get from https://platform.openai.com/api-keys%RESET%
echo %YELLOW%2. TELEGRAM_BOT_TOKEN - Get from @BotFather on Telegram%RESET%
echo %YELLOW%3. TELEGRAM_CHAT_ID - Your Telegram chat ID%RESET%
echo %YELLOW%4. MT5_LOGIN, MT5_PASSWORD, MT5_SERVER - Your MT5 credentials%RESET%
echo.

:: Create .env.example file
echo %CYAN%Creating .env.example file...%RESET%
copy .env .env.example >nul
echo %GREEN%✅ .env.example file created%RESET%

:: Create .env.local if it doesn't exist
if not exist ".env.local" (
    echo %CYAN%Creating .env.local file...%RESET%
    copy .env .env.local >nul
    echo %GREEN%✅ .env.local file created%RESET%
    echo %YELLOW%⚠️  Edit .env.local with your actual values%RESET%
)

:: Create configuration validation script
echo %CYAN%Creating configuration validation script...%RESET%
(
    echo @echo off
    echo echo Validating environment configuration...
    echo echo.
    echo if not exist ".env.local" ^(
    echo     echo ERROR: .env.local file not found
    echo     echo Please run the configure environment script first
    echo     pause
    echo     exit /b 1
    echo ^)
    echo.
    echo echo Checking required environment variables...
    echo echo.
    echo set "MISSING_VARS="
    echo.
    echo for /f "tokens=1 delims==" %%i in ^('.env.local'^) do ^(
    echo     set "LINE=%%i"
    echo     if "!LINE:~0,1!" neq "#" if "!LINE!" neq "" ^(
    echo         for /f "tokens=1 delims==" %%j in ^("!LINE!"^) do ^(
    echo             set "VAR_NAME=%%j"
    echo             if "!VAR_NAME!"=="OPENAI_API_KEY" if "!VAR_NAME!"=="your_openai_api_key_here" set "MISSING_VARS=!MISSING_VARS! OPENAI_API_KEY"
    echo             if "!VAR_NAME!"=="TELEGRAM_BOT_TOKEN" if "!VAR_NAME!"=="your_telegram_bot_token_here" set "MISSING_VARS=!MISSING_VARS! TELEGRAM_BOT_TOKEN"
    echo             if "!VAR_NAME!"=="MT5_LOGIN" if "!VAR_NAME!"=="your_mt5_login" set "MISSING_VARS=!MISSING_VARS! MT5_LOGIN"
    echo         ^)
    echo     ^)
    echo ^)
    echo.
    echo if defined MISSING_VARS ^(
    echo     echo ERROR: Missing or invalid configuration for: !MISSING_VARS!
    echo     echo Please edit .env.local file with your actual values
    echo     pause
    echo     exit /b 1
    echo ^)
    echo.
    echo echo All required configurations are present.
    echo echo Environment configuration is valid.
    echo pause
) > scripts\validate_env.bat

echo %GREEN%✅ Configuration validation script created%RESET%

:: Create environment loader script
echo %CYAN%Creating environment loader script...%RESET%
(
    echo @echo off
    echo echo Loading environment configuration...
    echo echo.
    echo if exist ".env.local" ^(
    echo     echo Loading from .env.local...
    echo     for /f "tokens=1,2 delims==" %%i in ^('.env.local'^) do ^(
    echo         set "LINE=%%i"
    echo         if "!LINE:~0,1!" neq "#" if "!LINE!" neq "" ^(
    echo             for /f "tokens=1,2 delims==" %%j in ^("!LINE!"^) do ^(
    echo                 set "VAR_NAME=%%j"
    echo                 set "VAR_VALUE=%%k"
    echo                 if not "!VAR_NAME!"=="" if not "!VAR_VALUE!"=="" ^(
    echo                     set "!VAR_NAME!=!VAR_VALUE!"
    echo                     echo Set: !VAR_NAME!=***hidden***
    echo                 ^)
    echo             ^)
    echo         ^)
    echo     ^)
    echo     echo Environment loaded successfully.
    echo ^) else ^(
    echo     echo Loading from .env...
    echo     for /f "tokens=1,2 delims==" %%i in ^('.env'^) do ^(
    echo         set "LINE=%%i"
    echo         if "!LINE:~0,1!" neq "#" if "!LINE!" neq "" ^(
    echo             for /f "tokens=1,2 delims==" %%j in ^("!LINE!"^) do ^(
    echo                 set "VAR_NAME=%%j"
    echo                 set "VAR_VALUE=%%k"
    echo                 if not "!VAR_NAME!"=="" if not "!VAR_VALUE!"=="" ^(
    echo                     set "!VAR_NAME!=!VAR_VALUE!"
    echo                     echo Set: !VAR_NAME!=***hidden***
    echo                 ^)
    echo             ^)
    echo         ^)
    echo     ^)
    echo     echo Environment loaded successfully.
    echo ^)
    echo echo.
) > scripts\load_env.bat

echo %GREEN%✅ Environment loader script created%RESET%

:: Test environment loading
echo %CYAN%Testing environment loading...%RESET%
call scripts\load_env.bat
if %errorlevel% equ 0 (
    echo %GREEN%✅ Environment loading test passed%RESET%
) else (
    echo %YELLOW%⚠️  Environment loading test failed, but continuing...%RESET%
)

echo.
echo %GREEN%🎉 Environment configuration completed!%RESET%
echo.
echo %CYAN%Next steps:%RESET%
echo %YELLOW%1. Edit .env.local file with your actual API keys and settings%RESET%
echo %YELLOW%2. Run 'Validate Environment' to check your configuration%RESET%
echo %YELLOW%3. Test the configuration with 'Test Installation'%RESET%
echo.
echo %CYAN%Files created:%RESET%
echo %YELLOW%- .env (template with default values)%RESET%
echo %YELLOW%- .env.example (copy of template)%RESET%
echo %YELLOW%- .env.local (for your actual values)%RESET%
echo %YELLOW%- scripts\validate_env.bat (validation script)%RESET%
echo %YELLOW%- scripts\load_env.bat (environment loader)%RESET%
echo.

exit /b 0
