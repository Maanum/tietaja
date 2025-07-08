"""
OpenAI client wrapper for GPT-4o chat completions.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class OpenAIClient:
    """Wrapper for OpenAI API client with GPT-4o support."""
    
    def __init__(self):
        """Initialize the OpenAI client."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Configure OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        # Default model and parameters
        self.default_model = "gpt-4o"
        self.default_temperature = 0.7
        self.default_max_tokens = 1000
        
        logger.info("OpenAI client initialized")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Make a chat completion request to GPT-4o.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            tools: Optional list of tool schemas for function calling
            model: Model to use (defaults to gpt-4o)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for the API call
            
        Returns:
            Generated response text
        """
        try:
            # Set default values
            model = model or self.default_model
            temperature = temperature or self.default_temperature
            max_tokens = max_tokens or self.default_max_tokens
            
            # Prepare request parameters
            request_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs
            }
            
            # Add tools if provided
            if tools:
                request_params["tools"] = tools
                request_params["tool_choice"] = "auto"
            
            logger.info(f"Making OpenAI API request with model: {model}")
            
            # Make the API call
            response = self.client.chat.completions.create(**request_params)
            
            # Extract the response content
            logger.info(f"Response type: {type(response)}")
            logger.info(f"Response: {response}")
            
            if response and hasattr(response, 'choices') and response.choices and len(response.choices) > 0:
                choice = response.choices[0]
                
                # Handle tool calls
                if getattr(choice.message, 'tool_calls', None):
                    logger.info(f"Received {len(choice.message.tool_calls)} tool calls")
                    return f"I can help you with that! I detected {len(choice.message.tool_calls)} action(s) I can take."
                
                # Return the content
                content = choice.message.content
                if content:
                    logger.info(f"Received response with {len(content)} characters")
                    return content
                else:
                    logger.warning("No content in response")
                    return "I received a response but it was empty."
            else:
                logger.warning(f"No choices in OpenAI response. Response: {response}")
                return "No response generated"
                
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    async def chat_completion_with_response(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> tuple[str, Any]:
        """
        Make a chat completion request to GPT-4o and return both content and full response.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            tools: Optional list of tool schemas for function calling
            model: Model to use (defaults to gpt-4o)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for the API call
            
        Returns:
            Tuple of (content, full_response_object)
        """
        try:
            # Set default values
            model = model or self.default_model
            temperature = temperature or self.default_temperature
            max_tokens = max_tokens or self.default_max_tokens
            
            # Prepare request parameters
            request_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs
            }
            
            # Add tools if provided
            if tools:
                request_params["tools"] = tools
                request_params["tool_choice"] = "auto"
            
            logger.info(f"Making OpenAI API request with model: {model}")
            
            # Make the API call
            response = self.client.chat.completions.create(**request_params)
            
            # Extract the response content
            logger.info(f"Response type: {type(response)}")
            
            if response and hasattr(response, 'choices') and response.choices and len(response.choices) > 0:
                choice = response.choices[0]
                
                # Handle tool calls
                if getattr(choice.message, 'tool_calls', None):
                    logger.info(f"Received {len(choice.message.tool_calls)} tool calls")
                    content = f"I can help you with that! I detected {len(choice.message.tool_calls)} action(s) I can take."
                else:
                    # Return the content
                    content = choice.message.content or "I received a response but it was empty."
                
                logger.info(f"Received response with {len(content)} characters")
                return content, response
            else:
                logger.warning(f"No choices in OpenAI response. Response: {response}")
                return "No response generated", response
                
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    def chat_completion_sync(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Synchronous version of chat completion for non-async contexts.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            tools: Optional list of tool schemas for function calling
            model: Model to use (defaults to gpt-4o)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for the API call
            
        Returns:
            Generated response text
        """
        try:
            # Set default values
            model = model or self.default_model
            temperature = temperature or self.default_temperature
            max_tokens = max_tokens or self.default_max_tokens
            
            # Prepare request parameters
            request_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs
            }
            
            # Add tools if provided
            if tools:
                request_params["tools"] = tools
                request_params["tool_choice"] = "auto"
            
            logger.info(f"Making synchronous OpenAI API request with model: {model}")
            
            # Make the API call
            response = self.client.chat.completions.create(**request_params)
            
            # Extract the response content
            logger.info(f"Response type: {type(response)}")
            logger.info(f"Response: {response}")
            
            if response and hasattr(response, 'choices') and response.choices and len(response.choices) > 0:
                choice = response.choices[0]
                
                # Return the content (tool calls will be handled separately)
                content = choice.message.content
                logger.info(f"Received response with {len(content)} characters")
                return content
            else:
                logger.warning(f"No choices in OpenAI response. Response: {response}")
                return "No response generated"
                
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    def get_models(self) -> List[Dict[str, Any]]:
        """
        Get available OpenAI models.
        
        Returns:
            List of available models
        """
        try:
            models = self.client.models.list()
            return [model.model_dump() for model in models.data]
        except Exception as e:
            logger.error(f"Error fetching models: {str(e)}")
            return []
    
    def validate_api_key(self) -> bool:
        """
        Validate the OpenAI API key.
        
        Returns:
            True if valid, False otherwise
        """
        try:
            # Try to list models as a simple validation
            models = self.get_models()
            return len(models) > 0
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return False
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get API usage statistics.
        
        Returns:
            Dictionary with usage statistics
        """
        # Usage API is not available in current version
        return {"error": "Usage API not available in current OpenAI version"}