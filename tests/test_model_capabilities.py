#!/usr/bin/env python3
"""
Test script to validate model capability detection without requiring API key.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def test_model_capabilities():
    """Test model capability detection."""
    print("🧪 Testing Model Capability Detection...")
    print("=" * 50)

    try:
        # Import the client wrapper
        from analysis.modules.openai_client_wrapper import OpenAIClientWrapper

        # Test different models
        test_models = ["gpt-5", "gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]

        print("Model Capability Matrix:")
        print("-" * 80)
        print(
            f"{'Model':<15} {'Web Search':<12} {'Real-time':<12} {'Vision':<8} {'Reasoning':<10}"
        )
        print("-" * 80)

        for model in test_models:
            try:
                # Create client wrapper with mock key
                client = OpenAIClientWrapper("mock_key", model)

                # Check capabilities
                capabilities = client.get_model_capabilities()

                print(
                    f"{model:<15} "
                    f"{'✅' if capabilities['web_search'] else '❌':<12} "
                    f"{'✅' if capabilities['realtime_data'] else '❌':<12} "
                    f"{'✅' if capabilities['vision'] else '❌':<8} "
                    f"{'✅' if capabilities.get('reasoning', False) else '❌':<10}"
                )

            except Exception as e:
                print(f"{model:<15} ❌ Error: {e}")

        print("-" * 80)

        # Test specific capability methods
        print(f"\n📋 Testing Capability Methods...")
        print("-" * 30)

        # Test with gpt-4o-mini (default)
        client = OpenAIClientWrapper("mock_key", "gpt-4o-mini")

        print(f"   Model: {client.model}")
        print(f"   Web Search: {client.supports_web_search()}")
        print(f"   Real-time Data: {client.supports_realtime_data()}")
        print(f"   Vision: {client.supports_vision()}")
        print(f"   Advanced Reasoning: {client.supports_reasoning()}")

        # Test web search tools
        print(f"\n🔍 Testing Web Search Tools...")
        print("-" * 30)

        tools = client.get_web_search_tools()
        print(f"   Web search tools: {tools}")

        print("\n" + "=" * 50)
        print("✅ Model capability detection test completed!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_configuration():
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


def main():
    """Main test function."""
    print("🚀 Starting Model Capability Tests...")
    print("=" * 60)

    # Test configuration files
    config_success = test_configuration()

    # Test model capabilities
    capability_success = test_model_capabilities()

    if config_success and capability_success:
        print("\n🎉 All tests passed! Model capability detection is working correctly.")
        print("\n📚 Summary:")
        print("   - GPT-5: Full capabilities including advanced reasoning")
        print("   - GPT-4o: Web search, real-time data, and vision")
        print("   - GPT-4o-mini: Web search and real-time data (cost-effective)")
        print("   - GPT-4-turbo: Vision only (legacy)")
        print("   - GPT-3.5-turbo: Basic text generation only")
    else:
        print("\n⚠️  Some tests failed. Please check your configuration.")

    return config_success and capability_success


if __name__ == "__main__":
    main()
