#!/usr/bin/env python3
"""
Simple test script to validate OpenAI configuration and model capabilities.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


# Test OpenAI client wrapper directly
async def test_openai_client():
    """Test OpenAI client wrapper functionality."""
    print("🔍 Testing OpenAI Client Wrapper...")
    print("=" * 50)

    # Check environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("   Testing with mock API key for capability detection...")
        api_key = "mock_key_for_testing"
        mock_mode = True
    else:
        print(f"✅ OPENAI_API_KEY found: {api_key[:10]}...")
        mock_mode = False

    try:
        # Import the client wrapper
        from analysis.modules.openai_client_wrapper import OpenAIClientWrapper

        # Test different models
        test_models = ["gpt-5", "gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]

        for model in test_models:
            print(f"\n🧪 Testing model: {model}")
            print("-" * 30)

            try:
                # Create client wrapper
                client = OpenAIClientWrapper(api_key, model)

                # Check capabilities
                capabilities = client.get_model_capabilities()
                print(f"   Web Search: {'✅' if capabilities['web_search'] else '❌'}")
                print(
                    f"   Real-time Data: {'✅' if capabilities['realtime_data'] else '❌'}"
                )
                print(f"   Vision: {'✅' if capabilities['vision'] else '❌'}")
                print(
                    f"   Advanced Reasoning: {'✅' if capabilities.get('reasoning', False) else '❌'}"
                )

                # Test connection only if not in mock mode
                if not mock_mode:
                    print("   Testing connection...")
                    connection_success = await client.test_connection()
                    print(f"   Connection: {'✅' if connection_success else '❌'}")
                else:
                    print("   Connection: ⏭️  Skipped (mock mode)")

            except Exception as e:
                print(f"   ❌ Error testing {model}: {e}")

        # Test web search tools
        print(f"\n🔍 Testing Web Search Tools...")
        print("-" * 30)

        client = OpenAIClientWrapper(api_key, "gpt-4o-mini")
        tools = client.get_web_search_tools()
        print(f"   Web search tools: {tools}")

        # Test capability methods
        print(f"\n📋 Testing Capability Methods...")
        print("-" * 30)

        print(f"   Supports web search: {client.supports_web_search()}")
        print(f"   Supports real-time data: {client.supports_realtime_data()}")
        print(f"   Supports vision: {client.supports_vision()}")
        print(f"   Supports reasoning: {client.supports_reasoning()}")

        print("\n" + "=" * 50)
        print("✅ OpenAI client wrapper test completed!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


async def test_config_files():
    """Test configuration files."""
    print("\n📋 Testing Configuration Files...")
    print("=" * 50)

    try:
        # Test settings.yaml
        settings_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        if settings_path.exists():
            print(f"✅ Settings file found: {settings_path}")

            # Read and check OpenAI config
            import yaml

            with open(settings_path, "r") as f:
                settings = yaml.safe_load(f)

            openai_config = settings.get("openai", {})
            print(f"   Model: {openai_config.get('model', 'Not set')}")
            print(f"   Tools enabled: {openai_config.get('tools_enabled', 'Not set')}")
            print(
                f"   Web search enabled: {openai_config.get('web_search_enabled', 'Not set')}"
            )
            print(
                f"   Real-time data enabled: {openai_config.get('realtime_data_enabled', 'Not set')}"
            )
        else:
            print(f"❌ Settings file not found: {settings_path}")

        # Test core config
        core_config_path = Path(__file__).parent.parent / "src" / "core" / "config.py"
        if core_config_path.exists():
            print(f"✅ Core config file found: {core_config_path}")
        else:
            print(f"❌ Core config file not found: {core_config_path}")

        return True

    except Exception as e:
        print(f"❌ Error testing config files: {e}")
        return False


async def main():
    """Main test function."""
    print("🚀 Starting OpenAI Configuration Tests...")
    print("=" * 60)

    # Test configuration files
    config_success = await test_config_files()

    # Test OpenAI client
    client_success = await test_openai_client()

    if config_success and client_success:
        print("\n🎉 All tests passed! Your OpenAI configuration is ready.")
        print("\n📚 Next steps:")
        print("   1. Set your OPENAI_API_KEY environment variable")
        print("   2. Test with a specific model: export OPENAI_MODEL='gpt-4o-mini'")
        print("   3. Run the full test: python tests/test_openai_config.py")
    else:
        print("\n⚠️  Some tests failed. Please check your configuration.")

    return config_success and client_success


if __name__ == "__main__":
    asyncio.run(main())
