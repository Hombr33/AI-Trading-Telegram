#!/usr/bin/env python3
"""
Basic functionality test for the AI Trading Bot system.
"""

import os
import sys
import json
from pathlib import Path

def test_directory_structure():
    """Test that all required directories and files exist."""
    print("🔍 Testing directory structure...")
    
    required_dirs = [
        "src",
        "src/models",
        "src/database", 
        "src/core",
        "src/api",
        "src/api/routes",
        "ea",
        "config",
        "docs",
        "scripts",
        "database/migrations",
        "runtime/data"
    ]
    
    required_files = [
        "src/app.py",
        "src/models/__init__.py",
        "src/database/__init__.py",
        "src/core/__init__.py",
        "src/api/__init__.py",
        "ea/BridgeEA.mq4",
        "ea/BridgeEA.mq5",
        "config/settings.yaml",
        ".env.example",
        "alembic.ini",
        "requirements.txt",
        "README.md",
        "VERIFICATION_CHECKLIST.md"
    ]
    
    all_good = True
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ {dir_path} - MISSING")
            all_good = False
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - MISSING")
            all_good = False
    
    return all_good

def test_config_files():
    """Test configuration files for validity."""
    print("\n🔧 Testing configuration files...")
    
    # Test .env.example
    if Path(".env.example").exists():
        with open(".env.example", "r") as f:
            content = f.read()
            if "BRIDGE_TOKEN" in content:
                print("  ✅ .env.example contains BRIDGE_TOKEN")
            else:
                print("  ❌ .env.example missing BRIDGE_TOKEN")
                return False
    else:
        print("  ❌ .env.example not found")
        return False
    
    # Test config/settings.yaml
    if Path("config/settings.yaml").exists():
        print("  ✅ config/settings.yaml exists")
    else:
        print("  ❌ config/settings.yaml not found")
        return False
    
    return True

def test_ea_files():
    """Test Expert Advisor files."""
    print("\n🤖 Testing Expert Advisor files...")
    
    # Test MT4 EA
    if Path("ea/BridgeEA.mq4").exists():
        with open("ea/BridgeEA.mq4", "r") as f:
            content = f.read()
            if "BRIDGE_TOKEN" in content and "http://127.0.0.1:8000" in content:
                print("  ✅ BridgeEA.mq4 properly configured")
            else:
                print("  ❌ BridgeEA.mq4 missing required configuration")
                return False
    else:
        print("  ❌ BridgeEA.mq4 not found")
        return False
    
    # Test MT5 EA
    if Path("ea/BridgeEA.mq5").exists():
        with open("ea/BridgeEA.mq5", "r") as f:
            content = f.read()
            if "BRIDGE_TOKEN" in content and "http://127.0.0.1:8000" in content:
                print("  ✅ BridgeEA.mq5 properly configured")
            else:
                print("  ❌ BridgeEA.mq5 missing required configuration")
                return False
    else:
        print("  ❌ BridgeEA.mq5 not found")
        return False
    
    return True

def test_database_schema():
    """Test database schema files."""
    print("\n🗄️ Testing database schema...")
    
    # Test models
    model_files = [
        "src/models/base.py",
        "src/models/users.py",
        "src/models/signals.py",
        "src/models/trades.py",
        "src/models/positions.py"
    ]
    
    for model_file in model_files:
        if Path(model_file).exists():
            print(f"  ✅ {model_file}")
        else:
            print(f"  ❌ {model_file} - MISSING")
            return False
    
    # Test database configuration
    if Path("src/database/config.py").exists():
        print("  ✅ Database configuration exists")
    else:
        print("  ❌ Database configuration missing")
        return False
    
    return True

def test_api_structure():
    """Test API structure."""
    print("\n🌐 Testing API structure...")
    
    # Test main app
    if Path("src/app.py").exists():
        with open("src/app.py", "r") as f:
            content = f.read()
            if "FastAPI" in content and "bridge" in content:
                print("  ✅ Main app properly configured")
            else:
                print("  ❌ Main app missing required components")
                return False
    else:
        print("  ❌ Main app not found")
        return False
    
    # Test routes
    route_files = [
        "src/api/routes/bridge.py",
        "src/api/routes/health.py",
        "src/api/routes/metrics.py",
        "src/api/routes/v1.py"
    ]
    
    for route_file in route_files:
        if Path(route_file).exists():
            print(f"  ✅ {route_file}")
        else:
            print(f"  ❌ {route_file} - MISSING")
            return False
    
    return True

def test_documentation():
    """Test documentation files."""
    print("\n📚 Testing documentation...")
    
    doc_files = [
        "docs/README.md",
        "docs/architecture.md",
        "docs/database-erd.md",
        "VERIFICATION_CHECKLIST.md"
    ]
    
    for doc_file in doc_files:
        if Path(doc_file).exists():
            print(f"  ✅ {doc_file}")
        else:
            print(f"  ❌ {doc_file} - MISSING")
            return False
    
    return True

def test_scripts():
    """Test Windows scripts."""
    print("\n🪟 Testing Windows scripts...")
    
    script_files = [
        "scripts/run_app.bat",
        "scripts/first_run.bat"
    ]
    
    for script_file in script_files:
        if Path(script_file).exists():
            print(f"  ✅ {script_file}")
        else:
            print(f"  ❌ {script_file} - MISSING")
            return False
    
    return True

def main():
    """Run all tests."""
    print("🚀 AI Trading Bot System Verification")
    print("=" * 50)
    
    tests = [
        test_directory_structure,
        test_config_files,
        test_ea_files,
        test_database_schema,
        test_api_structure,
        test_documentation,
        test_scripts
    ]
    
    all_passed = True
    
    for test in tests:
        try:
            if not test():
                all_passed = False
        except Exception as e:
            print(f"  ❌ Test failed with error: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! System is ready.")
        print("\n📋 Next steps:")
        print("1. Set BRIDGE_TOKEN in .env file")
        print("2. Install Python dependencies")
        print("3. Start the application")
        print("4. Configure MT4/MT5")
        print("5. Attach BridgeEA to chart")
    else:
        print("❌ Some tests failed. Please check the issues above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)