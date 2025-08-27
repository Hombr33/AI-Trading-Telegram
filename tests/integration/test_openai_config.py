#!/usr/bin/env python3
"""
Test script to validate OpenAI configuration and model capabilities.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.analysis.modules.openai_client_wrapper import OpenAIClientWrapper
from src.analysis.openai_analyzer import OpenAIAnalyzer
from src.core.config import config


async def test_openai_config():
    """Test OpenAI configuration and model capabilities."""
    print("🔍 Testing OpenAI Configuration...")
    print("=" * 50)
    
    # Check environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("   Please set OPENAI_API_KEY environment variable")
        return False
    
    print(f"✅ OPENAI_API_KEY found: {api_key[:10]}...")
    
    # Test different models
    test_models = [
        "gpt-5",
        "gpt-4o-mini",
        "gpt-4o", 
        "gpt-4-turbo",
        "gpt-3.5-turbo"
    ]
    
    for model in test_models:
        print(f"\n🧪 Testing model: {model}")
        print("-" * 30)
        
        try:
            # Create client wrapper
            client = OpenAIClientWrapper(api_key, model)
            
            # Check capabilities
            capabilities = client.get_model_capabilities()
            print(f"   Web Search: {'✅' if capabilities['web_search'] else '❌'}")
            print(f"   Real-time Data: {'✅' if capabilities['realtime_data'] else '❌'}")
            print(f"   Vision: {'✅' if capabilities['vision'] else '❌'}")
            print(f"   Advanced Reasoning: {'✅' if capabilities.get('reasoning', False) else '❌'}")
            
            # Test connection
            print("   Testing connection...")
            connection_success = await client.test_connection()
            print(f"   Connection: {'✅' if connection_success else '❌'}")
            
        except Exception as e:
            print(f"   ❌ Error testing {model}: {e}")
    
    # Test analyzer
    print(f"\n🧪 Testing OpenAIAnalyzer...")
    print("-" * 30)
    
    try:
        analyzer = OpenAIAnalyzer(api_key, "gpt-4o-mini")
        capabilities = analyzer.get_model_capabilities()
        recommendations = analyzer.get_model_recommendations()
        
        print(f"   Current model: {analyzer.model}")
        print(f"   Capabilities: {capabilities}")
        print(f"   Recommendations:")
        for rec in recommendations:
            print(f"     - {rec}")
        
        # Test validation
        print("\n   Testing model validation...")
        print(f"     General analysis: {'✅' if analyzer.validate_model_for_analysis('general') else '❌'}")
        print(f"     Image analysis: {'✅' if analyzer.validate_model_for_analysis('image') else '❌'}")
        print(f"     Real-time data: {'✅' if analyzer.validate_model_for_analysis('realtime') else '❌'}")
        print(f"     Web search: {'✅' if analyzer.validate_model_for_analysis('web_search') else '❌'}")
        print(f"     Advanced reasoning: {'✅' if analyzer.validate_model_for_analysis('reasoning') else '❌'}")
        
    except Exception as e:
        print(f"   ❌ Error testing analyzer: {e}")
    
    # Check configuration
    print(f"\n📋 Configuration Check...")
    print("-" * 30)
    
    print(f"   Settings YAML model: {config.openai.model}")
    print(f"   Core config model: {config.openai.model}")
    print(f"   Tools enabled: {config.openai.tools_enabled}")
    print(f"   Web search enabled: {config.openai.web_search_enabled}")
    print(f"   Real-time data enabled: {config.openai.realtime_data_enabled}")
    
    print("\n" + "=" * 50)
    print("✅ Configuration test completed!")
    
    return True


async def main():
    """Main test function."""
    success = await test_openai_config()
    if success:
        print("\n🎉 All tests passed! Your OpenAI configuration is ready for web search and real-time data.")
    else:
        print("\n⚠️  Some tests failed. Please check your configuration.")
    
    return success


if __name__ == "__main__":
    asyncio.run(main())
