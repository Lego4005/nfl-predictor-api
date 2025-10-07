#!/usr/bin/env python3
"""
Simple wrapper for existing code to use the unified AI client
This provides backward compatibility while migrating to the new unified approach
"""

from typing import List, Dict, Any
from .unified_ai_client import UnifiedAIClient, create_embedding, create_chat_completion

# Global client instance
_client = None

def get_client() -> UnifiedAIClient:
    """Get or create the global unified AI client"""
    global _client
    if _client is None:
        _client = UnifiedAIClient()
    return _client

# Backward compatibility functions
def get_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """Get embedding vector (backward compatible)"""
    return create_embedding(text, model)

def get_chat_response(messages: List[Dict[str, str]], model: str = "openai/gpt-4o-mini") -> str:
    """Get chat completion response (backward compatible)"""
    return create_chat_completion(messages, model)

# OpenAI-style client for drop-in replacement
class OpenAICompatibleClient:
    """Drop-in replacement for OpenAI client that uses unified routing"""

    def __init__(self):
        self.client = get_client()
        self.embeddings = EmbeddingsAPI(self.client)
        self.chat = ChatAPI(self.client)

class EmbeddingsAPI:
    """OpenAI-compatible embeddings API"""

    def __init__(self, client: UnifiedAIClient):
        self.client = client

    def create(self, model: str, input: str, **kwargs):
        """Create embeddings (OpenAI-compatible)"""
        response = self.client.create_embedding(input, model)

        # Return OpenAI-compatible response object
        class EmbeddingData:
            def __init__(self, embedding):
                self.embedding = embedding

        class EmbeddingResponse:
            def __init__(self, embedding, model, usage):
                self.data = [EmbeddingData(embedding)]
                self.model = model
                self.usage = usage

        return EmbeddingResponse(response.embedding, response.model, response.usage)

class ChatAPI:
    """OpenAI-compatible chat API"""

    def __init__(self, client: UnifiedAIClient):
        self.client = client
        self.completions = ChatCompletionsAPI(client)

class ChatCompletionsAPI:
    """OpenAI-compatible chat completions API"""

    def __init__(self, client: UnifiedAIClient):
        self.client = client

    def create(self, model: str, messages: List[Dict[str, str]], **kwargs):
        """Create chat completion (OpenAI-compatible)"""
        response = self.client.create_chat_completion(messages, model, **kwargs)

        # Return OpenAI-compatible response object
        class Message:
            def __init__(self, content):
                self.content = content

        class Choice:
            def __init__(self, message, finish_reason):
                self.message = message
                self.finish_reason = finish_reason

        class ChatResponse:
            def __init__(self, content, model, usage, finish_reason):
                self.choices = [Choice(Message(content), finish_reason)]
                self.model = model
                self.usage = usage

        return ChatResponse(response.content, response.model, response.usage, response.finish_reason)

# Factory function for easy migration
def create_openai_client():
    """Create OpenAI-compatible client that uses unified routing"""
    return OpenAICompatibleClient()
