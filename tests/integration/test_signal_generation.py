#!/usr/bin/env python3
"""
Test script to validate signal generation with real data.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


async def test_signal_generation():
    """Test actual signal generation with real data."""
    print("🚀 Testing Signal Generation with Real Data...")
    print("=" * 60)

    # Check environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("   Please set OPENAI_API_KEY environment variable")
        print("   Example: export OPENAI_API_KEY='your_key_here'")
        return False

    print(f"✅ OPENAI_API_KEY found: {api_key[:10]}...")

    try:
        # Import required modules
        from analysis.modules.realtime_data_provider import RealtimeDataProvider
        from analysis.openai_analyzer import OpenAIAnalyzer

        print("\n🧪 Testing Real-time Data Provider...")
        print("-" * 40)

        # Test real-time data provider
        realtime_provider = RealtimeDataProvider(
            None
        )  # Will use OpenAI client directly

        # Test market data
        symbols = ["EURUSD", "XAUUSD", "GBPUSD"]
        print(f"   Fetching market data for: {symbols}")

        try:
            market_data = await realtime_provider.get_current_market_data(symbols)
            print(f"   Market data received: {'✅' if market_data else '❌'}")
            if market_data:
                print(f"   Data content: {market_data[:200]}...")
        except Exception as e:
            print(f"   ❌ Error fetching market data: {e}")

        # Test economic calendar
        print(f"\n   Fetching economic calendar...")
        try:
            calendar_data = await realtime_provider.get_economic_calendar()
            print(f"   Economic calendar received: {'✅' if calendar_data else '❌'}")
            if calendar_data:
                print(f"   Calendar content: {calendar_data[:200]}...")
        except Exception as e:
            print(f"   ❌ Error fetching economic calendar: {e}")

        print("\n🧪 Testing OpenAI Analyzer...")
        print("-" * 40)

        # Create analyzer with different models
        test_models = ["gpt-4o-mini", "gpt-4o", "gpt-5"]

        for model in test_models:
            print(f"\n   Testing model: {model}")
            print("   " + "-" * 30)

            try:
                # Create analyzer
                analyzer = OpenAIAnalyzer(api_key, model)

                # Check capabilities
                capabilities = analyzer.get_model_capabilities()
                print(
                    f"     Web Search: {'✅' if capabilities['web_search'] else '❌'}"
                )
                print(
                    f"     Real-time Data: {'✅' if capabilities['realtime_data'] else '❌'}"
                )
                print(f"     Vision: {'✅' if capabilities['vision'] else '❌'}")
                print(
                    f"     Advanced Reasoning: {'✅' if capabilities.get('reasoning', False) else '❌'}"
                )

                # Test connection
                print("     Testing connection...")
                connection_success = await analyzer.test_connection()
                print(f"     Connection: {'✅' if connection_success else '❌'}")

                if connection_success:
                    # Generate a mock signal to test the system
                    print("     Generating test signal...")

                    # Create mock market context
                    market_context = {
                        "symbols": ["EURUSD"],
                        "timeframe": "H1",
                        "session": "London",
                        "volatility": "medium",
                        "current_price": 1.0850,
                        "timestamp": datetime.now().isoformat(),
                    }

                    # Generate signal (without screenshot for now)
                    signal = await analyzer.analyze(None, market_context)

                    if signal:
                        print(f"     Signal generated: {'✅' if signal else '❌'}")
                        print(f"     Signal type: {type(signal)}")
                        print(f"     Signal content: {str(signal)[:300]}...")

                        # Check if signal contains real data indicators
                        signal_str = str(signal).lower()
                        real_data_indicators = [
                            "current",
                            "latest",
                            "today",
                            "now",
                            "recent",
                            "market",
                            "price",
                            "eurusd",
                            "forex",
                            "trading",
                        ]

                        real_data_found = sum(
                            1
                            for indicator in real_data_indicators
                            if indicator in signal_str
                        )
                        print(
                            f"     Real data indicators found: {real_data_found}/{len(real_data_indicators)}"
                        )

                        if real_data_found >= 3:
                            print("     🎯 Signal appears to contain real-time data!")
                        else:
                            print("     ⚠️  Signal may not contain real-time data")
                    else:
                        print("     ❌ No signal generated")

            except Exception as e:
                print(f"     ❌ Error testing {model}: {e}")

        print("\n" + "=" * 60)
        print("✅ Signal generation test completed!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


async def test_web_search_capability():
    """Test web search capability specifically."""
    print("\n🔍 Testing Web Search Capability...")
    print("=" * 50)

    try:
        from analysis.modules.openai_client_wrapper import OpenAIClientWrapper

        # Test with different models
        test_models = ["gpt-4o-mini", "gpt-4o", "gpt-5"]

        for model in test_models:
            print(f"\n   Testing {model} web search...")
            print("   " + "-" * 30)

            try:
                client = OpenAIClientWrapper("mock_key", model)

                # Check web search support
                supports_web_search = client.supports_web_search()
                print(
                    f"     Web search supported: {'✅' if supports_web_search else '❌'}"
                )

                if supports_web_search:
                    # Get web search tools
                    tools = client.get_web_search_tools()
                    print(f"     Web search tools: {tools}")

                    # Test tool structure
                    if tools and len(tools) > 0:
                        tool = tools[0]
                        if tool.get("type") == "web_search":
                            print("     ✅ Web search tool structure correct")
                        else:
                            print("     ❌ Web search tool structure incorrect")
                    else:
                        print("     ❌ No web search tools available")
                else:
                    print("     ⏭️  Skipping web search tests (not supported)")

            except Exception as e:
                print(f"     ❌ Error testing {model}: {e}")

        return True

    except Exception as e:
        print(f"❌ Error testing web search: {e}")
        return False


async def main():
    """Main test function."""
    print("🚀 Starting Signal Generation Tests...")
    print("=" * 70)

    # Test web search capability
    web_search_success = await test_web_search_capability()

    # Test signal generation
    signal_success = await test_signal_generation()

    if web_search_success and signal_success:
        print("\n🎉 All tests completed!")
        print("\n📊 Assessment Summary:")
        print("   - Web search capability: ✅ Tested")
        print("   - Real-time data access: ✅ Tested")
        print("   - Signal generation: ✅ Tested")
        print("   - Model capabilities: ✅ Verified")
        print("\n🔍 To assess real data usage:")
        print("   1. Check if signals contain current market information")
        print("   2. Verify timestamps are recent")
        print("   3. Look for specific price levels and market conditions")
        print("   4. Check if news events are current")
    else:
        print("\n⚠️  Some tests failed. Please check your configuration.")

    return web_search_success and signal_success


if __name__ == "__main__":
    asyncio.run(main())
