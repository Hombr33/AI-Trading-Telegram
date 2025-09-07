"""
OpenAI client wrapper module for enhanced functionality.
Handles OpenAI API interactions with proper error handling and retry logic.
"""

import asyncio
import base64
import json
import logging
from typing import Any, Dict, List, Optional, Union

import openai
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class OpenAIClientWrapper:
    """Wrapper for OpenAI client with enhanced functionality."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", max_retries: int = 3):
        """Initialize OpenAI client wrapper.

        Args:
            api_key: OpenAI API key
            model: Model to use for completions (default: gpt-4o-mini for web search)
            max_retries: Maximum number of retries for failed requests
        """
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None

        # Define available models with their capabilities
        self.model_capabilities = {
            "gpt-5": {
                "web_search": True,
                "realtime_data": True,
                "vision": True,
                "reasoning": True,
            },
            "gpt-4o": {"web_search": True, "realtime_data": True, "vision": True},
            "gpt-4o-mini": {"web_search": True, "realtime_data": True, "vision": False},
            "gpt-4-turbo": {
                "web_search": False,
                "realtime_data": False,
                "vision": True,
            },
            "gpt-3.5-turbo": {
                "web_search": False,
                "realtime_data": False,
                "vision": False,
            },
        }

        if not self.client:
            logger.warning("OpenAI client not initialized - API key missing")

    async def create_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[Union[str, Dict[str, str]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.3,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, str]]] = None,
    ) -> Optional[Any]:
        """Create chat completion with retry logic and tool support.

        Args:
            messages: List of messages for the conversation
            functions: Optional list of functions for function calling (deprecated, use tools)
            function_call: Optional function call specification (deprecated, use tool_choice)
            response_format: Optional response format specification
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            tools: Optional list of tools (including web search)
            tool_choice: Optional tool choice specification

        Returns:
            OpenAI response object or None if failed
        """
        if not self.client:
            logger.error("OpenAI client not available")
            return None

        for attempt in range(self.max_retries):
            try:
                # Prepare request parameters
                params = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens or 2000,
                    "temperature": temperature,
                }

                # Add tools if supported and provided
                if tools and self.supports_web_search():
                    params["tools"] = tools
                    if tool_choice:
                        params["tool_choice"] = tool_choice
                elif functions and not tools:  # Backward compatibility
                    params["functions"] = functions
                    if function_call:
                        params["function_call"] = function_call

                # Add response format if specified
                if response_format:
                    params["response_format"] = response_format

                # Make the API call
                response = await self.client.chat.completions.create(**params)

                logger.info(f"OpenAI API call successful (attempt {attempt + 1})")
                return response

            except openai.RateLimitError as e:
                wait_time = (attempt + 1) * 2  # Exponential backoff
                logger.warning(
                    f"Rate limit hit (attempt {attempt + 1}), waiting {wait_time}s: {e}"
                )
                await asyncio.sleep(wait_time)

            except openai.APIError as e:
                if attempt == self.max_retries - 1:
                    logger.error(
                        f"OpenAI API error after {self.max_retries} attempts: {e}"
                    )
                    return None
                else:
                    wait_time = (attempt + 1) * 1
                    logger.warning(
                        f"API error (attempt {attempt + 1}), retrying in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)

            except Exception as e:
                logger.error(f"Unexpected error in OpenAI API call: {e}")
                return None

        return None

    async def analyze_image_with_context(
        self,
        image_data: bytes,
        system_prompt: str,
        user_prompt: str,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Analyze image with text context using vision model.

        Args:
            image_data: Image data as bytes
            system_prompt: System prompt for context
            user_prompt: User prompt for analysis
            response_format: Optional structured response format

        Returns:
            Analysis result or None if failed
        """
        if not self.client:
            logger.error("OpenAI client not available for image analysis")
            return None

        try:
            # Encode image to base64
            base64_image = base64.b64encode(image_data).decode("utf-8")

            # Prepare messages
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            },
                        },
                    ],
                },
            ]

            # Make API call
            response = await self.create_chat_completion(
                messages=messages, response_format=response_format, max_tokens=2000
            )

            if response and response.choices:
                content = response.choices[0].message.content
                logger.info("Image analysis completed successfully")
                return content
            else:
                logger.error("No response from image analysis")
                return None

        except Exception as e:
            logger.error(f"Error in image analysis: {e}")
            return None

    async def search_realtime_data(
        self, query: str, max_tokens: int = 800
    ) -> Optional[str]:
        """Search for real-time data using OpenAI.

        Args:
            query: Search query
            max_tokens: Maximum tokens in response

        Returns:
            Search results or None if failed
        """
        if not self.client:
            logger.error("OpenAI client not available for real-time search")
            return None

        messages = [
            {
                "role": "system",
                "content": """You are a financial data analyst. Analyze the market and provide a trading signal in the following JSON format:

{
    "action": "BUY|SELL|HOLD",
    "entry_price": current_market_price,
    "stop_loss": recommended_stop_loss,
    "take_profit": recommended_take_profit,
    "confidence": confidence_score_1_to_10,
    "risk_level": "LOW|MEDIUM|HIGH",
    "reasoning": "detailed_explanation_with_current_market_context"
}

Focus on specific price levels, recent movements, and relevant news. Return ONLY the JSON, no additional text.""",
            },
            {"role": "user", "content": query},
        ]

        # Use simple JSON response format
        response = await self.create_chat_completion(
            messages=messages, max_tokens=max_tokens, temperature=0.3
        )

        if response and response.choices:
            content = response.choices[0].message.content
            logger.info("Real-time data search completed")
            return content

        logger.warning("No response from real-time data search")
        return None

    async def generate_structured_signal(
        self,
        system_prompt: str,
        analysis_prompt: str,
        signal_schema: Dict[str, Any],
        image_data: Optional[bytes] = None,
    ) -> Optional[Dict[str, Any]]:
        """Generate structured trading signal.

        Args:
            system_prompt: System prompt with trading rules
            analysis_prompt: Analysis prompt with market context
            signal_schema: JSON schema for signal structure
            image_data: Optional chart image data

        Returns:
            Structured signal data or None if failed
        """
        if not self.client:
            logger.error("OpenAI client not available for signal generation")
            return None

        try:
            # Prepare messages
            if image_data:
                # Include image analysis
                base64_image = base64.b64encode(image_data).decode("utf-8")
                messages = [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": analysis_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                },
                            },
                        ],
                    },
                ]
            else:
                # Text-only analysis
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": analysis_prompt},
                ]

            # Make API call without response_format to avoid schema validation errors
            response = await self.create_chat_completion(
                messages=messages, max_tokens=2000, temperature=0.3
            )

            if response and response.choices:
                content = response.choices[0].message.content
                if content:
                    try:
                        # Clean markdown formatting if present
                        cleaned_content = self._extract_json_from_response(content)

                        # Log the cleaned content for debugging
                        logger.debug(f"Cleaned content: {cleaned_content[:200]}...")

                        # Try to parse the JSON
                        signal_data = json.loads(cleaned_content)
                        logger.info("Structured signal generated successfully")
                        return signal_data
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse signal JSON: {e}")
                        logger.error(f"Raw response content: {content[:500]}...")
                        logger.error(f"Cleaned content: {cleaned_content[:500]}...")

                        # Try to fix common JSON issues
                        fixed_content = self._fix_common_json_issues(cleaned_content)
                        if fixed_content != cleaned_content:
                            try:
                                signal_data = json.loads(fixed_content)
                                logger.info(
                                    "Signal generated successfully after JSON fixing"
                                )
                                return signal_data
                            except json.JSONDecodeError as e2:
                                logger.error(f"JSON fixing failed: {e2}")

                        return None
                else:
                    logger.error("Empty response from signal generation")
                    return None
            else:
                logger.error("No response from signal generation")
                return None

        except Exception as e:
            logger.error(f"Error in structured signal generation: {e}")
            return None

    def _extract_json_from_response(self, content: str) -> str:
        """Extract JSON from response with robust error handling.

        Args:
            content: Raw response content that may contain markdown formatting

        Returns:
            Cleaned JSON string
        """
        if not content:
            return ""

        # Remove markdown code blocks if present
        if "```json" in content:
            # Extract content between ```json and ```
            start_marker = "```json"
            end_marker = "```"

            start_index = content.find(start_marker)
            if start_index != -1:
                start_index += len(start_marker)
                end_index = content.find(end_marker, start_index)
                if end_index != -1:
                    json_content = content[start_index:end_index].strip()
                    return json_content

        # Handle generic code blocks
        elif "```" in content:
            lines = content.split("\n")
            in_code_block = False
            json_lines = []

            for line in lines:
                if line.strip().startswith("```"):
                    if in_code_block:
                        break  # End of code block
                    else:
                        in_code_block = True  # Start of code block
                        continue
                elif in_code_block:
                    json_lines.append(line)

            if json_lines:
                return "\n".join(json_lines).strip()

        # Try to find JSON object boundaries
        content = content.strip()

        # Look for opening and closing braces
        start_brace = content.find("{")
        end_brace = content.rfind("}")

        if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
            json_content = content[start_brace : end_brace + 1]

            # Validate that this looks like JSON
            if self._looks_like_json(json_content):
                return json_content

        # Return content as-is if no better extraction method worked
        return content.strip()

    def _looks_like_json(self, content: str) -> bool:
        """Check if content looks like valid JSON.

        Args:
            content: Content to check

        Returns:
            True if content looks like JSON
        """
        if not content:
            return False

        # Basic JSON structure checks
        content = content.strip()

        # Must start with { and end with }
        if not (content.startswith("{") and content.endswith("}")):
            return False

        # Must contain basic JSON elements
        if not any(
            keyword in content for keyword in ['"id"', '"symbol"', '"bias"', '"setups"']
        ):
            return False

        # Check for balanced braces
        brace_count = 0
        for char in content:
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count < 0:
                    return False

        return brace_count == 0

    def _fix_common_json_issues(self, content: str) -> str:
        """Fix common JSON formatting issues.

        Args:
            content: JSON content that may have formatting issues

        Returns:
            Fixed JSON content
        """
        if not content:
            return content

        fixed = content

        # Fix trailing commas
        fixed = fixed.replace(",}", "}")
        fixed = fixed.replace(",]", "]")

        # Fix comma-separated numbers (e.g., 113,600.00 -> 113600.00)
        import re

        # Find numbers with commas and remove them
        pattern = r"(\d+),(\d+(?:\.\d+)?)"
        fixed = re.sub(pattern, r"\1\2", fixed)

        # Fix missing quotes around property names
        # Find property names that don't have quotes and add them
        pattern = r"(\s*)(\w+)(\s*):"
        fixed = re.sub(pattern, r'\1"\2"\3:', fixed)

        # Fix single quotes to double quotes
        fixed = fixed.replace("'", '"')

        # Fix unescaped quotes in string values
        # This is a simple approach - in production you'd want more sophisticated handling
        lines = fixed.split("\n")
        fixed_lines = []

        for line in lines:
            # Skip lines that are just braces or brackets
            if line.strip() in ["{", "}", "[", "]", "{", "}"]:
                fixed_lines.append(line)
                continue

            # Handle lines with string values
            if ":" in line and '"' in line:
                # Find the colon position
                colon_pos = line.find(":")
                key_part = line[:colon_pos].strip()
                value_part = line[colon_pos:].strip()

                # Ensure key has quotes
                if not key_part.startswith('"'):
                    # Clean the key part and add quotes
                    clean_key = key_part.strip().strip("\"'")
                    key_part = f'"{clean_key}"'

                # Handle value part
                if value_part.startswith(":"):
                    value_part = value_part[1:].strip()

                # Reconstruct the line
                fixed_line = f"    {key_part}: {value_part}"
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)

        fixed = "\n".join(fixed_lines)

        return fixed

    def is_available(self) -> bool:
        """Check if OpenAI client is available.

        Returns:
            True if client is available, False otherwise
        """
        return self.client is not None

    def get_model(self) -> str:
        """Get current model name.

        Returns:
            Model name
        """
        return self.model

    def set_model(self, model: str):
        """Set model for completions.

        Args:
            model: Model name to use
        """
        self.model = model
        logger.info(f"OpenAI model set to: {model}")

    async def test_connection(self) -> bool:
        """Test OpenAI API connection.

        Returns:
            True if connection successful, False otherwise
        """
        if not self.client:
            return False

        try:
            response = await self.create_chat_completion(
                messages=[{"role": "user", "content": "Hello"}], max_tokens=10
            )

            if response and response.choices:
                logger.info("OpenAI connection test successful")
                return True
            else:
                logger.error("OpenAI connection test failed - no response")
                return False

        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False

    def get_model_capabilities(self) -> Dict[str, bool]:
        """Get capabilities for the current model.

        Returns:
            Dictionary of model capabilities
        """
        return self.model_capabilities.get(
            self.model, {"web_search": False, "realtime_data": False, "vision": False}
        )

    def supports_web_search(self) -> bool:
        """Check if current model supports web search.

        Returns:
            True if web search is supported
        """
        return self.get_model_capabilities().get("web_search", False)

    def supports_realtime_data(self) -> bool:
        """Check if current model supports real-time data.

        Returns:
            True if real-time data is supported
        """
        return self.get_model_capabilities().get("realtime_data", False)

    def supports_vision(self) -> bool:
        """Check if current model supports vision (image analysis).

        Returns:
            True if vision is supported
        """
        return self.get_model_capabilities().get("vision", False)

    def supports_reasoning(self) -> bool:
        """Check if current model supports advanced reasoning.

        Returns:
            True if advanced reasoning is supported
        """
        return self.get_model_capabilities().get("reasoning", False)

    def get_web_search_tools(self) -> List[Dict[str, Any]]:
        """Get web search tools for OpenAI API."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for current market data, news, and real-time information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to find current market information",
                            }
                        },
                        "required": ["query"],
                    },
                },
            }
        ]

    async def create_chat_completion_with_web_search(
        self,
        messages: List[Dict[str, Any]],
        search_query: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.3,
    ) -> Optional[Any]:
        """Create chat completion with web search capability.

        Args:
            messages: List of message dictionaries
            search_query: Optional search query to include
            max_tokens: Maximum tokens for response
            temperature: Response creativity (0.0 to 1.0)

        Returns:
            OpenAI response object or None if failed
        """
        if not self.client:
            logger.error("OpenAI client not available")
            return None

        try:
            # Add search query to messages if provided
            if search_query:
                messages.append(
                    {
                        "role": "user",
                        "content": f"Please search for current information about: {search_query}",
                    }
                )

            # Get web search tools
            tools = self.get_web_search_tools()

            # Make API call with tools
            return await self.create_chat_completion(
                messages=messages,
                tools=tools,
                tool_choice="auto",  # Let the model decide when to use tools
                max_tokens=max_tokens,
                temperature=temperature,
            )

        except Exception as e:
            logger.error(f"Error in web search completion: {e}")
            return None
