# OpenAI Model Upgrade Guide

## Overview

This document outlines the recent upgrades to the OpenAI integration in the AI Trading Bot, including support for web search, real-time data access, and enhanced model capabilities.

## Model Capabilities

### Supported Models

| Model | Web Search | Real-time Data | Vision | Advanced Reasoning | Cost | Recommended Use |
|-------|------------|----------------|---------|-------------------|------|-----------------|
| `gpt-5` | ✅ | ✅ | ✅ | ✅ | High | **Premium choice** - Full capabilities including advanced reasoning |
| `gpt-4o-mini` | ✅ | ✅ | ❌ | ❌ | Low | **Default choice** - Best balance of features and cost |
| `gpt-4o` | ✅ | ✅ | ✅ | ❌ | Medium | Full-featured analysis including image processing |
| `gpt-4-turbo` | ❌ | ❌ | ✅ | ❌ | Medium | Image analysis only (no web search) |
| `gpt-3.5-turbo` | ❌ | ❌ | ❌ | ❌ | Low | Basic text generation only |

### Feature Matrix

- **Web Search**: Access to current market data, news, and real-time information
- **Real-time Data**: Live market updates and economic calendar events
- **Vision**: Chart screenshot analysis and image processing
- **Advanced Reasoning**: Complex analysis, multi-step problem solving, and strategic thinking

## Configuration Updates

### Settings YAML

```yaml
# OpenAI Configuration
openai:
  api_key_env: "OPENAI_API_KEY"
  model: "gpt-4o-mini"  # Updated to latest model with web search
  max_tokens: 2000
  temperature: 0.1
  timeout: 30
  tools_enabled: true  # Enable tool usage for web search and real-time data
  web_search_enabled: true  # Enable web search capabilities
  realtime_data_enabled: true  # Enable real-time data access
```

### Environment Variables

```bash
# Required
export OPENAI_API_KEY="your_api_key_here"

# Optional - override defaults
export OPENAI_MODEL="gpt-4o-mini"
export OPENAI_TOOLS_ENABLED="true"
export OPENAI_WEB_SEARCH_ENABLED="true"
export OPENAI_REALTIME_DATA_ENABLED="true"
```

## New Features

### 1. Web Search Integration

The bot now uses OpenAI's built-in web search capabilities to access real-time market data:

```python
# Example: Get current market data with web search
response = await client.create_chat_completion_with_web_search(
    messages=[...],
    search_query="current EURUSD price news sentiment",
    max_tokens=800
)
```

### 2. Real-time Data Provider

Enhanced data provider that leverages web search for current market information:

- **Market Data**: Current prices, news, sentiment
- **Economic Calendar**: Upcoming events and their impact
- **Technical Analysis**: Real-time insights from financial websites

### 3. Model Capability Validation

The system now automatically validates model capabilities before attempting analysis:

```python
# Check if model supports required features
if analyzer.validate_model_for_analysis("image"):
    # Proceed with image analysis
    pass
else:
    # Fall back to text-only analysis
    pass
```

## Usage Examples

### Basic Market Analysis

```python
from src.analysis.openai_analyzer import OpenAIAnalyzer

# Initialize analyzer with web search support
analyzer = OpenAIAnalyzer(
    api_key="your_key",
    model="gpt-4o-mini"  # Supports web search
)

# Analyze market with real-time data
result = await analyzer.analyze_market("EURUSD")
```

### Chart Analysis with Vision

```python
# For image analysis, use gpt-4o
analyzer = OpenAIAnalyzer(
    api_key="your_key",
    model="gpt-4o"  # Supports vision + web search
)

# Analyze chart screenshot
with open("chart.png", "rb") as f:
    screenshot_data = f.read()

result = await analyzer.analyze(screenshot_data, market_context)
```

### Advanced Analysis with GPT-5

```python
# For advanced reasoning and complex analysis, use gpt-5
analyzer = OpenAIAnalyzer(
    api_key="your_key",
    model="gpt-5"  # Supports all features including advanced reasoning
)

# This model can handle complex multi-step analysis
# - Market structure analysis
# - Multi-timeframe confluence
# - Risk assessment with multiple scenarios
# - Strategic position sizing recommendations

result = await analyzer.analyze(screenshot_data, market_context)
```

### Real-time Data Access

```python
from src.analysis.modules.realtime_data_provider import RealtimeDataProvider

provider = RealtimeDataProvider(openai_client)

# Get current market data
market_data = await provider.get_current_market_data(["EURUSD", "GBPUSD"])

# Get economic calendar
calendar = await provider.get_economic_calendar("today", "high")
```

## Testing Your Configuration

Run the configuration test to verify your setup:

```bash
# From project root
python tests/test_openai_config.py
```

This will:
- Verify your API key
- Test different models
- Check capabilities
- Validate configuration
- Provide recommendations

## Migration Guide

### From GPT-4 to GPT-4o-mini

1. **Update Configuration**:
   ```yaml
   # Old
   model: "gpt-4"

   # New
   model: "gpt-4o-mini"
   ```

2. **Enable New Features**:
   ```yaml
   tools_enabled: true
   web_search_enabled: true
   realtime_data_enabled: true
   ```

3. **Test Capabilities**:
   ```bash
   python tests/test_openai_config.py
   ```

### Backward Compatibility

- Old function calling (`functions` parameter) still works
- New tool system (`tools` parameter) is preferred
- Automatic fallback to compatible features

## Performance Considerations

### Model Selection

- **gpt-4o-mini**: Best for most use cases, cost-effective
- **gpt-4o**: Use when image analysis is required
- **gpt-4-turbo**: Legacy model, limited features

### Caching

Real-time data is cached for 5 minutes to reduce API calls and costs.

### Rate Limits

- Web search: Subject to OpenAI's rate limits
- Real-time data: Cached to minimize API usage
- Fallback to mock data when limits are hit

## Troubleshooting

### Common Issues

1. **"Model does not support web search"**
   - Solution: Upgrade to `gpt-4o-mini` or `gpt-4o`

2. **"Web search not available"**
   - Check: API key validity
   - Check: Model supports web search
   - Check: Tools are enabled

3. **"Real-time data unavailable"**
   - Check: Internet connectivity
   - Check: OpenAI API status
   - Check: Rate limits

### Debug Mode

Enable debug logging to see detailed API interactions:

```yaml
logging:
  level: "DEBUG"
```

## Best Practices

1. **Model Selection**: Use `gpt-4o-mini` for most trading analysis
2. **Caching**: Leverage built-in caching for real-time data
3. **Fallbacks**: Always provide fallback data for critical operations
4. **Validation**: Use model capability validation before analysis
5. **Monitoring**: Monitor API usage and costs

## Support

For issues or questions:

1. Check the configuration test: `python tests/test_openai_config.py`
2. Review model capabilities in the logs
3. Verify API key and model settings
4. Check OpenAI API status page

## Future Enhancements

- **Multi-model routing**: Automatic model selection based on task
- **Advanced caching**: Redis-based caching for better performance
- **Cost optimization**: Smart model selection based on budget
- **Real-time streaming**: Live market data streaming
