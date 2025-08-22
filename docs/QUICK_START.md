# 🚀 Quick Start Guide - Telegram AI Trade

## 📋 Prerequisites

Before running the setup scripts, ensure you have:

- **Windows 10/11** (or compatible Windows version)
- **Python 3.8+** installed and added to PATH
- **Git** installed and added to PATH
- **At least 2GB free disk space**
- **At least 4GB RAM**

## 🎯 Getting Started

### 1. Download the Repository
```bash
git clone <your-repo-url>
cd telegram-ai-trade
```

### 2. Run the Setup
Double-click `setup.bat` in the root folder, or run it from command prompt:
```cmd
setup.bat
```

### 3. Choose Setup Option
The setup wizard will present you with 8 options:

- **Option 1: Complete Setup** ⭐ (Recommended for first time)
- **Option 2: Install Dependencies Only**
- **Option 3: Setup Database**
- **Option 4: Configure Environment**
- **Option 5: Test Installation**
- **Option 6: Run Application**
- **Option 7: Clean & Reset**
- **Option 8: Exit**

## 🚀 First Time Setup (Recommended)

1. **Choose Option 1: Complete Setup**
   - This will install everything automatically
   - Creates virtual environment
   - Installs all Python packages
   - Sets up database
   - Configures environment
   - Creates startup scripts

2. **Configure Your API Keys**
   - Edit `.env.local` file with your actual values:
     - `OPENAI_API_KEY` - Get from [OpenAI Platform](https://platform.openai.com/api-keys)
     - `TELEGRAM_BOT_TOKEN` - Get from [@BotFather](https://t.me/BotFather)
     - `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER` - Your MT5 credentials

3. **Test the Installation**
   - Choose Option 5 to run comprehensive tests
   - Ensure all tests pass (80%+ success rate)

4. **Run the Application**
   - Choose Option 6 to start the trading bot
   - Access the web interface at http://localhost:8000

## 🔧 Individual Setup Steps

If you prefer to set up components individually:

### Install Dependencies Only
```cmd
scripts\install_dependencies.bat
```

### Setup Database
```cmd
scripts\setup_database.bat
```

### Configure Environment
```cmd
scripts\configure_environment.bat
```

### Test Installation
```cmd
scripts\test_installation.bat
```

### Run Application
```cmd
scripts\run_application.bat
```

## 📁 What Gets Created

The setup scripts will create:

- **`venv/`** - Python virtual environment
- **`runtime/`** - Runtime data, logs, and configuration
- **`.env`** - Environment template
- **`.env.local`** - Your actual configuration (edit this!)
- **`.env.example`** - Example configuration
- **`scripts/`** - Additional utility scripts
- **Desktop shortcut** - Quick access to setup

## 🚨 Troubleshooting

### Common Issues

1. **Python not found**
   - Install Python 3.8+ from [python.org](https://python.org)
   - Ensure Python is added to PATH

2. **Git not found**
   - Install Git from [git-scm.com](https://git-scm.com)
   - Ensure Git is added to PATH

3. **Port 8000 already in use**
   - Stop other applications using port 8000
   - Or change the port in `.env.local`

4. **Database connection failed**
   - Run "Setup Database" option
   - Check file permissions

5. **Package installation failed**
   - Ensure you have internet connection
   - Try running "Install Dependencies" again
   - Check Python version compatibility

### Reset Everything

If something goes wrong, use Option 7 to clean and reset:
```cmd
scripts\clean_reset.bat
```

This will remove everything and let you start fresh.

## 📚 Next Steps

After successful setup:

1. **Read the Documentation**
   - Check `docs/` folder for detailed guides
   - Review `README.md` for project overview

2. **Configure Trading Parameters**
   - Edit risk management settings in `.env.local`
   - Adjust position sizing and drawdown limits

3. **Test with Demo Account**
   - Use demo MT5 account first
   - Verify all connections work

4. **Monitor Performance**
   - Check logs in `runtime/logs/`
   - Monitor trading performance
   - Review risk metrics

## 🆘 Need Help?

- **Check the logs** in `runtime/logs/`
- **Review documentation** in `docs/` folder
- **Run tests** using Option 5
- **Check system requirements** are met
- **Verify API keys** are correct

## 🔄 Maintenance

### Regular Tasks
- Monitor log files for errors
- Check database health
- Update Python packages periodically
- Backup configuration files

### Updates
- Pull latest code from repository
- Run "Install Dependencies" to update packages
- Test installation before running

---

**Happy Trading! 🎯📈**

Remember: Always test with small amounts first and never risk more than you can afford to lose.
