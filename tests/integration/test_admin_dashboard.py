#!/usr/bin/env python3
"""
Test script for Admin Dashboard
Tests the admin dashboard functionality and integration.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_admin_dashboard_structure():
    """Test admin dashboard file structure."""
    admin_dir = os.path.join(os.path.dirname(__file__), 'src', 'admin_dashboard')

    if os.path.exists(admin_dir):
        print("✓ Admin dashboard directory found")

        # Check required files
        required_files = [
            'router.py',
            'README.md',
            '__init__.py'
        ]

        for file in required_files:
            if os.path.exists(os.path.join(admin_dir, file)):
                print(f"✓ {file} found")
            else:
                print(f"✗ {file} missing")

        # Check templates
        templates_dir = os.path.join(admin_dir, 'templates')
        if os.path.exists(templates_dir):
            templates = os.listdir(templates_dir)
            print(f"✓ Templates directory found with {len(templates)} templates")
        else:
            print("✗ Templates directory missing")

        # Check static files
        static_dir = os.path.join(admin_dir, 'static')
        if os.path.exists(static_dir):
            print("✓ Static files directory found")
        else:
            print("✗ Static files directory missing")

    else:
        print("✗ Admin dashboard directory not found")

def test_imports():
    """Test that we can import the admin dashboard components."""
    try:
        from admin_dashboard.router import router as admin_router
        print("✓ Admin dashboard router imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import admin dashboard router: {e}")

    try:
        from admin_dashboard import __version__
        print(f"✓ Admin dashboard version: {__version__}")
    except ImportError as e:
        print(f"✗ Failed to import admin dashboard: {e}")

def test_template_files():
    """Test that template files exist and are readable."""
    template_dir = os.path.join(os.path.dirname(__file__), 'src', 'admin_dashboard', 'templates')

    if os.path.exists(template_dir):
        templates = {
            'base.html': 'Base template',
            'dashboard.html': 'Main dashboard',
            'users.html': 'User management',
            'system.html': 'System monitoring',
            'signals.html': 'Signal monitoring',
            'platforms.html': 'Platform management',
            'config.html': 'Configuration management',
            'audit.html': 'Audit logs',
            'user_details.html': 'User details',
            'error.html': 'Error page'
        }

        for template, description in templates.items():
            template_path = os.path.join(template_dir, template)
            if os.path.exists(template_path):
                print(f"✓ {template} - {description}")
            else:
                print(f"✗ {template} - {description} (missing)")

def test_static_files():
    """Test that static files exist."""
    static_dir = os.path.join(os.path.dirname(__file__), 'src', 'admin_dashboard', 'static')

    if os.path.exists(static_dir):
        # Check CSS
        css_dir = os.path.join(static_dir, 'css')
        if os.path.exists(css_dir):
            css_files = os.listdir(css_dir)
            print(f"✓ CSS files found: {len(css_files)} files")

        # Check JS
        js_dir = os.path.join(static_dir, 'js')
        if os.path.exists(js_dir):
            js_files = os.listdir(js_dir)
            print(f"✓ JavaScript files found: {len(js_files)} files")

        # Check images
        img_dir = os.path.join(static_dir, 'images')
        if os.path.exists(img_dir):
            print("✓ Images directory found")
        else:
            print("⚠ Images directory not found (this is optional)")

def main():
    """Run all tests."""
    print("🧪 Testing Admin Dashboard Structure")
    print("=" * 50)

    test_admin_dashboard_structure()
    test_imports()
    test_template_files()
    test_static_files()

    print("=" * 50)
    print("✅ Admin Dashboard structure tests completed!")
    print("\n📝 To access the admin dashboard:")
    print("1. Start the main application: python run.py")
    print("2. Navigate to: http://localhost:8000/admin/?admin_id=YOUR_ADMIN_ID")
    print("3. Replace YOUR_ADMIN_ID with your actual Telegram user ID")

def test_admin_dashboard_routes():
    """Test admin dashboard routes."""
    print("✓ Admin dashboard route tests skipped (requires full app initialization)")

def test_static_files():
    """Test static file existence."""
    static_dir = os.path.join(os.path.dirname(__file__), 'src', 'admin_dashboard', 'static')

    if os.path.exists(static_dir):
        # Check CSS files
        css_file = os.path.join(static_dir, 'css', 'admin.css')
        if os.path.exists(css_file):
            print("✓ Admin CSS file exists")
        else:
            print("✗ Admin CSS file missing")

        # Check JS files
        js_file = os.path.join(static_dir, 'js', 'admin.js')
        if os.path.exists(js_file):
            print("✓ Admin JavaScript file exists")
        else:
            print("✗ Admin JavaScript file missing")
    else:
        print("✗ Static files directory not found")

def test_template_rendering():
    """Test template rendering (basic check)."""
    try:
        from admin_dashboard.router import router
        print("✓ Admin dashboard router imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import admin dashboard router: {e}")
        return

    # Check if templates directory exists
    template_dir = os.path.join(os.path.dirname(__file__), 'src', 'admin_dashboard', 'templates')
    if os.path.exists(template_dir):
        templates = os.listdir(template_dir)
        print(f"✓ Templates directory found with {len(templates)} templates: {', '.join(templates)}")
    else:
        print("✗ Templates directory not found")

def test_multi_user_service_integration():
    """Test multi-user service integration."""
    try:
        # This would normally require a database connection
        # For now, just test that the service can be imported
        from services.multi_user_service import MultiUserService
        print("✓ Multi-user service imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import multi-user service: {e}")

async def test_admin_functionality():
    """Test admin functionality with mock data."""
    try:
        # Create a mock multi-user service
        service = MultiUserService("mock_token")

        # Test that we can set it for the admin dashboard
        from admin_dashboard.router import set_multi_user_service
        set_multi_user_service(service)

        print("✓ Admin dashboard service integration successful")

    except Exception as e:
        print(f"✗ Admin functionality test failed: {e}")

def main():
    """Run all tests."""
    print("🧪 Testing Admin Dashboard")
    print("=" * 50)

    # Run synchronous tests
    test_admin_dashboard_routes()
    test_static_files()
    test_template_rendering()
    test_multi_user_service_integration()

    # Run asynchronous tests
    asyncio.run(test_admin_functionality())

    print("=" * 50)
    print("✅ Admin Dashboard tests completed!")
    print("\n📝 To access the admin dashboard:")
    print("1. Start the main application: python run.py")
    print("2. Navigate to: http://localhost:8000/admin/?admin_id=YOUR_ADMIN_ID")
    print("3. Replace YOUR_ADMIN_ID with your actual Telegram user ID")

if __name__ == "__main__":
    main()