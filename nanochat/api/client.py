import aiohttp
import asyncio
import json
import logging
from typing import Optional
from nanochat.api.exceptions import *
from nanochat.api.models import ChatRequest, ChatResponse, StreamChunk, Message
from nanochat.constants import DEFAULT_MAX_TOKENS

logger = logging.getLogger(__name__)


class NanoGPTClient:
    """
    Client for NanoGPT API

    API Documentation:
    - Base URL: https://nano-gpt.com/api
    - Chat endpoint: /v1/chat/completions
    - Web search endpoint: /web
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://nano-gpt.com/api",
        timeout: int = 60,
        model: str = "gpt-4"
    ):
        """
        Initialize API client

        Args:
            api_key: NanoGPT API key
            base_url: API base URL
            timeout: Request timeout in seconds
            model: Default model to use
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = aiohttp.ClientTimeout(total=timeout)

        # Endpoints
        self.chat_endpoint = f"{self.base_url}/v1/chat/completions"
        self.web_endpoint = f"{self.base_url}/web"

        # Validate API key
        if not self.api_key or len(self.api_key) < 10:
            logger.warning("API key appears invalid")

    def _get_headers(self) -> dict:
        """Get request headers with authentication"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def send_message(
        self,
        message: str,
        conversation_history: list[dict],
        use_web_search: bool = False,
        stream: bool = True,
        temperature: float = 0.7,
        max_tokens: int = DEFAULT_MAX_TOKENS
    ):
        """
        Send message to API and stream response

        Args:
            message: User message to send
            conversation_history: List of previous messages as dicts
            use_web_search: Whether to use web search endpoint
            stream: Whether to stream response
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            StreamChunk objects with response content
        """
        if use_web_search:
            # Use web search API with proper cleanup
            gen = self._web_search(message)
            try:
                async for chunk in gen:
                    yield chunk
            finally:
                await gen.aclose()
        else:
            # Use standard chat completions API with proper cleanup
            gen = self._chat_completions(message, conversation_history, stream, temperature, max_tokens)
            try:
                async for chunk in gen:
                    yield chunk
            finally:
                await gen.aclose()

    async def _web_search(self, query: str):
        """Perform web search using NanoGPT's web search API"""
        # Build request for web search endpoint
        request_data = {
            "query": query,
            "depth": "standard",  # Use standard depth (cheaper)
            "outputType": "sourcedAnswer"  # Get answer with sources
        }

        logger.info(f"Sending web search request to {self.web_endpoint}")

        # Create session with proper cleanup
        session = aiohttp.ClientSession(timeout=self.timeout)
        try:
            async with session.post(
                self.web_endpoint,
                headers=self._get_headers(),
                json=request_data
            ) as response:
                # Handle errors
                if response.status == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status == 400:
                    # Try to read error response, but don't fail if we can't
                    try:
                        error_text = await response.text()
                        raise InvalidRequestError(
                            error_text or 'Invalid request',
                            status_code=400
                        )
                    except Exception:
                        raise InvalidRequestError('Invalid request', status_code=400)
                elif response.status != 200:
                    # Try to read error response, but don't fail if we can't
                    try:
                        error_text = await response.text()
                    except Exception:
                        error_text = f"HTTP {response.status}"
                    raise APIError(
                        f"API returned {response.status}: {error_text}",
                        status_code=response.status
                    )

                # Parse response (web search is NOT streaming)
                try:
                    data = await response.json()
                except Exception as e:
                    raise APIError(f"Failed to parse response: {str(e)}")

                if 'data' in data and 'answer' in data['data']:
                    answer = data['data']['answer']
                    sources = data['data'].get('sources', [])

                    # Yield the answer as a single chunk
                    yield StreamChunk(content=answer, done=True, web_sources=sources)
                else:
                    raise APIError("Unexpected web search response format")

        except asyncio.TimeoutError:
            raise TimeoutError("Request timed out")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Connection error: {str(e)}")
        finally:
            # Always close the session
            await session.close()

    async def _chat_completions(
        self,
        message: str,
        conversation_history: list[dict],
        stream: bool,
        temperature: float,
        max_tokens: int
    ):
        """Send message to standard chat completions API"""
        # Prepare messages list
        messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in conversation_history
        ]
        messages.append({"role": "user", "content": message})

        # Build request
        request_data = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        logger.info(f"Sending request to {self.chat_endpoint}")

        # Create session with proper cleanup
        session = aiohttp.ClientSession(timeout=self.timeout)
        try:
            async with session.post(
                self.chat_endpoint,
                headers=self._get_headers(),
                json=request_data
            ) as response:
                # Handle errors
                if response.status == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status == 400:
                    # Try to read error response, but don't fail if we can't
                    try:
                        error_text = await response.text()
                        raise InvalidRequestError(
                            error_text or 'Invalid request',
                            status_code=400
                        )
                    except Exception:
                        raise InvalidRequestError('Invalid request', status_code=400)
                elif response.status != 200:
                    # Try to read error response, but don't fail if we can't
                    try:
                        error_text = await response.text()
                    except Exception:
                        error_text = f"HTTP {response.status}"
                    raise APIError(
                        f"API returned {response.status}: {error_text}",
                        status_code=response.status
                    )

                # Stream response
                if stream:
                    async for chunk in self._process_stream(response):
                        yield chunk
                else:
                    # Non-streaming response
                    try:
                        data = await response.json()
                        content = data['choices'][0]['message']['content']
                        yield StreamChunk(content=content, done=True)
                    except Exception as e:
                        raise APIError(f"Failed to parse response: {str(e)}")

        except asyncio.TimeoutError:
            raise TimeoutError("Request timed out")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Connection error: {str(e)}")
        finally:
            # Always close the session
            await session.close()

    async def _process_stream(
        self,
        response: aiohttp.ClientResponse
    ):
        """
        Process streaming response

        Expected format: SSE (Server-Sent Events)
        data: {"content": "...", "done": false}
        """
        buffer = ""

        async for line in response.content:
            line_str = line.decode('utf-8').strip()

            if not line_str:
                continue

            if line_str.startswith('data: '):
                data_str = line_str[6:]  # Remove 'data: ' prefix

                # Check for end of stream
                if data_str == '[DONE]':
                    yield StreamChunk(content="", done=True)
                    return

                try:
                    data = json.loads(data_str)

                    # Handle different response formats
                    if 'choices' in data and len(data['choices']) > 0:
                        delta = data['choices'][0].get('delta', {})
                        content = delta.get('content', '')
                        finish_reason = data['choices'][0].get('finish_reason')

                        done = finish_reason is not None
                        web_sources = data.get('web_sources')

                        if content or done:
                            yield StreamChunk(
                                content=content,
                                done=done,
                                web_sources=web_sources
                            )
                    elif 'content' in data:
                        # Alternative format
                        yield StreamChunk(
                            content=data['content'],
                            done=data.get('done', False),
                            web_sources=data.get('web_sources')
                        )

                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse SSE data: {data_str}, error: {e}")
                    continue

    async def fetch_models(self) -> list:
        """
        Fetch available models from the API

        Returns:
            List of model IDs (strings)

        Raises:
            AuthenticationError: If API key is invalid
            APIError: If request fails
        """
        models_endpoint = f"{self.base_url}/v1/models"

        logger.info(f"Fetching available models from {models_endpoint}")

        session = aiohttp.ClientSession(timeout=self.timeout)
        try:
            async with session.get(
                models_endpoint,
                headers=self._get_headers()
            ) as response:
                # Handle errors
                if response.status == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status != 200:
                    error_text = await response.text()
                    raise APIError(
                        f"API returned {response.status}: {error_text}",
                        status_code=response.status
                    )

                # Parse response
                try:
                    data = await response.json()
                except Exception as e:
                    raise APIError(f"Failed to parse models response: {str(e)}")

                # Extract model IDs from response
                # OpenAI-compatible format: {"data": [{"id": "model1"}, ...]}
                if 'data' in data and isinstance(data['data'], list):
                    models = [model['id'] for model in data['data'] if 'id' in model]
                    logger.info(f"Successfully fetched {len(models)} models")
                    return models
                else:
                    logger.warning("Unexpected models response format")
                    return []

        except asyncio.TimeoutError:
            raise TimeoutError("Request timed out")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Connection error: {str(e)}")
        finally:
            await session.close()

    async def test_connection(self) -> bool:
        """Test if API key is valid by making a simple request"""
        try:
            async for chunk in self.send_message(
                message="Hello",
                conversation_history=[],
                stream=True,
                max_tokens=5
            ):
                if chunk.content:
                    logger.info("API connection test successful")
                    return True
            return True
        except AuthenticationError:
            logger.error("API key is invalid")
            return False
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
