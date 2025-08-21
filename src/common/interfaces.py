from abc import ABC, abstractmethod
from typing import Any

class IAnalyzer(ABC):
    """
    Interface for an analysis service that processes market data
    to generate a trading signal.
    """

    @abstractmethod
    async def analyze(self, screenshot_data: bytes, market_context: dict) -> Any:
        """
        Analyzes the provided market data and returns a trading signal.

        Args:
            screenshot_data: The byte content of the market screenshot.
            market_context: A dictionary containing additional context about the market.

        Returns:
            A structured trading signal, or None if no signal is generated.
        """
        pass
