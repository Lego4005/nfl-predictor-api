"""
Local LLM Service - Interface to local language model
Provides AI-powered reasoning for NFL prediction experts
"""

import requests
import time
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import random

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Structured response from local LLM"""
    content: str
    tokens_used: Optional[int] = None
    response_time: float = 0.0
    model: str = "openai/gpt-oss-20b"

    # Additional properties for compatibility
    @property
    def total_tokens(self) -> int:
        return self.tokens_used or 0

    @property
    def prompt_tokens(self) -> int:
        # Estimate: roughly 70% of total tokens are typically completion
        return int((self.tokens_used or 0) * 0.3)

    @property
    def completion_tokens(self) -> int:
        # Estimate: roughly 70% of total tokens are typically completion
        return int((self.tokens_used or 0) * 0.7)


class LocalLLMService:
    """Service for interacting with local LLM at 192.168.254.253:1234"""

    def __init__(self, base_url: str = "http://192.168.254.253:1234", timeout: int = 60):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()

        # Configure session with connection pooling
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

        logger.info(f"🤖 LocalLLMService initialized with endpoint: {base_url}")

    def generate_completion(
        self,
        system_message: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = -1,
        model: str = "openai/gpt-oss-120b",
        json_schema: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """
        Generate completion using local LLM with OpenAI-compatible API

        Args:
            system_message: System prompt defining expert personality
            user_message: User prompt with game context
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate (-1 for unlimited)
            model: Model name to use

        Returns:
            LLMResponse with generated content and metadata
        """
        start_time = time.perf_counter()

        try:
            # Construct OpenAI-compatible request
            request_data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                "temperature": temperature,
                "stream": False
            }

            # Add max_tokens if specified (don't include if unlimited)
            if max_tokens > 0:
                request_data["max_tokens"] = max_tokens

            # Add JSON schema for structured output (LM Studio support)
            if json_schema:
                request_data["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "nfl_prediction",
                        "strict": True,
                        "schema": json_schema
                    }
                }
                logger.info("📋 Using JSON schema for structured output")

            logger.info(f"🔄 Making LLM request to {self.base_url}/v1/chat/completions")
            logger.debug(f"Request data: {json.dumps(request_data, indent=2)}")

            # Make request with retry logic
            response = self._make_request_with_retry(
                url=f"{self.base_url}/v1/chat/completions",
                data=request_data,
                max_retries=3
            )

            response_time = time.perf_counter() - start_time

            # Parse response
            try:
                response_json = response.json()
                logger.debug(f"Raw response: {json.dumps(response_json, indent=2)}")

                # Extract content from OpenAI-compatible response
                if 'choices' in response_json and len(response_json['choices']) > 0:
                    message = response_json['choices'][0]['message']
                    content = message.get('content', '')

                    # If content is empty but reasoning exists, use reasoning instead
                    if not content and 'reasoning' in message:
                        content = message['reasoning']
                        logger.info("📝 Using reasoning field as content (content field was empty)")

                    # Extract usage info if available
                    tokens_used = None
                    if 'usage' in response_json:
                        tokens_used = response_json['usage'].get('total_tokens')

                    logger.info(f"✅ LLM response received in {response_time:.3f}s")
                    if tokens_used:
                        logger.info(f"   → Tokens used: {tokens_used}")

                    return LLMResponse(
                        content=content,
                        tokens_used=tokens_used,
                        response_time=response_time,
                        model=model
                    )
                else:
                    raise ValueError("Invalid response format: missing choices")

            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse JSON response: {e}")
                logger.error(f"Raw response text: {response.text[:500]}")
                raise ValueError(f"Invalid JSON response from LLM: {e}")

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error calling LLM: {e}")
            raise ConnectionError(f"Failed to connect to local LLM: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error in LLM call: {e}")
            raise

    def _make_request_with_retry(
        self,
        url: str,
        data: Dict[str, Any],
        max_retries: int = 3
    ) -> requests.Response:
        """Make HTTP request with exponential backoff retry logic"""

        for attempt in range(max_retries + 1):
            try:
                response = self.session.post(
                    url=url,
                    json=data,
                    timeout=self.timeout
                )

                # Check for HTTP errors
                response.raise_for_status()
                return response

            except requests.exceptions.Timeout as e:
                if attempt == max_retries:
                    logger.error(f"❌ Request timed out after {max_retries} retries")
                    raise

                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"⚠️ Request timeout (attempt {attempt + 1}), retrying in {wait_time:.1f}s")
                time.sleep(wait_time)

            except requests.exceptions.ConnectionError as e:
                if attempt == max_retries:
                    logger.error(f"❌ Connection failed after {max_retries} retries")
                    raise

                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"⚠️ Connection error (attempt {attempt + 1}), retrying in {wait_time:.1f}s")
                time.sleep(wait_time)

            except requests.exceptions.HTTPError as e:
                # Don't retry on 4xx errors (client errors)
                if 400 <= e.response.status_code < 500:
                    logger.error(f"❌ Client error: {e.response.status_code} - {e.response.text}")
                    raise

                # Retry on 5xx errors (server errors)
                if attempt == max_retries:
                    logger.error(f"❌ Server error after {max_retries} retries: {e}")
                    raise

                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"⚠️ Server error (attempt {attempt + 1}), retrying in {wait_time:.1f}s")
                time.sleep(wait_time)

    def test_connection(self) -> bool:
        """Test connection to local LLM with simple prompt"""
        try:
            logger.info("🔍 Testing connection to local LLM...")

            response = self.generate_completion(
                system_message="You are a helpful assistant.",
                user_message="Respond with exactly: 'Connection test successful'",
                temperature=0.0,
                max_tokens=10
            )

            # Check if we got any response (connection successful)
            success = len(response.content) > 0
            if success:
                logger.info(f"✅ LLM connection test passed in {response.response_time:.3f}s")
                logger.info(f"   Response preview: {response.content[:100]}...")
            else:
                logger.warning(f"⚠️ LLM responded but with empty content")

            return success

        except Exception as e:
            logger.error(f"❌ LLM connection test failed: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information from the local LLM"""
        try:
            response = self.session.get(f"{self.base_url}/v1/models", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"⚠️ Could not retrieve model info: {e}")
            return {"models": [{"id": "openai/gpt-oss-20b"}]}


# Global instance for easy access
_llm_service = None

def get_llm_service() -> LocalLLMService:
    """Get global LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LocalLLMService()
    return _llm_service
