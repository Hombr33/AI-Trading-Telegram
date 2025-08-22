import base64
import json
import logging
from typing import Any

import openai
from pydantic import ValidationError

from src.common.interfaces import IAnalyzer
from src.api.models import SignalResponse
from src.core.config import AppConfig

# Configure logging
logger = logging.getLogger(__name__)


class OpenAIAnalyzer(IAnalyzer):
    """
    An analyzer that uses OpenAI's GPT models to analyze market screenshots.
    """

    def __init__(self, config: AppConfig):
        """Initialize the OpenAI analyzer with configuration."""
        self.api_key = config.openai.api_key
        if not self.api_key:
            raise ValueError("OpenAI API key not configured.")
        self.client = openai.AsyncOpenAI(api_key=self.api_key)
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Loads the detailed system prompt from the JSON file."""
        try:
            prompt_path = os.path.join(
                os.path.dirname(__file__), "app-code-prompt.json"
            )
            with open(prompt_path, "r") as f:
                prompt_data = json.load(f)
            # We can construct a more targeted system message here if needed
            return json.dumps(prompt_data)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Could not load or parse app-code-prompt.json: {e}")
            # Fallback to a simple instruction if the file is missing/corrupt
            return "You are a financial market analyst. Analyze the provided image and return a trading signal in JSON format."

    async def analyze(self, screenshot_data: bytes, market_context: dict) -> Any:
        """
        Analyzes the market data using OpenAI's vision capabilities.

        Returns:
            A validated SignalResponse object or None.
        """
        logger.info("Starting OpenAI analysis...")
        base64_image = base64.b64encode(screenshot_data).decode("utf-8")

        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Analyze this chart screenshot within the following market context and provide a trading signal in JSON format according to the 'signal_schema'. Market context: {json.dumps(market_context)}",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                },
            ],
        }

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4o for its vision and JSON mode capabilities
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    user_message,
                ],
                response_format={"type": "json_object"},
                max_tokens=1500,
            )

            response_content = response.choices[0].message.content
            if not response_content:
                logger.warning("OpenAI response was empty.")
                return None

            # The response is a JSON string, so we parse it.
            signal_data = json.loads(response_content)

            # Validate the data with our Pydantic model
            # Assuming the direct output matches SignalResponse structure.
            # This might need adjustment if the AI nests it under a key.
            validated_signal = SignalResponse(**signal_data)
            logger.info(
                f"Successfully received and validated signal for {validated_signal.symbol}"
            )
            return validated_signal

        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from OpenAI response: {e}")
            logger.error(f"Raw response content: {response_content}")
            return None
        except ValidationError as e:
            logger.error(f"Failed to validate signal data against Pydantic model: {e}")
            logger.error(f"Received data: {signal_data}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during analysis: {e}")
            return None
