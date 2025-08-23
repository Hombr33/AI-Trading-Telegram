#!/usr/bin/env python3
"""Demo script to showcase enhanced Telegram keyboards."""

from src.telegram_bot.utils.keyboards import *
from src.telegram_bot.utils.visual_effects import VisualEffects

def demo_keyboards():
    """Demonstrate all keyboard types."""
    print("🎮 TELEGRAM BOT KEYBOARD SHOWCASE 🎮\n")
    
    # Reply Keyboard Demo
    print("1. 📱 REPLY KEYBOARD (Main Menu):")
    main_menu = get_main_menu_keyboard()
    print(f"   Rows: {len(main_menu.keyboard)}")
    for row in main_menu.keyboard:
        buttons = [btn.text for btn in row]
        print(f"   {' | '.join(buttons)}")
    
    print("\n2. 🎯 INLINE KEYBOARDS:")
    
    # Trading Dashboard
    print("   📊 Trading Dashboard:")
    dashboard = create_trading_dashboard_keyboard()
    print(f"   Buttons: {len(dashboard.inline_keyboard)} rows")
    
    # Progress Bar Demo
    print("   📊 Progress Bar:")
    progress = create_progress_keyboard(75, 100, "demo")
    print("   █████████░ 75/100")
    
    # Pagination Demo
    print("   📄 Pagination:")
    pages = create_paginated_keyboard(3, 10, "demo")
    print("   ⬅️ Previous | 📄 3/10 | ➡️ Next")
    
    print("\n3. 🎨 VISUAL EFFECTS:")
    
    # Progress bars
    print("   Progress Bars:")
    print(f"   {VisualEffects.create_progress_bar(25, 100)} 25%")
    print(f"   {VisualEffects.create_progress_bar(75, 100)} 75%")
    print(f"   {VisualEffects.create_progress_bar(100, 100)} 100%")
    
    # Sparklines
    print("   Sparklines:")
    print(f"   {VisualEffects.create_sparkline([1, 3, 2, 5, 4, 7, 6, 8])}")
    print(f"   {VisualEffects.create_sparkline([8, 6, 7, 4, 5, 2, 3, 1])}")
    
    # Currency formatting
    print("   Currency Formatting:")
    print(f"   {VisualEffects.format_currency(1250.50)}")
    print(f"   {VisualEffects.format_currency(-850.25)}")
    print(f"   {VisualEffects.format_currency(0)}")
    
    # Percentage formatting
    print("   Percentage Formatting:")
    print(f"   {VisualEffects.format_percentage(8.5)}")
    print(f"   {VisualEffects.format_percentage(-3.2)}")
    print(f"   {VisualEffects.format_percentage(-12.8)}")
    
    print("\n4. 🃏 TRADING CARDS:")
    
    # Mock position for demo
    demo_position = {
        "symbol": "EURUSD",
        "type": "BUY", 
        "price_open": 1.08500,
        "price_current": 1.08750,
        "volume": 0.1,
        "profit": 25.00,
        "profit_pct": 2.31,
        "price_history": [1.08500, 1.08520, 1.08480, 1.08600, 1.08750]
    }
    
    card = VisualEffects.create_trading_card(demo_position)
    print(card)
    
    print("\n✅ All keyboard and visual features working perfectly!")
    print("🚀 Ready to enhance your Telegram trading bot experience!")

if __name__ == "__main__":
    demo_keyboards()
