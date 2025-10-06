#!/usr/bin/env python3
"""
Real LLM Prediction Generator

This modulectual LLM API calls to generate authentic expert predictions
using each expert's personality prompt and game context. This replaces the
hardcoded simulation logic with real AI-generated predictions.
"""

import sys
import logging
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import os
import requests
import json
from dotenv import load_dotenv
sys.path.append('src')

from training.expert_configuration import ExpertType, ExpertConfiguration, ExpertConfigurationManager
from training.prediction_generator import GamePrediction, PredictionType
from training.memory_retrieval_system import MemoryRetrievalResult, RetrievedMemory

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Expert-to-Model permanent assignments (actual valid OpenRouter models)
EXPERT_MODEL_ASSIGNMENTS = {
    ExpertType.CHAOS_THEORY_BELIEVER: {
        "model": "deepseek/deepseek-chat-v3.1:free",
        "rpm_limit": 20,
        "provider": "openrouter"
    },
    ExpertType.CONSENSUS_FOLLOWER: {
        "model": "qwen/qwen3-30b-a3b:free",
        "rpm_limit": 20,
        "provider": "openrouter"
    },
    ExpertType.CONSERVATIVE_ANALYZER: {
        "model": "mistralai/mistral-small-3.2-24b-instruct:free",
        "rpm_limit": 20,
        "provider": "openrouter"
    },
    ExpertType.CONTRARIAN_REBEL: {
        "model": "meta-llama/llama-3.3-8b-instruct:free",
        "rpm_limit": 20,
        "provider": "openrouter"
    },
    ExpertType.FUNDAMENTALIST_SCHOLAR: {
        "model": "qwen/qwen3-235b-a22b:free",
        "rpm_limit": 20,
        "provider": "openrouter"
    },
    ExpertType.GUT_INSTINCT_EXPERT: {
        "model": "moonshotai/kimi-k2:free",
        "rpm_limit": 20,
        "provider": "openrouter"
    },
    ExpertType.MARKET_INEFFICIENCY_EXPLOITER: {
        "model": "qwen/qwen3-coder:free",
        "rpm_limit": 20,
        "provider": "openrouter"
    },
    ExpertType.MOMENTUM_RIDER: {
        "model": "tencent/hunyuan-a13b-instruct:free",
        "rpm_limit": 20,
        "provider": "openrouter"
    },
    ExpertType.POPULAR_NARRATIVE_FADER: {
        "model": "deepseek/deepseek-chat-v3.1:free",
        "rpm_limit": 20,
        "provider": "openrouter"
    },
    ExpertType.RISK_TAKING_GAMBLER: {
        "model": "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
        "rpm_limit": 20,
        "provider": "openrouter"
    },
    ExpertType.SHARP_MONEY_FOLLOWER: {
        "model": "shisa-ai/shisa-v2-llama3.3-70b:free",
        "rpm_limit": 20,
        "provider": "openrouter"
    },
    ExpertType.STATISTICS_PURIST: {
        "model": "microsoft/mai-ds-r1:free",
        "rpm_limit": 20,
        "provider": "openrouter"
    },
    ExpertType.TREND_REVERSAL_SPECIALIST: {
        "model": "qwen/qwen3-14b:free",
        "rpm_limit": 20,
        "provider": "openrouter"
    },
    ExpertType.UNDERDOG_CHAMPION: {
        "model": "moonshotai/kimi-dev-72b:free",
        "rpm_limit": 20,
        "provider": "openrouter"
    },
    ExpertType.VALUE_HUNTER: {
        "model": "arliai/qwq-32b-arliai-rpr-v1:free",
        "rpm_limit": 20,
        "provider": "openrouter"
    }
}

@dataclass
class LLMPredictionRequest:
    """Request for LLM prediction generation"""
    expert_type: ExpertType
    expert_config: ExpertConfiguration
    game_context: Dict[str, Any]
    retrieved_memories: List[RetrievedMemory]
    prediction_type: PredictionType

@dataclass
class LLMPredictionResponse:
    """Response from LLM prediction generation"""
    predicted_winner: Optional[str]
    win_probability: float
    confidence_level: float
    reasoning_chain: List[str]
    key_factors: List[str]
    raw_llm_response: str = ""
    raw_llm_response: str = ""

