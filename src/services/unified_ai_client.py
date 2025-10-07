#!/usr/bin/env python3
"""
Unified AI Client that routes requests to appropriate providers:
- OpenAI for embeddings (only provider that supports embeddings)
- OpenRouter for chat completions (cost-effective)
- OpenAI as fallback for chat completions
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import json

# Try to import OpenAI client
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)

@dataclass
class EmbeddingResponse:
    """Normalized embedding response"""
    embedding: List[float]
    model: str
    usage: Dict[str, Any]

@dataclass
class ChatResponse:
    """Normalized chat completion response"""
    content: str
    model: str
    usage: Dict[str, Any]
    finish_reason: str

class UnifiedAIClient:
    """
    Unified client that automatically routes requests to the best provider:
    - OpenAI for embeddings (only provider that supports embeddings)
    - OpenRouter for chat completions (cost-effective)
    - OpenAI as fallback for chat completions
    """

    def __init__(self):
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.openrouter_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('VITE_OPENROUTER_API_KEY')

        # Initialize clients
        self._openrouter_client = None
        self._openai_client = None

        if self.openrouter_key and OpenAI:
            try:
                self._openrouter_client = OpenAI(
                    api_key=self.openrouter_key,
                    base_url="https://openrouter.ai/api/v1"
                )
                logger.info("✅ OpenRouter client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenRouter client: {e}")

        if self.openai_key and OpenAI:
            try:
                self._openai_client = OpenAI(api_key=self.openai_key)
                logger.info("✅ OpenAI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")

    def create_embedding(self, text: str, model: str = "text-embedding-3-small") -> EmbeddingResponse:
        """
        Create embeddings using OpenAI (only provider that supports embeddings)
        """
        # OpenAI is the only provider that supports embeddings
        if self._openai_client:
            try:
                return self._create_embedding_openai(text, model)
            except Exception as e:
                logger.error(f"OpenAI embedding failed: {e}")
                raise

        raise RuntimeError("No embedding providers available - OpenAI API key required for embeddings")



    def _create_embedding_openai(self, text: str, model: str) -> EmbeddingResponse:
        """Direct OpenAI embedding call"""
        response = self._openai_client.embeddings.create(
            model=model,
            input=text
        )

        return EmbeddingResponse(
            embedding=response.data[0].embedding,
            model=response.model,
            usage=response.usage.model_dump() if hasattr(response.usage, 'model_dump') else dict(response.usage)
        )



    def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "openai/gpt-4o-mini",
        **kwargs
    ) -> ChatResponse:
        """
        Create chat completions using OpenRouter (preferred) or OpenAI fallback
        """
        # Try OpenRouter first (cost-effective)
        if self._openrouter_client:
            try:
                return self._create_chat_openrouter(messages, model, **kwargs)
            except Exception as e:
                logger.warning(f"OpenRouter chat failed, trying OpenAI: {e}")

        # Fallback to OpenAI
        if self._openai_client:
            # Convert OpenRouter model names to OpenAI equivalents
            openai_model = self._convert_model_name(model)
            try:
                return self._create_chat_openai(messages, openai_model, **kwargs)
            except Exception as e:
                logger.error(f"All chat providers failed. Last error: {e}")
                raise

        raise RuntimeError("No chat completion providers available")

    def _create_chat_openrouter(self, messages: List[Dict[str, str]], model: str, **kwargs) -> ChatResponse:
        """OpenRouter chat completion"""
        response = self._openrouter_client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )

        return ChatResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage=response.usage.model_dump() if hasattr(response.usage, 'model_dump') else dict(response.usage),
            finish_reason=response.choices[0].finish_reason
        )

    def _create_chat_openai(self, messages: List[Dict[str, str]], model: str, **kwargs) -> ChatResponse:
        """Direct OpenAI chat completion"""
        response = self._openai_client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )

        return ChatResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage=response.usage.model_dump() if hasattr(response.usage, 'model_dump') else dict(response.usage),
            finish_reason=response.choices[0].finish_reason
        )

    def _convert_model_name(self, openrouter_model: str) -> str:
        """Convert OpenRouter model names to OpenAI equivalents"""
        model_mapping = {
            "openai/gpt-4o": "gpt-4o",
            "openai/gpt-4o-mini": "gpt-4o-mini",
            "openai/gpt-4": "gpt-4",
            "openai/gpt-3.5-turbo": "gpt-3.5-turbo",
        }
        return model_mapping.get(openrouter_model, "gpt-4o-mini")

    def test_connections(self) -> Dict[str, bool]:
        """Test all available connections"""
        results = {
            "openai_embeddings": False,
            "openrouter_chat": False,
            "openai_chat": False
        }

        # Test OpenAI embeddings
        if self._openai_client:
            try:
                self._create_embedding_openai("test", "text-embedding-3-small")
                results["openai_embeddings"] = True
            except:
                pass



        # Test OpenRouter chat
        if self._openrouter_client:
            try:
                self._create_chat_openrouter([{"role": "user", "content": "test"}], "openai/gpt-4o-mini")
                results["openrouter_chat"] = True
            except:
                pass

        # Test OpenAI chat
        if self._openai_client:
            try:
                self._create_chat_openai([{"role": "user", "content": "test"}], "gpt-4o-mini")
                results["openai_chat"] = True
            except:
                pass

        return results

# Convenience functions for backward compatibility
def create_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """Create embedding and return just the vector for backward compatibility"""
    client = UnifiedAIClient()
    response = client.create_embedding(text, model)
    return response.embedding

def create_chat_completion(messages: List[Dict[str, str]], model: str = "openai/gpt-4o-mini", **kwargs) -> str:
    """Create chat completion and return just the content for backward compatibility"""
    client = UnifiedAIClient()
    response = client.create_chat_completion(messages, model, **kwargs)
    return response.content
