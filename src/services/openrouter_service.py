"""
OpenRouter LLM Service - Access to multiple cloud models
"""

import requests
import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Structured response from LLM"""
    content: str
    tokens_used: Optional[int] = None
    response_time: float = 0.0
    model: str = "unknown"


class OpenRouterService:
    """Service for accessing models via OpenRouter API"""

    def __init__(self, api_key: str, timeout: int = 60):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.timeout = timeout
        self.session = requests.Session()

        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/nfl-predictor',
            'X-Title': 'NFL Predictor'
        })

        logger.info(f"🌐 OpenRouterService initialized")

    def generate_completion(
        self,
        system_message: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        model: str = "anthropic/claude-3.5-sonnet"
    ) -> LLMResponse:
        """Generate completion using OpenRouter"""
        start_time = time.perf_counter()

        try:
            request_data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            logger.info(f"🔄 Making request to {model}")

            response = self.session.post(
                url=f"{self.base_url}/chat/completions",
                json=request_data,
                timeout=self.timeout
            )

            response.raise_for_status()
            response_time = time.perf_counter() - start_time

            response_json = response.json()

            if 'choices' in response_json and len(response_json['choices']) > 0:
                content = response_json['choices'][0]['message']['content']
                tokens_used = response_json.get('usage', {}).get('total_tokens')

                logger.info(f"✅ Response received in {response_time:.3f}s")
                if tokens_used:
                    logger.info(f"   → Tokens used: {tokens_used}")

                return LLMResponse(
                    content=content,
                    tokens_used=tokens_used,
                    response_time=response_time,
                    model=model
                )
            else:
                raise ValueError("Invalid response format")

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request failed: {e}")
            raise ConnectionError(f"Failed to connect to OpenRouter: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            raise
