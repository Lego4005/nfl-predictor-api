"""
OpenRouter LLM Service

Unified LLMg OpenRouter to access multiple model providers
through a single API endpoint. Supports all the models needed for the
4-expert pilot system.
"""

import os
import asyncio
import aiohttp
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class OpenRouterLLMService:
    """Service for making LLM calls through OpenRouter"""

    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1"
        self.app_name = "NFL Expert Council Betting System"

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")

        # Model mappings for the 4-expert pilot
        self.model_mappings = {
            # Primary models for experts
            'conservative_analyzer': 'anthropic/claude-3.5-sonnet',
            'momentum_rider': 'deepseek/deepseek-chat',
            'contrarian_rebel': 'deepseek/deepseek-chat',
            'value_hunter': 'anthropic/claude-3.5-sonnet',

            # Critic/Repair model (reliable for schema validation)
            'critic_repair': 'anthropic/claude-3.5-sonnet',

            # Shadow models for A/B testing
            'shadow_gemini': 'google/gemini-pro-1.5',
            'shadow_grok': 'x-ai/grok-beta',

            # Baseline models
            'one_shot': 'deepseek/deepseek-chat',
            'deliberate': 'anthropic/claude-3.5-sonnet'
        }

        # Model configurations
        self.model_configs = {
            'anthropic/claude-3.5-sonnet': {
                'max_tokens': 4000,
                'temperature': 0.3,
                'top_p': 0.9,
                'description': 'High-quality reasoning, excellent for schema compliance'
            },
            'deepseek/deepseek-chat': {
                'max_tokens': 4000,
                'temperature': 0.3,
                'top_p': 0.9,
                'description': 'Fast and cost-effective, good for high-volume predictions'
            },
            'google/gemini-pro-1.5': {
                'max_tokens': 4000,
                'temperature': 0.3,
                'top_p': 0.9,
                'description': 'Balanced performance for shadow testing'
            },
            'x-ai/grok-beta': {
                'max_tokens': 4000,
                'temperature': 0.4,
                'top_p': 0.9,
                'description': 'Contrarian analysis, good for diverse perspectives'
            }
        }

    async def generate_expert_prediction(
        self,
        expert_id: str,
        system_prompt: str,
        user_prompt: str,
        model_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate expert prediction using appropriate model"""

        # Determine model to use
        model = model_override or self.model_mappings.get(expert_id, 'deepseek/deepseek-chat')

        try:
            response = await self._make_llm_call(
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                expert_id=expert_id
            )

            return {
                'success': True,
                'response': response,
                'model_used': model,
                'expert_id': expert_id,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Expert prediction failed for {expert_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'model_used': model,
                'expert_id': expert_id,
                'timestamp': datetime.now().isoformat()
            }

    async def critic_repair_call(
        self,
        original_response: str,
        schema_errors: List[str],
        system_prompt: str
    ) -> Dict[str, Any]:
        """Make critic/repair call to fix schema issues"""

        model = self.model_mappings['critic_repair']

        repair_prompt = f"""
The following response failed schema validation:

ORIGINAL RESPONSE:
{original_response}

SCHEMA ERRORS:
{json.dumps(schema_errors, indent=2)}

Please provide a corrected version that follows the exact schema requirements.
Return only the corrected JSON response.
"""

        try:
            response = await self._make_llm_call(
                model=model,
                system_prompt=system_prompt,
                user_prompt=repair_prompt,
                expert_id='critic_repair'
            )

            return {
                'success': True,
                'repaired_response': response,
                'model_used': model,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Critic repair failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'model_used': model,
                'timestamp': datetime.now().isoformat()
            }

    async def shadow_model_call(
        self,
        expert_id: str,
        system_prompt: str,
        user_prompt: str,
        shadow_model: str
    ) -> Dict[str, Any]:
        """Make shadow model call for A/B testing"""

        try:
            response = await self._make_llm_call(
                model=shadow_model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                expert_id=f"{expert_id}_shadow"
            )

            return {
                'success': True,
                'response': response,
                'model_used': shadow_model,
                'expert_id': expert_id,
                'shadow_run': True,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Shadow model call failed for {expert_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'model_used': shadow_model,
                'expert_id': expert_id,
                'shadow_run': True,
                'timestamp': datetime.now().isoformat()
            }

    async def baseline_one_shot_call(
        self,
        game_context: str,
        minimal_prompt: str
    ) -> Dict[str, Any]:
        """Make one-shot baseline call without memory/context"""

        model = self.model_mappings['one_shot']

        try:
            response = await self._make_llm_call(
                model=model,
                system_prompt="You are a sports analyst. Provide concise predictions in JSON format.",
                user_prompt=minimal_prompt,
                expert_id='baseline_one_shot'
            )

            return {
                'success': True,
                'response': response,
                'model_used': model,
                'baseline_type': 'one_shot',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Baseline one-shot call failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'model_used': model,
                'baseline_type': 'one_shot',
                'timestamp': datetime.now().isoformat()
            }

    async def _make_llm_call(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        expert_id: str
    ) -> str:
        """Make the actual LLM API call through OpenRouter"""

        config = self.model_configs.get(model, self.model_configs['deepseek/deepseek-chat'])

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/your-repo/nfl-predictor-api',
            'X-Title': self.app_name
        }

        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'max_tokens': config['max_tokens'],
            'temperature': config['temperature'],
            'top_p': config['top_p'],
            'stream': False
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        content = data['choices'][0]['message']['content']

                        # Log usage for monitoring
                        usage = data.get('usage', {})
                        logger.info(f"LLM call successful - {expert_id} - {model} - "
                                  f"Tokens: {usage.get('total_tokens', 0)}")

                        return content
                    else:
                        error_text = await response.text()
                        raise Exception(f"OpenRouter API error {response.status}: {error_text}")

            except asyncio.TimeoutError:
                raise Exception("LLM call timed out after 60 seconds")
            except Exception as e:
                raise Exception(f"LLM call failed: {str(e)}")

    def get_model_for_expert(self, expert_id: str) -> str:
        """Get the current model assignment for an expert"""
        return self.model_mappings.get(expert_id, 'deepseek/deepseek-chat')

    def update_model_assignment(self, expert_id: str, new_model: str):
        """Update model assignment for an expert"""
        if new_model in self.model_configs:
            self.model_mappings[expert_id] = new_model
            logger.info(f"Updated {expert_id} model assignment to {new_model}")
        else:
            raise ValueError(f"Unknown model: {new_model}")

    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available models and their configurations"""
        return {
            model: {
                'config': config,
                'current_assignments': [
                    expert_id for expert_id, assigned_model in self.model_mappings.items()
                    if assigned_model == model
                ]
            }
            for model, config in self.model_configs.items()
        }

    async def test_connection(self) -> Dict[str, Any]:
        """Test OpenRouter connection and available models"""
        try:
            test_response = await self._make_llm_call(
                model='deepseek/deepseek-chat',
                system_prompt='You are a helpful assistant.',
                user_prompt='Say "Connection test successful" in JSON format: {"status": "success", "message": "Connection test successful"}',
                expert_id='connection_test'
            )

            return {
                'success': True,
                'response': test_response,
                'available_models': list(self.model_configs.keys()),
                'current_assignments': self.model_mappings
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'available_models': list(self.model_configs.keys())
            }

# Global service instance
_llm_service = None

def get_llm_service() -> OpenRouterLLMService:
    """Get global LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = OpenRouterLLMService()
    return _llm_service
