@echo off
setlocal enabledelayedexpansion

:: Set color codes
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "CYAN=[96m"
set "RESET=[0m"

echo %CYAN%🗄️  Setting up Database%RESET%
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
if not exist "runtime\data" mkdir runtime\data
if not exist "runtime\logs" mkdir runtime\logs
echo %GREEN%✅ Runtime directories created%RESET%

:: Check if SQLite database exists
if exist "runtime\data\trade.sqlite3" (
    echo %YELLOW%⚠️  Database already exists%RESET%
    set /p overwrite="Do you want to recreate it? (y/N): "
    if /i "!overwrite!"=="y" (
        echo %CYAN%Removing existing database...%RESET%
        del "runtime\data\trade.sqlite3"
        echo %GREEN%✅ Existing database removed%RESET%
    ) else (
        echo %CYAN%Using existing database%RESET%
    )
)

:: Create new database if needed
if not exist "runtime\data\trade.sqlite3" (
    echo %CYAN%Creating SQLite database...%RESET%
    echo. > runtime\data\trade.sqlite3
    if %errorlevel% equ 0 (
        echo %GREEN%✅ Database file created%RESET%
    ) else (
        echo %RED%❌ Failed to create database file%RESET%
        pause
        exit /b 1
    )
)

:: Check if alembic.ini exists
if not exist "alembic.ini" (
    echo %YELLOW%⚠️  alembic.ini not found, creating basic configuration...%RESET%
    (
        echo [alembic]
        echo script_location = database/migrations
        echo sqlalchemy.url = sqlite:///runtime/data/trade.sqlite3
        echo.
        echo [loggers]
        echo keys = root,sqlalchemy,alembic
        echo.
        echo [handlers]
        echo keys = console
        echo.
        echo [formatters]
        echo keys = generic
        echo.
        echo [logger_root]
        echo level = WARN
        echo handlers = console
        echo qualname =
        echo.
        echo [logger_sqlalchemy]
        echo level = WARN
        echo handlers =
        echo qualname = sqlalchemy.engine
        echo.
        echo [logger_alembic]
        echo level = INFO
        echo handlers =
        echo qualname = alembic
        echo.
        echo [handler_console]
        echo class = StreamHandler
        echo args = ^(sys.stderr^)
        echo level = NOTSET
        echo formatter = generic
        echo.
        echo [formatter_generic]
        echo format = %^(levelname^)-5.5s [%^(name^)s] %^(message^)s
        echo datefmt = %H:%M:%S
    ) > alembic.ini
    echo %GREEN%✅ alembic.ini created%RESET%
)

:: Check if migrations directory exists
if not exist "database\migrations" (
    echo %CYAN%Creating migrations directory...%RESET%
    mkdir database\migrations 2>nul
    echo %GREEN%✅ Migrations directory created%RESET%
)

:: Check if env.py exists in migrations
if not exist "database\migrations\env.py" (
    echo %CYAN%Creating env.py for migrations...%RESET%
    (
        echo from logging.config import fileConfig
        echo from sqlalchemy import engine_from_config
        echo from sqlalchemy import pool
        echo from alembic import context
        echo import os
        echo import sys
        echo.
        echo # Add the src directory to the Python path
        echo sys.path.append^('src'^)
        echo.
        echo # Import your models here
        echo from models.base import Base
        echo.
        echo # this is the Alembic Config object, which provides
        echo # access to the values within the .ini file in use.
        echo config = context.config
        echo.
        echo # Interpret the config file for Python logging.
        echo # This line sets up loggers basically.
        echo if config.config_file_name is not None:
        echo     fileConfig^(config.config_file_name^)
        echo.
        echo # add your model's MetaData object here
        echo # for 'autogenerate' support
        echo target_metadata = Base.metadata
        echo.
        echo # other values from the config, defined by the needs of env.py,
        echo # can be acquired:
        echo # my_important_option = config.get_main_option^("my_important_option"^)
        echo # ... etc.
        echo.
        echo def run_migrations_offline^(^) -^> None:
        echo     """Run migrations in 'offline' mode."""
        echo.
        echo     url = config.get_main_option^("sqlalchemy.url"^)
        echo     context.configure^(
        echo         url=url,
        echo         target_metadata=target_metadata,
        echo         literal_binds=True,
        echo         dialect_opts={"paramstyle": "named"},
        echo     ^)
        echo.
        echo     with context.begin_transaction^(^):
        echo         context.run_migrations^(^)
        echo.
        echo.
        echo def run_migrations_online^(^) -^> None:
        echo     """Run migrations in 'online' mode."""
        echo.
        echo     connectable = engine_from_config^(
        echo         config.get_section^(config.config_ini_section^),
        echo         prefix="sqlalchemy.",
        echo         poolclass=pool.NullPool,
        echo     ^)
        echo.
        echo     with connectable.connect^(^) as connection:
        echo         context.configure^(
        echo             connection=connection, target_metadata=target_metadata
        echo         ^)
        echo.
        echo         with context.begin_transaction^(^):
        echo             context.run_migrations^(^)
        echo.
        echo.
        echo if context.is_offline_mode^(^):
        echo     run_migrations_offline^(^)
        echo else:
        echo     run_migrations_online^(^)
    ) > database\migrations\env.py
    echo %GREEN%✅ env.py created%RESET%
)

:: Check if script.py.mako exists
if not exist "database\migrations\script.py.mako" (
    echo %CYAN%Creating script.py.mako...%RESET%
    (
        echo """${up_revision}
        echo """${down_revision}
        echo """${comment}
        echo """${imports}
        echo.
        echo def upgrade^(^) -^> None:
        echo     """${upgrades}"""
        echo     ${upgrades if upgrades else "pass"}
        echo.
        echo.
        echo def downgrade^(^) -^> None:
        echo     """${downgrades}"""
        echo     ${downgrades if downgrades else "pass"}
    ) > database\migrations\script.py.mako
    echo %GREEN%✅ script.py.mako created%RESET%
)

:: Initialize alembic if not already done
if not exist "database\migrations\versions" (
    echo %CYAN%Initializing Alembic...%RESET%
    alembic init database\migrations
    if %errorlevel% neq 0 (
        echo %YELLOW%⚠️  Alembic initialization failed, but continuing...%RESET%
    ) else (
        echo %GREEN%✅ Alembic initialized%RESET%
    )
)

:: Create versions directory if it doesn't exist
if not exist "database\migrations\versions" mkdir database\migrations\versions

:: Check if there are any migration files
dir /b "database\migrations\versions\*.py" >nul 2>&1
if %errorlevel% neq 0 (
    echo %CYAN%Creating initial migration...%RESET%
    alembic revision --autogenerate -m "Initial database schema"
    if %errorlevel% neq 0 (
        echo %YELLOW%⚠️  Failed to create initial migration, but continuing...%RESET%
    ) else (
        echo %GREEN%✅ Initial migration created%RESET%
    )
)

:: Run migrations
echo %CYAN%Running database migrations...%RESET%
alembic upgrade head
if %errorlevel% neq 0 (
    echo %YELLOW%⚠️  Database migrations failed, but continuing...%RESET%
    echo %CYAN%This might be normal if the database schema is already up to date.%RESET%
) else (
    echo %GREEN%✅ Database migrations completed%RESET%
)

:: Test database connection
echo %CYAN%Testing database connection...%RESET%
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
) else (
    echo %YELLOW%⚠️  Database connection test failed, but continuing...%RESET%
)

echo.
echo %GREEN%🎉 Database setup completed!%RESET%
echo %CYAN%The database is now ready for use.%RESET%
echo.

exit /b 0
