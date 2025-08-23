"""
OpenAI client wrapper module for enhanced functionality.
Handles OpenAI API interactions with proper error handling and retry logic.
"""

import logging
import asyncio
import base64
from typing import Dict, Any, List, Optional, Union
import json
import openai
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class OpenAIClientWrapper:
    """Wrapper for OpenAI client with enhanced functionality."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o", max_retries: int = 3):
        """Initialize OpenAI client wrapper.
        
        Args:
            api_key: OpenAI API key
            model: Model to use for completions
            max_retries: Maximum number of retries for failed requests
        """
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None
        
        if not self.client:
            logger.warning("OpenAI client not initialized - API key missing")
    
    async def create_chat_completion(self, 
                                   messages: List[Dict[str, Any]],
                                   functions: Optional[List[Dict[str, Any]]] = None,
                                   function_call: Optional[Union[str, Dict[str, str]]] = None,
                                   response_format: Optional[Dict[str, Any]] = None,
                                   max_tokens: Optional[int] = None,
                                   temperature: float = 0.3) -> Optional[Any]:
        """Create chat completion with retry logic.
        
        Args:
            messages: List of messages for the conversation
            functions: Optional list of functions for function calling
            function_call: Optional function call specification
            response_format: Optional response format specification
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            
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
                    "temperature": temperature
                }
                
                # Add optional parameters
                if functions:
                    params["functions"] = functions
                if function_call:
                    params["function_call"] = function_call
                if response_format:
                    params["response_format"] = response_format
                
                # Make the API call
                response = await self.client.chat.completions.create(**params)
                
                logger.info(f"OpenAI API call successful (attempt {attempt + 1})")
                return response
                
            except openai.RateLimitError as e:
                wait_time = (attempt + 1) * 2  # Exponential backoff
                logger.warning(f"Rate limit hit (attempt {attempt + 1}), waiting {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
                
            except openai.APIError as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"OpenAI API error after {self.max_retries} attempts: {e}")
                    return None
                else:
                    wait_time = (attempt + 1) * 1
                    logger.warning(f"API error (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"Unexpected error in OpenAI API call: {e}")
                return None
        
        return None
    
    async def analyze_image_with_context(self,
                                       image_data: bytes,
                                       system_prompt: str,
                                       user_prompt: str,
                                       response_format: Optional[Dict[str, Any]] = None) -> Optional[str]:
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
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                        }
                    ]
                }
            ]
            
            # Make API call
            response = await self.create_chat_completion(
                messages=messages,
                response_format=response_format,
                max_tokens=2000
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
    
    async def search_realtime_data(self, query: str, max_tokens: int = 800) -> Optional[str]:
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

Focus on specific price levels, recent movements, and relevant news. Return ONLY the JSON, no additional text."""
            },
            {"role": "user", "content": query}
        ]
        
        # Use simple JSON response format
        response = await self.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.3
        )
        
        if response and response.choices:
            content = response.choices[0].message.content
            logger.info("Real-time data search completed")
            return content
        
        logger.warning("No response from real-time data search")
        return None
    
    async def generate_structured_signal(self,
                                       system_prompt: str,
                                       analysis_prompt: str,
                                       signal_schema: Dict[str, Any],
                                       image_data: Optional[bytes] = None) -> Optional[Dict[str, Any]]:
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
                                "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                            }
                        ]
                    }
                ]
            else:
                # Text-only analysis
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": analysis_prompt}
                ]
            
            # Make API call without response_format to avoid schema validation errors
            response = await self.create_chat_completion(
                messages=messages,
                max_tokens=2000,
                temperature=0.3
            )
            
            if response and response.choices:
                content = response.choices[0].message.content
                if content:
                    try:
                        signal_data = json.loads(content)
                        logger.info("Structured signal generated successfully")
                        return signal_data
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse signal JSON: {e}")
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
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
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
