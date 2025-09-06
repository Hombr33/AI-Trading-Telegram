"""
OpenAI-powered market analyzer for trading signals.
Integrates real-time market data with AI analysis.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..common.interfaces import IAnalyzer
from .modules.openai_client_wrapper import OpenAIClientWrapper
from .modules.prompt_manager import PromptManager
from .modules.real_market_data_provider import RealMarketDataProvider
from .modules.signal_validator import SignalValidator

logger = logging.getLogger(__name__)


class OpenAIAnalyzer(IAnalyzer):
    """OpenAI-powered market analyzer with real-time data integration."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initialize OpenAI analyzer.

        Args:
            api_key: OpenAI API key
            model: OpenAI model to use for analysis
        """
        self.api_key = api_key
        self.model = model

        # Initialize components
        self.client = OpenAIClientWrapper(api_key, model)
        self.realtime_provider = RealMarketDataProvider()  # Use REAL data provider
        self.prompt_manager = PromptManager()
        self.signal_validator = SignalValidator()

        # Validate model capabilities
        self._validate_model_setup()

        logger.info(f"OpenAI Analyzer initialized with model: {model}")

    @property
    def is_available(self) -> bool:
        """Check if analyzer is available.

        Returns:
            True if the analyzer is available and ready to use
        """
        return self.client is not None and self.api_key is not None

    async def test_connection(self) -> bool:
        """Test OpenAI API connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            if not self.client:
                return False

            # Test with a simple completion
            response = await self.client.create_chat_completion(
                messages=[{"role": "user", "content": "Hello"}], max_tokens=10
            )

            return response is not None and response.choices is not None

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def _validate_model_setup(self):
        """Validate model setup and log capabilities."""
        try:
            capabilities = self.client.get_model_capabilities()
            logger.info(f"Model {self.model} capabilities:")
            logger.info(
                f"  - Web Search: {'✅' if capabilities.get('web_search') else '❌'}"
            )
            logger.info(
                f"  - Real-time Data: {'✅' if capabilities.get('realtime_data') else '❌'}"
            )
            logger.info(f"  - Vision: {'✅' if capabilities.get('vision') else '❌'}")
            logger.info(
                f"  - Advanced Reasoning: {'✅' if capabilities.get('reasoning') else '❌'}"
            )

            # Get recommendations for improvement
            recommendations = self._get_model_recommendations(capabilities)
            if recommendations:
                logger.info("Model improvement recommendations:")
                for rec in recommendations:
                    logger.info(f"  - {rec}")

        except Exception as e:
            logger.warning(f"Could not validate model capabilities: {e}")

    def _get_model_recommendations(self, capabilities: Dict[str, bool]) -> List[str]:
        """Get recommendations for model improvements."""
        recommendations = []

        if not capabilities.get("web_search"):
            recommendations.append(
                "Consider upgrading to gpt-4o-mini, gpt-4o, or gpt-5 for web search capabilities"
            )

        if not capabilities.get("realtime_data"):
            recommendations.append(
                "Consider upgrading to gpt-4o-mini, gpt-4o, or gpt-5 for real-time data access"
            )

        if not capabilities.get("vision"):
            recommendations.append(
                "Consider upgrading to gpt-4o or gpt-5 for image analysis capabilities"
            )

        if not capabilities.get("reasoning"):
            recommendations.append(
                "Consider upgrading to gpt-5 for advanced reasoning capabilities"
            )

        return recommendations

    def validate_model_for_analysis(self, analysis_type: str) -> bool:
        """Validate if current model supports the requested analysis type.

        Args:
            analysis_type: Type of analysis (basic, advanced, vision, reasoning)

        Returns:
            True if model supports the analysis type
        """
        capabilities = self.client.get_model_capabilities()

        if analysis_type == "basic":
            return True  # All models support basic analysis

        if analysis_type == "vision" and not capabilities.get("vision"):
            logger.warning(f"Model {self.model} does not support image analysis")
            return False

        if analysis_type == "web_search" and not capabilities.get("web_search"):
            logger.warning(f"Model {self.model} does not support web search")
            return False

        if analysis_type == "reasoning" and not capabilities.get("reasoning"):
            logger.warning(f"Model {self.model} does not support advanced reasoning")
            return False

        return True

    async def analyze(
        self,
        market_context: Dict[str, Any],
        analysis_type: str = "basic",
        image_data: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """Analyze market and generate trading signals using REAL data.

        Args:
            market_context: Market context including symbols, timeframes, etc.
            analysis_type: Type of analysis to perform
            image_data: Optional chart image for analysis

        Returns:
            Analysis results with trading signals
        """
        try:
            # Validate model capabilities
            if not self.validate_model_for_analysis(analysis_type):
                logger.warning(
                    f"Model {self.model} does not support {analysis_type} analysis"
                )
                return self._get_fallback_response(
                    market_context, "Model capability not supported"
                )

            # Get REAL market data (not fake data)
            symbols = market_context.get("symbols", [])
            if not symbols:
                return self._get_fallback_response(
                    market_context, "No symbols specified"
                )

            logger.info(f"Starting analysis for symbols: {symbols}")

            # Fetch REAL market data using the new provider
            real_market_data = await self.realtime_provider.get_current_market_data(
                symbols
            )
            logger.info(f"Real market data fetched: {len(real_market_data)} characters")

            # Validate that we got real data, not fake data
            if self._is_fake_data(real_market_data):
                logger.error("Received fake data instead of real market data!")
                return self._get_fallback_response(
                    market_context, "Real data provider failed"
                )

            # Create analysis prompt with REAL data
            analysis_prompt = self.prompt_manager.create_analysis_prompt(
                market_context=market_context, realtime_data=real_market_data
            )

            # Generate signal using OpenAI
            signal_data = await self._generate_signal_with_real_data(
                analysis_prompt=analysis_prompt,
                image_data=image_data,
                market_context=market_context,
            )

            if signal_data:
                # Validate the generated signal
                validation_result = self.signal_validator.validate_signal(signal_data)

                # Handle tuple return (validated_signal, validation_errors)
                if isinstance(validation_result, tuple) and len(validation_result) == 2:
                    validated_signal, validation_errors = validation_result

                    if validated_signal and not validation_errors:
                        logger.info("Signal generated and validated successfully")
                        return {
                            "status": "success",
                            "analysis_type": analysis_type,
                            "symbols": symbols,
                            "market_data": real_market_data,
                            "signal": signal_data,
                            "validation": {"is_valid": True, "errors": []},
                            "timestamp": datetime.now().isoformat(),
                            "model_used": self.model,
                            "data_source": "REAL_MARKET_APIS",
                        }
                    else:
                        logger.warning(f"Signal validation failed: {validation_errors}")
                        return self._get_fallback_response(
                            market_context,
                            f"Signal validation failed: {validation_errors}",
                            original_signal=signal_data,
                            market_data=real_market_data,
                        )
                else:
                    # Handle case where validation_result is not a tuple
                    logger.warning("Unexpected validation result format")
                    return self._get_fallback_response(
                        market_context,
                        "Signal validation format error",
                        original_signal=signal_data,
                        market_data=real_market_data,
                    )
            else:
                logger.warning("Failed to generate signal with real data")
                return self._get_fallback_response(
                    market_context,
                    "Signal generation failed",
                    original_signal=signal_data,
                    market_data=real_market_data,
                )

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return self._get_fallback_response(
                market_context,
                f"Analysis error: {e}",
                original_signal=signal_data,
                market_data=real_market_data,
            )

    def _is_fake_data(self, market_data: str) -> bool:
        """Check if the market data is fake or real."""
        if not market_data:
            return True

        # Check for fake data indicators
        fake_indicators = [
            "mock",
            "fake",
            "sample",
            "testing",
            "placeholder",
            "august 24, 2025",
            "2025-08-24",  # Future dates
            "29,450",
            "30,200",
            "28,750",  # Wrong BTC prices
            "35,750",
            "36,500",  # Wrong BTC prices
        ]

        data_lower = market_data.lower()
        fake_indicators_found = sum(
            1 for indicator in fake_indicators if indicator in data_lower
        )

        # If we find multiple fake indicators, it's likely fake data
        return fake_indicators_found >= 2

    async def _generate_signal_with_real_data(
        self,
        analysis_prompt: str,
        image_data: Optional[bytes],
        market_context: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Generate trading signal using real market data."""
        try:
            # Use the client to generate structured signal
            signal_data = await self.client.generate_structured_signal(
                system_prompt=self.prompt_manager.get_system_prompt(),
                analysis_prompt=analysis_prompt,
                signal_schema=self.prompt_manager.get_signal_schema(),
                image_data=image_data,
            )

            if signal_data:
                logger.info("Signal generated successfully with real data")
                return signal_data
            else:
                logger.warning("No signal data generated")
                return None

        except Exception as e:
            logger.error(f"Error generating signal with real data: {e}")
            return None

    def _get_fallback_response(
        self,
        market_context: Dict[str, Any],
        reason: str,
        original_signal: Optional[Dict[str, Any]] = None,
        market_data: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get fallback response when analysis fails, preserving original signal data for manual trading."""
        fallback_response = {
            "status": "error",
            "reason": reason,
            "symbols": market_context.get("symbols", []),
            "timestamp": datetime.now().isoformat(),
            "model_used": self.model,
            "data_source": "FALLBACK",
            "warning": "This is a fallback response due to analysis failure",
        }

        # Preserve original signal data if available, so users can still see intended levels
        if original_signal:
            fallback_response["original_signal"] = original_signal
            fallback_response["preserved_data"] = True
            fallback_response["manual_trading_available"] = True

        # Preserve market data if available
        if market_data:
            fallback_response["market_data"] = market_data

        return fallback_response

    async def get_market_data(self, symbols: List[str]) -> str:
        """Get real market data for specified symbols."""
        try:
            return await self.realtime_provider.get_current_market_data(symbols)
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            return f"Error fetching market data: {e}"

    async def get_economic_calendar(
        self, timeframe: str = "today", impact_level: str = "high"
    ) -> str:
        """Get economic calendar data."""
        try:
            return await self.realtime_provider.get_economic_calendar(
                timeframe, impact_level
            )
        except Exception as e:
            logger.error(f"Failed to get economic calendar: {e}")
            return f"Error fetching economic calendar: {e}"

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        capabilities = self.client.get_model_capabilities()
        return {
            "model": self.model,
            "capabilities": capabilities,
            "recommendations": self._get_model_recommendations(capabilities),
        }

    async def close(self):
        """Clean up resources."""
        try:
            if hasattr(self.realtime_provider, "close"):
                await self.realtime_provider.close()
            logger.info("OpenAI Analyzer resources cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