class RateLimiter:
    """Rate limiter for API calls per model"""

    def __init__(self):
        from collections import defaultdict
        from datetime import datetime, timedelta
        self.call_times = defaultdict(list)

    async def wait_if_needed(self, model_key: str, rpm_limit: int):
        """Wait if we're at the rate limit for this model"""
        from datetime import datetime, timedelta

        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)

        # Remove calls older than 1 minute
        self.call_times[model_key] = [t for t in self.call_times[model_key] if t > minute_ago]

        # If at limit, wait
        if len(self.call_times[model_key]) >= rpm_limit:
            wait_time = 60 - (now - self.call_times[model_key][0]).total_seconds()
            if wait_time > 0:
                logger.info(f"⏳ Rate limit reached for {model_key}, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time + 1)

        # Record this call
        self.call_times[model_key].append(now)

class RealLLMPredictionGenerator:
    """Generates real predictions using LLM API calls"""

    def __init__(self, config_manager: ExpertConfigurationManager):
        """Initialize the real LLM prediction generator"""
        self.config_manager = config_manager

        # Initialize OpenRouter client
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.openrouter_api_key:
            logger.warning("⚠️ OPENROUTER_API_KEY not found - LLM predictions will be simulated")
            self.llm_available = False
        else:
            self.llm_available = True
            logger.info("✅ OpenRouter API key configured")

        # OpenRouter configuration
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"

        # Rate limiter for all models
        self.rate_limiter = RateLimiter()

        logger.info("✅ Real LLM Prediction Generator initialized with parallel processing")

    async def generate_real_prediction(self, expert_type: ExpertType, game_context: Dict[str, Any],
                                     retrieved_memories: List[RetrievedMemory],
                                     prediction_type: PredictionType = PredictionType.WINNER) -> GamePrediction:
        """Generate a real prediction using LLM API call"""

        logger.info(f"🤖 Generating real LLM prediction for {expert_type.value}")

        try:
            # Get expert configuration
            config = self.config_manager.get_configuration(expert_type)
            if not config:
                raise ValueError(f"No configuration found for {expert_type}")

            # Create LLM request
            request = LLMPredictionRequest(
                expert_type=expert_type,
                expert_config=config,
                game_context=game_context,
                retrieved_memories=retrieved_memories,
                prediction_type=prediction_type
            )

            # Generate prediction using LLM
            if self.llm_available:
                llm_response = await self._call_llm_for_prediction(request)
            else:
                # Fallback to enhanced simulation if LLM not available
                llm_response = await self._simulate_enhanced_prediction(request)

            # Create GamePrediction object
            prediction = GamePrediction(
                expert_type=expert_type,
                prediction_type=prediction_type,
                predicted_winner=llm_response.predicted_winner,
                win_probability=llm_response.win_probability,
                confidence_level=llm_response.confidence_level,
                reasoning_chain=llm_response.reasoning_chain,
                key_factors=llm_response.key_factors,
                retrieved_memories_used=len(retrieved_memories),
                prediction_timestamp=datetime.now()
            )

            logger.info(f"✅ Generated prediction: {llm_response.predicted_winner} ({llm_response.win_probability:.1%} confidence)")
            return prediction

        except Exception as e:
            logger.error(f"❌ Failed to generate prediction for {expert_type.value}: {e}")
            raise

    async def generate_all_predictions_parallel(self, game_context: Dict[str, Any],
                                              memory_results: Dict[str, MemoryRetrievalResult]) -> Dict[str, GamePrediction]:
        """Generate predictions from all 15 experts in parallel using their assigned models"""

        logger.info(f"🚀 Generating predictions from all 15 experts in parallel")

        # Create tasks for all experts
        tasks = []
        expert_list = list(ExpertType)

        for expert_type in expert_list:
            # Get memories for this expert
            memory_result = memory_results.get(expert_type.value, None)
            retrieved_memories = memory_result.retrieved_memories if memory_result else []

            # Create task for this expert
            task = self._generate_single_expert_prediction(expert_type, game_context, retrieved_memories)
            tasks.append((expert_type, task))

        # Execute all predictions concurrently
        logger.info(f"⚡ Running {len(tasks)} expert predictions concurrently...")
        results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)

        # Process results
        predictions = {}
        for i, (expert_type, result) in enumerate(zip([t[0] for t in tasks], results)):
            if isinstance(result, Exception):
                logger.error(f"❌ Prediction failed for {expert_type.value}: {result}")
                # Create fallback prediction
                predictions[expert_type.value] = await self._create_fallback_prediction(expert_type, game_context)
            else:
                predictions[expert_type.value] = result

        logger.info(f"✅ Completed parallel predictions: {len(predictions)} experts")
        return predictions

    async def _generate_single_expert_prediction(self, expert_type: ExpertType,
                                               game_context: Dict[str, Any],
                                               retrieved_memories: List[RetrievedMemory]) -> GamePrediction:
        """Generate prediction for a single expert using their assigned model"""

        # Get model assignment for this expert
        model_config = EXPERT_MODEL_ASSIGNMENTS.get(expert_type)
        if not model_config:
            raise ValueError(f"No model assigned to {expert_type.value}")

        # Get expert configuration
        config = self.config_manager.get_configuration(expert_type)
        if not config:
            raise ValueError(f"No configuration found for {expert_type}")

        # Create request
        request = LLMPredictionRequest(
            expert_type=expert_type,
            expert_config=config,
            game_context=game_context,
            retrieved_memories=retrieved_memories,
            prediction_type=PredictionType.WINNER
        )

        # Generate prediction using assigned model
        if self.llm_available:
            llm_response = await self._call_llm_with_model(request, model_config)
        else:
            llm_response = await self._simulate_enhanced_prediction(request)

        # Create GamePrediction object
        return GamePrediction(
            expert_type=expert_type,
            prediction_type=PredictionType.WINNER,
            predicted_winner=llm_response.predicted_winner,
            win_probability=llm_response.win_probability,
            confidence_level=llm_response.confidence_level,
            reasoning_chain=llm_response.reasoning_chain,
            key_factors=llm_response.key_factors,
            prediction_timestamp=datetime.now()
        )

    async def _call_llm_with_model(self, request: LLMPredictionRequest, model_config: Dict[str, Any]) -> LLMPredictionResponse:
        """Make LLM API call using specific model configuration"""

        model_key = f"{model_config['provider']}:{model_config['model']}"

        # Apply rate limiting for this specific model
        await self.rate_limiter.wait_if_needed(model_key, model_config['rpm_limit'])

        # Build the prompt
        prompt = self._build_expert_prompt(request)

        # Make API call with assigned model
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://nfl-predictor.com",
            "X-Title": "NFL Expert Predictor"
        }

        payload = {
            "model": model_config['model'],
            "messages": [
                {"role": "system", "content": self._get_system_prompt(request.expert_config)},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(self.openrouter_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        llm_text = data['choices'][0]['message']['content']
                        logger.debug(f"✅ LLM response for {request.expert_type.value} using {model_config['model']}")
                        return self._parse_llm_response(llm_text, request)
                    else:
                        error_text = await response.text()
                        raise Exception(f"API call failed: {response.status} {error_text}")

        except Exception as e:
            logger.error(f"❌ LLM call failed for {request.expert_type.value} using {model_config['model']}: {e}")
            # Fallback to simulation
            return await self._simulate_enhanced_prediction(request)

    async def _create_fallback_prediction(self, expert_type: ExpertType, game_context: Dict[str, Any]) -> GamePrediction:
        """Create a fallback prediction when expert prediction fails"""

        return GamePrediction(
            expert_type=expert_type,
            prediction_type=PredictionType.WINNER,
            predicted_winner=game_context.get('home_team', 'HOME'),
            win_probability=0.5,
            confidence_level=0.1,
            reasoning_chain=[f"Fallback prediction for {expert_type.value} due to API failure"],
            key_factors=["api_failure_fallback"],
            prediction_timestamp=datetime.now()
        )

    async def _call_llm_for_prediction(self, request: LLMPredictionRequest) -> LLMPredictionResponse:
        """Make actual LLM API call to generate prediction"""

        # Rate limiting
        await self._enforce_rate_limit()

        # Build the prompt
        prompt = self._build_expert_prompt(request)

        try:
            # Make OpenAI API call
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self._get_system_prompt(request.expert_config)},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7,
                top_p=0.9
            )

            # Parse LLM response
            llm_text = response.choices[0].message.content
            parsed_response = self._parse_llm_response(llm_text, request)

            logger.debug(f"🤖 LLM response for {request.expert_type.value}: {llm_text[:100]}...")
            return parsed_response

        except Exception as e:
            logger.error(f"❌ LLM API call failed: {e}")
            # Fallback to enhanced simulation
            return await self._simulate_enhanced_prediction(request)

    def _get_system_prompt(self, config: ExpertConfiguration) -> str:
        """Get system prompt for the expert"""

        return f"""You are {config.name}, an NFL prediction expert with the following personality and approach:

PERSONALITY: {config.description}

ANALYTICAL FOCUS: You prioritize these factors in your analysis:
{self._format_analytical_focus(config.analytical_focus)}

CONFIDENCE STYLE: Your base confidence threshold is {config.confidence_threshold:.1%}. You tend to be {'more confident' if config.confidence_threshold > 0.6 else 'more cautious'} in your predictions.

DECISION MAKING: {config.decision_making_style}

Your job is to analyze NFL games and make predictions that reflect your unique analytical approach and personality. Always stay in character and provide reasoning that matches your expertise and style."""

    def _format_analytical_focus(self, focus: Dict[str, float]) -> str:
        """Format analytical focus for prompt"""

        sorted_factors = sorted(focus.items(), key=lambda x: x[1], reverse=True)
        formatted = []

        for factor, weight in sorted_factors[:5]:  # Top 5 factors
            factor_name = factor.replace('_', ' ').title()
            importance = "Very High" if weight > 0.8 else "High" if weight > 0.6 else "Moderate" if weight > 0.4 else "Low"
            formatted.append(f"- {factor_name}: {importance} ({weight:.1%})")

        return '\n'.join(formatted)

    def _build_expert_prompt(self, request: LLMPredictionRequest) -> str:
        """Build the prediction prompt for the expert"""

        game_context = request.game_context
        memories = request.retrieved_memories

        # Basic game information
        home_team = game_context.get('home_team', 'HOME')
        away_team = game_context.get('away_team', 'AWAY')
        week = game_context.get('week', 'Unknown')
        season = game_context.get('season', 'Unknown')

        prompt = f"""Analyze this NFL game and make your prediction:

GAME: {away_team} @ {home_team}
SEASON: {season}, Week {week}
DATE: {game_context.get('game_date', 'Unknown')}

GAME CONTEXT:
"""

        # Add available context
        if game_context.get('weather'):
            weather = game_context['weather']
            prompt += f"Weather: {weather.get('temperature', 'Unknown')}°F"
            if weather.get('wind_speed'):
                prompt += f", Wind: {weather['wind_speed']} mph"
            prompt += "\n"

        if game_context.get('spread_line'):
            prompt += f"Spread: {home_team} {game_context['spread_line']:+.1f}\n"

        if game_context.get('total_line'):
            prompt += f"Total: {game_context['total_line']}\n"

        if game_context.get('division_game'):
            prompt += "Division Game: Yes\n"

        # Add betting information if available
        if game_context.get('home_moneyline') and game_context.get('away_moneyline'):
            prompt += f"Moneylines: {home_team} {game_context['home_moneyline']:+d}, {away_team} {game_context['away_moneyline']:+d}\n"

        # Add relevant memories
        if memories:
            prompt += f"\nRELEVANT MEMORIES FROM YOUR PAST ANALYSIS:\n"
            for i, memory in enumerate(memories[:3], 1):  # Top 3 memories
                prompt += f"{i}. {memory.memory.content} (Age: {memory.decay_score.age_days} days)\n"

        # Add expert-specific analysis request
        expert_type = request.expert_type

        if expert_type == ExpertType.MOMENTUM_RIDER:
            prompt += f"\nAs The Momentum Rider, focus on recent team performance, winning/losing streaks, and momentum indicators."
        elif expert_type == ExpertType.CONTRARIAN_REBEL:
            prompt += f"\nAs The Contrarian Rebel, look for opportunities to fade public opinion and popular narratives."
        # Removed WEATHER_SPECIALIST reference - expert type no longer exists
        elif expert_type == ExpertType.CHAOS_THEORY_BELIEVER:
            prompt += f"\nAs The Chaos Theory Believer, acknowledge the inherent unpredictability while making your best guess."
        elif expert_type == ExpertType.FUNDAMENTALIST_SCHOLAR:
            prompt += f"\nAs The Fundamentalist Scholar, rely on deep research and statistical analysis."

        prompt += f"""

PROVIDE YOUR ANALYSIS IN THIS EXACT FORMAT:

WINNER: [HOME or AWAY]
WIN_PROBABILITY: [0.15 to 0.85 as decimal]
CONFIDENCE: [0.05 to 0.95 as decimal]

REASONING:
1. [First key factor and analysis]
2. [Second key factor and analysis]
3. [Third key factor and analysis]

KEY_FACTORS: [comma-separated list of 3-5 key factors you considered]

Remember to stay true to your analytical approach and personality. Provide specific reasoning that reflects your expertise."""

        return prompt

    def _parse_llm_response(self, llm_text: str, request: LLMPredictionRequest) -> LLMPredictionResponse:
        """Parse the LLM response into structured prediction"""

        try:
            lines = llm_text.strip().split('\n')

            # Initialize defaults
            predicted_winner = None
            win_probability = 0.5
            confidence_level = 0.5
            reasoning_chain = []
            key_factors = []

            # Parse structured response
            current_section = None

            for line in lines:
                line = line.strip()

                if line.startswith('WINNER:'):
                    winner_text = line.replace('WINNER:', '').strip().upper()
                    if 'HOME' in winner_text:
                        predicted_winner = request.game_context.get('home_team', 'HOME')
                    elif 'AWAY' in winner_text:
                        predicted_winner = request.game_context.get('away_team', 'AWAY')

                elif line.startswith('WIN_PROBABILITY:'):
                    try:
                        prob_text = line.replace('WIN_PROBABILITY:', '').strip()
                        win_probability = float(prob_text)
                        win_probability = max(0.15, min(0.85, win_probability))  # Enforce bounds
                    except ValueError:
                        pass

                elif line.startswith('CONFIDENCE:'):
                    try:
                        conf_text = line.replace('CONFIDENCE:', '').strip()
                        confidence_level = float(conf_text)
                        confidence_level = max(0.05, min(0.95, confidence_level))  # Enforce bounds
                    except ValueError:
                        pass

                elif line.startswith('REASONING:'):
                    current_section = 'reasoning'

                elif line.startswith('KEY_FACTORS:'):
                    factors_text = line.replace('KEY_FACTORS:', '').strip()
                    key_factors = [f.strip() for f in factors_text.split(',') if f.strip()]

                elif current_section == 'reasoning' and line and not line.startswith('KEY_FACTORS:'):
                    # Clean up reasoning line
                    clean_line = line.lstrip('0123456789. -').strip()
                    if clean_line:
                        reasoning_chain.append(clean_line)

            # Ensure we have a winner
            if not predicted_winner:
                predicted_winner = request.game_context.get('home_team', 'HOME')

            # Adjust win probability if needed
            if predicted_winner == request.game_context.get('away_team'):
                win_probability = 1.0 - win_probability

            # Ensure we have reasoning
            if not reasoning_chain:
                reasoning_chain = [f"Analysis supports {predicted_winner} based on {request.expert_type.value} methodology"]

            # Ensure we have key factors
            if not key_factors:
                key_factors = ["team_strength", "matchup_analysis", "situational_factors"]

            return LLMPredictionResponse(
                predicted_winner=predicted_winner,
                win_probability=win_probability,
                confidence_level=confidence_level,
                reasoning_chain=reasoning_chain,
                key_factors=key_factors,
                raw_llm_response=llm_text
            )

        except Exception as e:
            logger.error(f"❌ Failed to parse LLM response: {e}")
            # Return fallback response
            return self._create_fallback_response(request, llm_text)

    def _create_fallback_response(self, request: LLMPredictionRequest, raw_response: str) -> LLMPredictionResponse:
        """Create fallback response if parsing fails"""

        return LLMPredictionResponse(
            predicted_winner=request.game_context.get('home_team', 'HOME'),
            win_probability=0.55,
            confidence_level=0.5,
            reasoning_chain=[f"Analysis by {request.expert_config.name} supports this prediction"],
            key_factors=["team_analysis", "situational_factors"],
            raw_llm_response=raw_response
        )

    async def _simulate_enhanced_prediction(self, request: LLMPredictionRequest) -> LLMPredictionResponse:
        """Enhanced simulation when LLM is not available"""

        logger.info(f"🎭 Simulating enhanced prediction for {request.expert_type.value}")

        expert_type = request.expert_type
        config = request.expert_config
        game_context = request.game_context

        # Expert-specific prediction logic (enhanced from original)
        home_team = game_context.get('home_team', 'HOME')
        away_team = game_context.get('away_team', 'AWAY')

        if expert_type == ExpertType.CHAOS_THEORY_BELIEVER:
            win_probability = 0.50 + (hash(f"{home_team}{away_team}") % 100 - 50) / 1000  # Slight randomness
            confidence_level = 0.15  # Always low confidence
            reasoning = [
                "Chaos theory suggests this game is inherently unpredictable",
                "Random events and butterfly effects will dominate the outcome",
                "Traditional analysis fails in chaotic systems like NFL games"
            ]
            key_factors = ["chaos_theory", "unpredictability", "random_events"]

        elif expert_type == ExpertType.CONTRARIAN_REBEL:
            # Look for contrarian opportunities
            public_home = game_context.get('public_betting', {}).get('home', 50)
            if public_home >= 70:
                win_probability = 0.35  # Fade heavy public home betting
                reasoning = [
                    f"Public heavily on home team ({public_home}%) - classic fade spot",
                    "When everyone thinks the same, no one thinks at all",
                    "Contrarian value lies with the unpopular away team"
                ]
            elif public_home <= 30:
                win_probability = 0.65  # Fade heavy public away betting
                reasoning = [
                    f"Public heavily on away team ({100-public_home}%) - fade the crowd",
                    "Contrarian approach suggests home team has hidden value",
                    "Market overreaction creates opportunity"
                ]
            else:
                win_probability = 0.50
                reasoning = [
                    "Public split - looking for other contrarian angles",
                    "No clear fade opportunity in betting percentages",
                    "Seeking alternative contrarian value"
                ]
            confidence_level = 0.65
            key_factors = ["public_betting", "contrarian_value", "market_sentiment"]

        elif expert_type == ExpertType.MOMENTUM_RIDER:
            # Focus on momentum indicators
            momentum = game_context.get('momentum', {})
            home_momentum = momentum.get('home', '')
            away_momentum = momentum.get('away', '')

            if 'hot' in home_momentum.lower() or 'winning' in home_momentum.lower():
                win_probability = 0.70
                reasoning = [
                    f"Home team riding hot streak: {home_momentum}",
                    "Momentum is a powerful force in NFL - ride the wave",
                    "Hot teams find ways to win games"
                ]
            elif 'hot' in away_momentum.lower() or 'winning' in away_momentum.lower():
                win_probability = 0.30
                reasoning = [
                    f"Away team on fire: {away_momentum}",
                    "Road momentum is especially powerful",
                    "Confident teams play better away from home"
                ]
            else:
                win_probability = 0.55
                reasoning = [
                    "No clear momentum advantage for either team",
                    "Looking for subtle momentum indicators",
                    "Slight edge to home team in neutral momentum spot"
                ]
            confidence_level = 0.75
            key_factors = ["team_momentum", "recent_performance", "winning_streaks"]

        else:
            # Default enhanced logic for other experts
            win_probability = 0.55
            confidence_level = config.confidence_threshold
            reasoning = [
                f"Analysis by {config.name} supports this prediction",
                "Multiple factors align to support this outcome",
                "Confidence based on analytical methodology"
            ]
            key_factors = ["team_analysis", "matchup_factors", "situational_context"]

        # Incorporate memories if available
        if request.retrieved_memories:
            memory_adjustment = 0.0
            memory_reasoning = []

            for memory in request.retrieved_memories[:2]:  # Top 2 memories
                memory_content = memory.memory.content.lower()
                memory_weight = memory.decay_score.final_weighted_score

                if home_team.lower() in memory_content:
                    memory_adjustment += 0.05 * memory_weight
                    memory_reasoning.append(f"Past experience with {home_team}: {memory.memory.content[:50]}...")
                elif away_team.lower() in memory_content:
                    memory_adjustment -= 0.05 * memory_weight
                    memory_reasoning.append(f"Past experience with {away_team}: {memory.memory.content[:50]}...")

            win_probability += memory_adjustment
            win_probability = max(0.15, min(0.85, win_probability))

            if memory_reasoning:
                reasoning.extend(memory_reasoning)

        # Determine winner
        if win_probability > 0.5:
            predicted_winner = home_team
        else:
            predicted_winner = away_team
            win_probability = 1.0 - win_probability

        return LLMPredictionResponse(
            predicted_winner=predicted_winner,
            win_probability=win_probability,
            confidence_level=confidence_level,
            reasoning_chain=reasoning,
            key_factors=key_factors,
            raw_llm_response=f"Enhanced simulation for {expert_type.value}"
        )

    async def _enforce_rate_limit(self):
        """Enforce rate limiting for API calls"""

        current_time = datetime.now()

        # Remove requests older than 1 minute
        self.last_request_times = [
            t for t in self.last_request_times
            if (current_time - t).total_seconds() < 60
        ]

        # Check if we're at the limit
        if len(self.last_request_times) >= self.requests_per_minute:
            sleep_time = 60 - (current_time - self.last_request_times[0]).total_seconds()
            if sleep_time > 0:
                logger.info(f"⏱️ Rate limiting: sleeping {sleep_time:.1f} seconds")
                await asyncio.sleep(sleep_time)

        # Record this request
        self.last_request_times.append(current_time)


async def main():
    """Test the Real LLM Prediction Generator"""
    print("🤖 Real LLM Prediction Generator Test")
    print("=" * 60)

    from training.expert_configuration import ExpertConfigurationManager
    from training.memory_retrieval_system import RetrievedMemory, GameMemory, DecayScore

    # Initialize components
    config_manager = ExpertConfigurationManager()
    generator = RealLLMPredictionGenerator(config_manager)

    # Create test game context
    test_game_context = {
        'game_id': 'test_game_001',
        'home_team': 'Chiefs',
        'away_team': 'Raiders',
        'season': 2020,
        'week': 15,
        'game_date': '2020-12-13',
        'weather': {'temperature': 35, 'wind_speed': 12},
        'spread_line': -7.0,
        'total_line': 52.5,
        'division_game': True,
        'public_betting': {'home': 75}
    }

    # Create test memories
    test_memories = [
        RetrievedMemory(
            memory=GameMemory(
                memory_id='mem_001',
                memory_type='reasoning',
                content='Chiefs struggle in cold weather divisional games',
                game_context={},
                outcome_data=None,
                created_date=datetime.now()
            ),
            decay_score=DecayScore(
                base_score=0.8,
                age_days=30,
                temporal_decay=0.9,
                final_weighted_score=0.72
            ),
            similarity_explanation='Similar cold weather divisional context',
            relevance_rank=1
        )
    ]

    # Test different expert types
    test_experts = [
        ExpertType.MOMENTUM_RIDER,
        ExpertType.CONTRARIAN_REBEL,
        ExpertType.CHAOS_THEORY_BELIEVER
    ]

    for expert_type in test_experts:
        print(f"\n🎯 Testing {expert_type.value}:")

        try:
            prediction = await generator.generate_real_prediction(
                expert_type, test_game_context, test_memories
            )

            print(f"   Winner: {prediction.predicted_winner}")
            print(f"   Probability: {prediction.win_probability:.1%}")
            print(f"   Confidence: {prediction.confidence_level:.1%}")
            print(f"   Key Factors: {', '.join(prediction.key_factors)}")
            print(f"   Reasoning:")
            for i, reason in enumerate(prediction.reasoning_chain, 1):
                print(f"     {i}. {reason}")

        except Exception as e:
            print(f"   ❌ Failed: {e}")

    print(f"\n✅ Real LLM Prediction Generator test completed!")


if __name__ == "__main__":
    asyncio.run(main())
