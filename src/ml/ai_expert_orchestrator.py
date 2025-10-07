#!/usr/bin/env pytho
"""
AI Expert Orchestrator - Core Functionality

Coordinates the complete AI thinking process for each expert, integrating:
- Memory retrieval using SupabaseEpisodicMemoryManager
- Personality-driven analysis using PersonalityProfile
- Structured AI calls using existing model assignments
- Comprehensive prediction generation across 30+ categories

This orchestrator implements the sophisticated AI thinking process outlined
in the NFL Expert Prediction System requirements.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import json
import asyncio
import time

from .supabase_memory_services import SupabaseEpisodicMemoryManager
from .personality_driven_experts import PersonalityProfile, PersonalityTrait
from .comprehensive_expert_predictions import (
    ComprehensiveExpertPrediction, GameContext, MemoryInfluence,
    PredictionWithConfidence, QuarterPrediction, PlayerPropPrediction
)
from .expert_configuration_service import ExpertConfigurationService
from .performance_monitor import (
    PerformanceMonitor, PerformanceMetricType, performance_timer,
    get_performance_monitor, record_performance_metric
)
from .memory_cache import (
    MemoryCache, MemoryCacheKeyGenerator, get_memory_cache,
    cache_memory_retrieval, get_cached_memory_retrieval, CacheEntryType
)
from .api_rate_limiter import APICallManager, get_api_call_manager, RetryConfig
from .error_handler import (
    ComprehensiveErrorHandler, ErrorContext, ErrorCategory,
    get_error_handler, handle_error_with_fallback
)
from .graceful_degradation import (
    GracefulDegradationManager, get_degradation_manager
)

logger = logging.getLogger(__name__)

class AIExpertOrchestrator:
    """
    Orchestrates the complete AI thinking process for NFL expert predictions.

    This class coordinates:
    1. Memory retrieval from episodic memory system
    2. AI-powered analysis using expert personalities
    3. Comprehensive prediction generation across all categories
    4. Memory influence tracking and explanation
    """

    def __init__(self, supabase_client, ai_client=None):
        """
        Initialize the AI Expert Orchestrator.

        Args:
            supabase_client: Supabase client for database operations
            ai_client: AI client for model interactions (optional, will create if needed)
        """
        self.supabase = supabase_client
        self.memory_service = SupabaseEpisodicMemoryManager(supabase_client)

        # Initialize expert configuration service
        self.expert_config_service = ExpertConfigurationService()
        logger.info("✅ Expert configuration service initialized")

        # Initialize performance monitoring and optimization components
        self.performance_monitor = get_performance_monitor()
        self.memory_cache = get_memory_cache()
        self.api_call_manager = get_api_call_manager()
        self.cache_key_generator = MemoryCacheKeyGenerator()

        # Initialize error handling and graceful degradation
        self.error_handler = get_error_handler()
        self.degradation_manager = get_degradation_manager()

        logger.info("✅ Performance optimization and error handling components initialized")

        # Initialize AI client if not provided
        if ai_client is None:
            try:
                from ..services.unified_ai_client import UnifiedAIClient
                self.ai_client = UnifiedAIClient()
            except ImportError:
                logger.warning("UnifiedAIClient not available, will need to be provided externally")
                self.ai_client = None
        else:
            self.ai_client = ai_client

        # Expert model assignments from existing training system
        self.expert_model_mapping = {
            'conservative_analyzer': {
                'name': 'The Analyst',
                'model': 'anthropic/claude-sonnet-4.5',
                'personality': 'Conservative, methodical, data-driven analysis',
                'specialty': 'Risk-averse predictions with statistical backing'
            },
            'risk_taking_gambler': {
                'name': 'The Gambler',
                'model': 'x-ai/grok-4-fast',
                'personality': 'Bold, high-risk, high-reward mentality',
                'specialty': 'Aggressive betting strategies and upset picks'
            },
            'contrarian_rebel': {
                'name': 'The Rebel',
                'model': 'google/gemini-2.5-flash-preview-09-2025',
                'personality': 'Goes against popular opinion and conventional wisdom',
                'specialty': 'Contrarian plays and market inefficiencies'
            },
            'value_hunter': {
                'name': 'The Hunter',
                'model': 'deepseek/deepseek-chat-v3.1:free',
                'personality': 'Seeks undervalued opportunities and hidden gems',
                'specialty': 'Finding value in overlooked situations'
            },
            'momentum_rider': {
                'name': 'The Rider',
                'model': 'openai/gpt-5',
                'personality': 'Follows trends and momentum patterns',
                'specialty': 'Momentum-based predictions and trend analysis'
            },
            # Additional experts from the 15-expert system
            'fundamentalist_scholar': {
                'name': 'The Scholar',
                'model': 'anthropic/claude-sonnet-4.5',
                'personality': 'Deep statistical analysis and historical patterns',
                'specialty': 'Fundamental analysis and long-term trends'
            },
            'chaos_theory_believer': {
                'name': 'The Chaos',
                'model': 'x-ai/grok-4-fast',
                'personality': 'Embraces unpredictability and random events',
                'specialty': 'Chaos theory and unexpected outcomes'
            },
            'gut_instinct_expert': {
                'name': 'The Intuition',
                'model': 'openai/gpt-5',
                'personality': 'Relies on intuition and feel for the game',
                'specialty': 'Intuitive analysis and gut feelings'
            },
            'statistics_purist': {
                'name': 'The Quant',
                'model': 'google/gemini-2.5-flash-preview-09-2025',
                'personality': 'Pure statistical analysis and mathematical models',
                'specialty': 'Quantitative analysis and statistical modeling'
            },
            'trend_reversal_specialist': {
                'name': 'The Reversal',
                'model': 'deepseek/deepseek-chat-v3.1:free',
                'personality': 'Identifies trend reversals and inflection points',
                'specialty': 'Trend reversal analysis and timing'
            },
            'popular_narrative_fader': {
                'name': 'The Fader',
                'model': 'anthropic/claude-sonnet-4.5',
                'personality': 'Fades popular narratives and media hype',
                'specialty': 'Anti-narrative analysis and media fade'
            },
            'sharp_money_follower': {
                'name': 'The Sharp',
                'model': 'openai/gpt-5',
                'personality': 'Follows professional betting patterns',
                'specialty': 'Sharp money analysis and line movement'
            },
            'underdog_champion': {
                'name': 'The Underdog',
                'model': 'x-ai/grok-4-fast',
                'personality': 'Champions underdogs and upset potential',
                'specialty': 'Underdog analysis and upset predictions'
            },
            'consensus_follower': {
                'name': 'The Consensus',
                'model': 'google/gemini-2.5-flash-preview-09-2025',
                'personality': 'Follows consensus and popular opinion',
                'specialty': 'Consensus analysis and market following'
            },
            'market_inefficiency_exploiter': {
                'name': 'The Exploiter',
                'model': 'deepseek/deepseek-chat-v3.1:free',
                'personality': 'Exploits market inefficiencies and pricing errors',
                'specialty': 'Market inefficiency analysis and arbitrage'
            }
        }

        # Performance tracking
        self.analysis_stats = {
            'total_analyses': 0,
            'successful_analyses': 0,
            'memory_retrievals': 0,
            'ai_calls': 0,
            'errors': []
        }

    async def analyze_game(self, expert_id: str, game_context: GameContext) -> ComprehensiveExpertPrediction:
        """
        Coordinate the complete expert thinking process for a game.

        This is the main orchestration method that:
        1. Retrieves relevant episodic memories (with caching)
        2. Generates AI-powered analysis using expert personality (with rate limiting)
        3. Creates comprehensive predictions across all categories
        4. Tracks memory influences and reasoning
        5. Records performance metrics

        Args:
            expert_id: Expert identifier (e.g., 'conservative_analyzer')
            game_context: Complete game context with all available data

        Returns:
            ComprehensiveExpertPrediction with all 30+ prediction categories

        Raises:
            ValueError: If expert_id is not recognized
            Exception: If analysis fails and cannot be recovered
        """
        # Use performance timer for the entire analysis
        with performance_timer(
            PerformanceMetricType.RESPONSE_TIME,
            f"expert_analysis_{expert_id}",
            expert_id,
            metadata={'game_id': game_context.game_id}
        ):
            # Validate expert exists in both mapping and configuration service
            if expert_id not in self.expert_model_mapping:
                raise ValueError(f"Unknown expert_id: {expert_id}. Available: {list(self.expert_model_mapping.keys())}")

            if not self.expert_config_service.validate_expert_exists(expert_id):
                logger.warning(f"⚠️ Expert {expert_id} not found in configuration service, using fallback")

            expert_config = self.expert_model_mapping[expert_id]
            logger.info(f"🧠 Starting analysis for {expert_config['name']} ({expert_id})")

            try:
                self.analysis_stats['total_analyses'] += 1

                # Step 1: Retrieve relevant episodic memories (with caching)
                logger.info(f"📚 Retrieving memories for {expert_config['name']}")
                memories = await self.retrieve_relevant_memories_cached(expert_id, game_context)
                self.analysis_stats['memory_retrievals'] += 1

                # Step 2: Generate AI-powered analysis (with rate limiting and retry)
                logger.info(f"🤖 Generating AI analysis for {expert_config['name']}")
                ai_analysis = await self.generate_ai_analysis_with_retry(expert_id, memories, game_context)
                self.analysis_stats['ai_calls'] += 1

                # Step 3: Create comprehensive prediction structure
                logger.info(f"📊 Building comprehensive prediction for {expert_config['name']}")
                prediction = await self._build_comprehensive_prediction(
                    expert_id, expert_config, game_context, memories, ai_analysis
                )

                # Step 4: Record success
                self.analysis_stats['successful_analyses'] += 1
                logger.info(f"✅ Analysis complete for {expert_config['name']}")

                # Add expert configuration summary to prediction for debugging
                if hasattr(prediction, 'expert_configuration_summary'):
                    prediction.expert_configuration_summary = self.expert_config_service.get_expert_summary(expert_id)

                return prediction

            except Exception as e:
                error_msg = f"Analysis failed for {expert_config['name']}: {str(e)}"
                logger.error(f"❌ {error_msg}")

                self.analysis_stats['errors'].append({
                    'expert_id': expert_id,
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat()
                })

                # Record error metric
                record_performance_metric(
                    PerformanceMetricType.ERROR_RATE,
                    f"expert_analysis_error_{expert_id}",
                    0.0,  # Duration not relevant for error
                    expert_id,
                    success=False,
                    error_message=error_msg
                )

                # Try to create a fallback prediction using graceful degradation
                try:
                    return await self._create_comprehensive_fallback_prediction(expert_id, expert_config, game_context, error_msg)
                except Exception as fallback_error:
                    logger.error(f"❌ Comprehensive fallback prediction also failed: {fallback_error}")
                    raise e

    async def retrieve_relevant_memories_cached(self, expert_id: str, game_context: GameContext, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant episodic memories with intelligent caching.

        Uses the memory cache to avoid repeated database queries for the same
        game context and expert combination.

        Args:
            expert_id: Expert identifier
            game_context: Current game context
            limit: Maximum number of memories to retrieve

        Returns:
            List of relevant memory dictionaries with similarity scores
        """
        # Generate cache key
        cache_key = self.cache_key_generator.generate_memory_retrieval_key(
            expert_id=expert_id,
            game_context=game_context.to_dict(),
            limit=limit,
            bucket_type="all"
        )

        # Try to get from cache first
        cached_memories = get_cached_memory_retrieval(cache_key)
        if cached_memories is not None:
            logger.debug(f"📋 Using cached memories for {expert_id} ({len(cached_memories)} memories)")
            record_performance_metric(
                PerformanceMetricType.CACHE_HIT,
                "memory_retrieval_cache_hit",
                0.0,
                expert_id
            )
            return cached_memories

        # Cache miss - retrieve from database with performance tracking and error handling
        try:
            with performance_timer(
                PerformanceMetricType.MEMORY_RETRIEVAL,
                f"memory_retrieval_{expert_id}",
                expert_id,
                metadata={'cache_miss': True}
            ):
                memories = await self.retrieve_relevant_memories(expert_id, game_context, limit)
        except Exception as e:
            # Handle memory retrieval failure with fallback
            logger.warning(f"⚠️ Memory retrieval failed for {expert_id}: {e}")

            memories = await handle_error_with_fallback(
                error=e,
                expert_id=expert_id,
                game_id=game_context.game_id,
                operation_name="memory_retrieval",
                metadata={'cache_miss': True}
            )

        # Cache the results
        cache_memory_retrieval(
            key=cache_key,
            data=memories,
            ttl_seconds=1800,  # 30 minutes TTL
            metadata={
                'expert_id': expert_id,
                'game_id': game_context.game_id,
                'memory_count': len(memories)
            }
        )

        record_performance_metric(
            PerformanceMetricType.CACHE_MISS,
            "memory_retrieval_cache_miss",
            0.0,
            expert_id
        )

        logger.debug(f"💾 Cached {len(memories)} memories for {expert_id}")
        return memories

    async def retrieve_relevant_memories(self, expert_id: str, game_context: GameContext, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant episodic memories for the current game context.

        Uses the existing SupabaseEpisodicMemoryManager with vector similarity search
        to find memories that are contextually relevant to the current game.

        Args:
            expert_id: Expert identifier
            game_context: Current game context
            limit: Maximum number of memories to retrieve

        Returns:
            List of relevant memory dictionaries with similarity scores
        """
        try:
            # Convert GameContext to the format expected by memory service
            memory_context = {
                'home_team': game_context.home_team,
                'away_team': game_context.away_team,
                'season': game_context.season,
                'week': game_context.week,
                'weather': game_context.weather_conditions,
                'injuries': {
                    'home': game_context.home_injuries,
                    'away': game_context.away_injuries
                },
                'is_divisional': game_context.is_divisional,
                'is_primetime': game_context.is_primetime,
                'playoff_implications': game_context.playoff_implications
            }

            # Use existing memory service with vector similarity search
            memories = await self.memory_service.retrieve_memories(
                expert_id=expert_id,
                game_context=memory_context,
                limit=limit,
                team_specific=True  # Use vector similarity search
            )

            # Apply expert-specific analytical focus weights to memory retrieval
            weighted_memories = self.expert_config_service.apply_analytical_focus_to_memory_retrieval(
                expert_id, memories
            )

            logger.info(f"📚 Retrieved and weighted {len(weighted_memories)} memories for {expert_id}")

            # Log memory types for debugging
            if weighted_memories:
                memory_types = {}
                for memory in weighted_memories:
                    mem_type = memory.get('memory_type', 'unknown')
                    memory_types[mem_type] = memory_types.get(mem_type, 0) + 1

                logger.debug(f"Memory types: {memory_types}")

            return weighted_memories

        except Exception as e:
            logger.warning(f"⚠️ Memory retrieval failed for {expert_id}: {e}")
            return []

    async def generate_ai_analysis_with_retry(self, expert_id: str, memories: List[Dict[str, Any]], game_context: GameContext) -> Dict[str, Any]:
        """
        Generate AI-powered analysis with rate limiting and retry logic.

        This method wraps the AI analysis generation with intelligent retry logic,
        rate limiting, and performance monitoring.

        Args:
            expert_id: Expert identifier
            memories: Retrieved episodic memories
            game_context: Current game context

        Returns:
            Dictionary containing AI analysis results and structured predictions
        """
        expert_config = self.expert_model_mapping[expert_id]
        model = expert_config.get('model', 'unknown')

        # Configure retry strategy for AI calls
        retry_config = RetryConfig(
            max_retries=3,
            base_delay_seconds=2.0,
            max_delay_seconds=30.0,
            backoff_multiplier=2.0,
            jitter=True
        )

        # Use API call manager for rate limiting and retry
        async def make_ai_call():
            with performance_timer(
                PerformanceMetricType.AI_CALL,
                f"ai_call_{expert_id}",
                expert_id,
                metadata={'model': model}
            ):
                return await self.generate_ai_analysis(expert_id, memories, game_context)

        # Make the API call with retry logic
        result = await self.api_call_manager.make_api_call(
            api_function=make_ai_call,
            model=model,
            retry_config=retry_config
        )

        if result.success:
            # Record successful API call metrics
            if result.rate_limited:
                record_performance_metric(
                    PerformanceMetricType.AI_CALL,
                    f"ai_call_rate_limited_{expert_id}",
                    result.total_delay_seconds * 1000,
                    expert_id,
                    metadata={'attempts': result.attempts, 'model': model}
                )

            return result.response
        else:
            # Handle failure
            error_msg = f"AI call failed after {result.attempts} attempts: {result.error}"
            logger.error(f"❌ {error_msg}")

            # Record error
            record_performance_metric(
                PerformanceMetricType.AI_CALL,
                f"ai_call_failed_{expert_id}",
                result.total_delay_seconds * 1000,
                expert_id,
                success=False,
                error_message=str(result.error),
                metadata={'attempts': result.attempts, 'model': model}
            )

            # Return fallback analysis
            return {
                'analysis_text': f"AI analysis failed for {expert_config['name']}: {error_msg}",
                'confidence_overall': 0.4,
                'key_factors': ['AI analysis unavailable'],
                'reasoning': f"Using fallback analysis due to API issues",
                'predictions': {},
                'error': str(result.error),
                'retry_attempts': result.attempts
            }

    async def generate_ai_analysis(self, expert_id: str, memories: List[Dict[str, Any]], game_context: GameContext) -> Dict[str, Any]:
        """
        Generate AI-powered analysis using expert personality and retrieved memories.

        This method creates structured prompts that include:
        - Expert personality and specialty
        - Retrieved episodic memories with context
        - Current game data and context
        - Request for comprehensive analysis across all prediction categories

        Args:
            expert_id: Expert identifier
            memories: Retrieved episodic memories
            game_context: Current game context

        Returns:
            Dictionary containing AI analysis results and structured predictions
        """
        if not self.ai_client:
            raise RuntimeError("AI client not available for analysis generation")

        expert_config = self.expert_model_mapping[expert_id]

        try:
            # Build comprehensive AI prompt (will be implemented in subtask 2.2)
            system_prompt, user_prompt = await self._build_comprehensive_ai_prompt(
                expert_id, expert_config, memories, game_context
            )

            # Get model assignment from expert configuration service
            model_assignment = self.expert_config_service.get_model_assignment(expert_id)
            if not model_assignment:
                model_assignment = expert_config['model']  # Fallback to hardcoded mapping
                logger.warning(f"Using fallback model assignment for {expert_id}: {model_assignment}")

            # Make AI call using assigned model
            logger.debug(f"🤖 Making AI call to {model_assignment} for {expert_config['name']}")

            # Use the AI client to generate analysis
            response = await self._make_ai_call(
                model=model_assignment,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                expert_name=expert_config['name']
            )

            # Parse and validate AI response (will be implemented in subtask 2.3)
            parsed_analysis = await self._parse_ai_response(response, expert_id, expert_config)

            return parsed_analysis

        except Exception as e:
            logger.error(f"❌ AI analysis generation failed for {expert_config['name']}: {e}")
            # Return a basic fallback analysis
            return {
                'analysis_text': f"Fallback analysis for {expert_config['name']} due to AI error: {str(e)}",
                'confidence_overall': 0.5,
                'key_factors': ['AI analysis unavailable'],
                'reasoning': f"Using fallback analysis due to technical issues",
                'predictions': {},
                'error': str(e)
            }

    async def _build_comprehensive_ai_prompt(self, expert_id: str, expert_config: Dict, memories: List[Dict], game_context: GameContext) -> Tuple[str, str]:
        """
        Build comprehensive AI prompts for expert analysis using the enhanced prompt system.

        This method uses the comprehensive prompt generation system from natural_language_prompt.py
        to create expert-specific system prompts and dynamic user prompts with memory context.
        """
        try:
            # Import the comprehensive prompt builder
            from ..prompts.natural_language_prompt import build_comprehensive_ai_prompt

            # Get personality profile from expert configuration service
            personality_profile = None
            try:
                expert_configuration = self.expert_config_service.get_expert_configuration(expert_id)
                if expert_configuration:
                    personality_profile = expert_configuration.personality_profile
                    logger.debug(f"Using configured personality profile for {expert_id}")
                else:
                    # Fallback to basic profile creation
                    personality_profile = self._create_basic_personality_profile(expert_id, expert_config)
                    logger.debug(f"Using fallback personality profile for {expert_id}")
            except Exception as e:
                logger.debug(f"Personality profile retrieval failed: {e}")
                personality_profile = self._create_basic_personality_profile(expert_id, expert_config)

            # Use the comprehensive prompt builder
            system_prompt, user_prompt = build_comprehensive_ai_prompt(
                expert_id=expert_id,
                expert_config=expert_config,
                memories=memories,
                game_context=game_context,
                personality_profile=personality_profile
            )

            logger.debug(f"Built comprehensive prompts for {expert_config['name']}: "
                        f"system={len(system_prompt)} chars, user={len(user_prompt)} chars")

            return system_prompt, user_prompt

        except Exception as e:
            logger.error(f"❌ Comprehensive prompt building failed for {expert_config['name']}: {e}")
            # Fallback to basic prompts
            return await self._build_basic_fallback_prompt(expert_id, expert_config, memories, game_context)

    def _create_basic_personality_profile(self, expert_id: str, expert_config: Dict) -> Any:
        """
        Create a basic personality profile from expert configuration.

        This is a temporary implementation that will be enhanced when the full
        personality system integration is complete.
        """
        try:
            from .personality_driven_experts import PersonalityProfile, PersonalityTrait

            # Create basic traits based on expert type
            traits = {}

            # Map expert types to personality traits
            trait_mappings = {
                'conservative_analyzer': {
                    'risk_tolerance': 0.2, 'analytics_trust': 0.9, 'optimism': 0.4,
                    'contrarian_tendency': 0.1, 'recent_bias': 0.3
                },
                'risk_taking_gambler': {
                    'risk_tolerance': 0.9, 'analytics_trust': 0.3, 'optimism': 0.7,
                    'contrarian_tendency': 0.6, 'recent_bias': 0.8
                },
                'contrarian_rebel': {
                    'risk_tolerance': 0.7, 'analytics_trust': 0.5, 'optimism': 0.3,
                    'contrarian_tendency': 0.9, 'recent_bias': 0.4
                },
                'value_hunter': {
                    'risk_tolerance': 0.4, 'analytics_trust': 0.8, 'optimism': 0.6,
                    'contrarian_tendency': 0.7, 'recent_bias': 0.2
                },
                'momentum_rider': {
                    'risk_tolerance': 0.6, 'analytics_trust': 0.6, 'optimism': 0.8,
                    'contrarian_tendency': 0.2, 'recent_bias': 0.9
                }
            }

            # Get trait values for this expert (default to balanced if not found)
            expert_traits = trait_mappings.get(expert_id, {
                'risk_tolerance': 0.5, 'analytics_trust': 0.5, 'optimism': 0.5,
                'contrarian_tendency': 0.5, 'recent_bias': 0.5
            })

            # Create PersonalityTrait objects
            for trait_name, value in expert_traits.items():
                traits[trait_name] = PersonalityTrait(
                    name=trait_name,
                    value=value,
                    stability=0.7,  # Moderately stable
                    influence_weight=0.8  # High influence
                )

            # Create personality profile
            profile = PersonalityProfile(
                traits=traits,
                decision_style="analytical" if expert_traits.get('analytics_trust', 0.5) > 0.6 else "intuitive",
                confidence_level=expert_traits.get('optimism', 0.5),
                learning_rate=0.1
            )

            return profile

        except Exception as e:
            logger.debug(f"Failed to create personality profile: {e}")
            return None

    async def _build_basic_fallback_prompt(self, expert_id: str, expert_config: Dict, memories: List[Dict], game_context: GameContext) -> Tuple[str, str]:
        """
        Build basic fallback prompts when comprehensive prompt building fails.
        """
        # Basic system prompt with expert personality
        system_prompt = f"""You are {expert_config['name']}, an NFL prediction expert.

PERSONALITY: {expert_config['personality']}
SPECIALTY: {expert_config['specialty']}

You analyze NFL games using your unique perspective and make comprehensive predictions across multiple categories.
Focus on your specialty areas while providing complete analysis."""

        # Basic user prompt with game context
        user_prompt = f"""Analyze this NFL matchup:

GAME: {game_context.away_team} @ {game_context.home_team}
Season: {game_context.season}, Week: {game_context.week}
Date: {game_context.game_date}

CONTEXT:
- Divisional Game: {game_context.is_divisional}
- Primetime: {game_context.is_primetime}
- Playoff Implications: {game_context.playoff_implications}

BETTING LINES:
- Spread: {game_context.current_spread}
- Total: {game_context.total_line}

MEMORIES: {len(memories)} relevant past experiences retrieved

Provide your analysis and predictions based on your expertise."""

        return system_prompt, user_prompt

    async def _make_ai_call(self, model: str, system_prompt: str, user_prompt: str, expert_name: str) -> str:
        """
        Make AI call using the specified model with structured JSON output requirements.

        This method makes actual AI calls using the configured model for each expert,
        implementing retry logic and error handling for robust operation.
        """
        try:
            if not self.ai_client:
                logger.warning(f"⚠️ No AI client available for {expert_name}, using fallback")
                return self._create_fallback_ai_response(expert_name, model)

            # Try to use the AI client (implementation depends on available client)
            try:
                # Check if we have OpenRouter service available
                from ..services.openrouter_service import OpenRouterService
                import os

                # Create OpenRouter client if we have the key
                openrouter_key = os.getenv('VITE_OPENROUTER_API_KEY') or os.getenv('OPENROUTER_API_KEY')
                if openrouter_key:
                    openrouter = OpenRouterService(openrouter_key)

                    logger.debug(f"🤖 Making OpenRouter call to {model} for {expert_name}")

                    response = openrouter.generate_completion(
                        system_message=system_prompt,
                        user_message=user_prompt,
                        model=model,
                        temperature=0.7,
                        max_tokens=1500  # Enough for comprehensive analysis
                    )

                    if hasattr(response, 'content') and response.content:
                        logger.info(f"✅ AI call successful for {expert_name} ({len(response.content)} chars)")
                        return response.content
                    else:
                        logger.warning(f"⚠️ Empty response from {model} for {expert_name}")
                        return self._create_fallback_ai_response(expert_name, model)

                else:
                    logger.warning(f"⚠️ No OpenRouter API key available for {expert_name}")
                    return self._create_fallback_ai_response(expert_name, model)

            except ImportError:
                logger.debug(f"OpenRouter service not available for {expert_name}")
                # Try unified AI client if available
                if hasattr(self.ai_client, 'generate_completion'):
                    response = await self.ai_client.generate_completion(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        model=model,
                        temperature=0.7,
                        max_tokens=1500
                    )
                    return response
                else:
                    return self._create_fallback_ai_response(expert_name, model)

        except Exception as e:
            logger.error(f"❌ AI call failed for {expert_name} using {model}: {e}")
            return self._create_fallback_ai_response(expert_name, model, error=str(e))

    def _create_fallback_ai_response(self, expert_name: str, model: str, error: str = None) -> str:
        """
        Create a fallback AI response when actual AI calls fail.

        This ensures the system can continue operating even when AI services are unavailable.
        """
        error_context = f" (Error: {error})" if error else ""

        return f"""ANALYSIS: {expert_name} analysis using fallback system{error_context}. Based on general NFL knowledge and expert specialty.

CORE PREDICTIONS:
WINNER: home
WINNER_CONFIDENCE: 55
SPREAD: -3.0
SPREAD_CONFIDENCE: 52
TOTAL: over
TOTAL_POINTS: 45.5
TOTAL_CONFIDENCE: 50
EXACT_SCORE: 24-21
MARGIN: 3

QUARTER PREDICTIONS:
Q1_HOME: 7
Q1_AWAY: 3
Q2_HOME: 10
Q2_AWAY: 7
Q3_HOME: 3
Q3_AWAY: 7
Q4_HOME: 4
Q4_AWAY: 4
FIRST_HALF_WINNER: home
HIGHEST_SCORING_QUARTER: 2

SITUATIONAL PREDICTIONS:
TURNOVER_DIFF: 0
RED_ZONE_EFF: 0.6
THIRD_DOWN_CONV: 0.4
TIME_OF_POSS: 30.5
TOTAL_SACKS: 3
TOTAL_PENALTIES: 8

ENVIRONMENTAL IMPACT:
WEATHER_IMPACT: 0.3
INJURY_IMPACT: 0.4
MOMENTUM_FACTOR: 0.5
SPECIAL_TEAMS: 0.5
COACHING_EDGE: 0.5

KEY_FACTORS: [Fallback analysis, General NFL trends, Expert specialty focus]
MEMORY_INFLUENCE: Limited due to technical issues
CONFIDENCE_OVERALL: 50"""

    async def _parse_ai_response(self, response: str, expert_id: str, expert_config: Dict) -> Dict[str, Any]:
        """
        Parse and validate AI response using comprehensive parsing system.

        This method uses the enhanced parsing system from natural_language_prompt.py
        to handle different model output formats and implement fallback parsing
        for malformed responses.
        """
        try:
            # Import the comprehensive parser
            from ..prompts.natural_language_prompt import parse_comprehensive_ai_response, create_fallback_parsed_response

            # Use the comprehensive parser
            parsed_analysis = parse_comprehensive_ai_response(
                response_text=response,
                expert_id=expert_id,
                expert_config=expert_config
            )

            # Log parsing results
            if parsed_analysis['parsing_success']:
                logger.info(f"✅ Successfully parsed response for {expert_config['name']}")
                if parsed_analysis['parsing_errors']:
                    logger.debug(f"   Parsing warnings: {len(parsed_analysis['parsing_errors'])}")
            else:
                logger.warning(f"⚠️ Parsing issues for {expert_config['name']}: {len(parsed_analysis['parsing_errors'])} errors")
                for error in parsed_analysis['parsing_errors'][:3]:  # Log first 3 errors
                    logger.debug(f"   • {error}")

            return parsed_analysis

        except Exception as e:
            logger.error(f"❌ Critical parsing error for {expert_config['name']}: {e}")

            # Create fallback response
            try:
                from ..prompts.natural_language_prompt import create_fallback_parsed_response
                return create_fallback_parsed_response(expert_id, expert_config, str(e))
            except ImportError:
                # Ultimate fallback if imports fail
                return {
                    'analysis_text': f"Critical parsing failure for {expert_config['name']}: {str(e)}",
                    'confidence_overall': 0.5,
                    'key_factors': ['Critical parsing error'],
                    'reasoning': f"Fallback analysis due to parsing failure",
                    'memory_influence': 'Unable to process',
                    'predictions': {
                        'winner': 'home',
                        'winner_confidence': 0.55,
                        'spread': 0.0,
                        'total': 'over',
                        'total_points': 45.0
                    },
                    'parsing_success': False,
                    'parsing_errors': [f'Critical error: {str(e)}']
                }

    async def _build_comprehensive_prediction(self, expert_id: str, expert_config: Dict, game_context: GameContext,
                                           memories: List[Dict], ai_analysis: Dict) -> ComprehensiveExpertPrediction:
        """
        Build comprehensive prediction structure from AI analysis.

        This method creates the full ComprehensiveExpertPrediction object with all
        30+ prediction categories based on the AI analysis results.
        """
        # Create memory influences from retrieved memories
        memory_influences = []
        for memory in memories:
            influence = MemoryInfluence(
                memory_id=memory.get('memory_id', 'unknown'),
                similarity_score=memory.get('similarity_score', 0.5),
                temporal_weight=memory.get('temporal_weight', 0.5),
                influence_strength=memory.get('similarity_score', 0.5) * memory.get('temporal_weight', 0.5),
                memory_summary=memory.get('lessons_learned', ['No summary'])[0] if memory.get('lessons_learned') else 'No summary',
                why_relevant=f"Similar game context for {expert_config['name']}",
                memory_type=memory.get('memory_type', 'unknown')
            )
            memory_influences.append(influence)

        # Apply personality consistency to AI analysis
        consistent_analysis = self.expert_config_service.ensure_personality_consistency(
            expert_id, ai_analysis
        )

        # Create comprehensive predictions from consistent AI analysis
        predictions = consistent_analysis.get('predictions', {})

        game_winner = PredictionWithConfidence(
            prediction=predictions.get('winner', 'home'),
            confidence=predictions.get('winner_confidence', 0.6),
            reasoning=ai_analysis.get('reasoning', f"{expert_config['name']}'s analysis based on {expert_config['specialty']}"),
            key_factors=ai_analysis.get('key_factors', ['AI analysis'])
        )

        # Create predictions from parsed AI analysis
        point_spread = PredictionWithConfidence(
            prediction="home" if predictions.get('spread', 0) < 0 else "away",
            confidence=predictions.get('spread_confidence', 0.55),
            reasoning="Spread analysis from AI",
            key_factors=['Line movement', 'Team matchup']
        )

        total_points = PredictionWithConfidence(
            prediction=predictions.get('total', 'over'),
            confidence=predictions.get('total_confidence', 0.52),
            reasoning="Total points analysis from AI",
            key_factors=['Offensive efficiency', 'Weather conditions']
        )

        # Create quarter predictions from AI analysis
        quarters = []
        for q in range(1, 5):
            home_key = f'q{q}_home'
            away_key = f'q{q}_away'
            home_score = predictions.get(home_key, 7)
            away_score = predictions.get(away_key, 6)

            quarter = QuarterPrediction(
                quarter=q,
                home_score=home_score,
                away_score=away_score,
                total_points=home_score + away_score,
                confidence=0.4,
                key_factors=[f'Q{q} analysis from AI']
            )
            quarters.append(quarter)

        # Create comprehensive prediction object
        prediction = ComprehensiveExpertPrediction(
            expert_id=expert_id,
            expert_name=expert_config['name'],
            game_context=game_context,

            # Core predictions
            game_winner=game_winner,
            point_spread=point_spread,
            total_points=total_points,
            moneyline=game_winner,  # Same as game winner for now
            exact_score=PredictionWithConfidence(
                predictions.get('exact_score', '24-21'), 0.3,
                "Score prediction from AI", ["Offensive analysis"]
            ),
            margin_of_victory=PredictionWithConfidence(
                predictions.get('margin', 3), 0.4,
                "Margin analysis from AI", ["Game flow"]
            ),

            # Quarter predictions
            q1_score=quarters[0],
            q2_score=quarters[1],
            q3_score=quarters[2],
            q4_score=quarters[3],
            first_half_winner=PredictionWithConfidence(
                predictions.get('first_half_winner', 'home'), 0.4,
                "First half analysis from AI", ["Early game script"]
            ),
            highest_scoring_quarter=PredictionWithConfidence(
                predictions.get('highest_scoring_quarter', 2), 0.3,
                "Quarter analysis from AI", ["Tempo", "Adjustments"]
            ),

            # Player props (empty lists for now, will be populated by AI analysis)
            qb_passing_yards=[],
            qb_touchdowns=[],
            qb_completions=[],
            qb_interceptions=[],
            rb_rushing_yards=[],
            rb_attempts=[],
            rb_touchdowns=[],
            wr_receiving_yards=[],
            wr_receptions=[],
            wr_touchdowns=[],

            # Situational predictions from AI analysis
            turnover_differential=PredictionWithConfidence(
                predictions.get('turnover_diff', 0), 0.5,
                "Turnover analysis from AI", ["Ball security", "Pressure"]
            ),
            red_zone_efficiency=PredictionWithConfidence(
                predictions.get('red_zone_eff', 0.6), 0.5,
                "Red zone analysis from AI", ["Goal line offense"]
            ),
            third_down_conversion=PredictionWithConfidence(
                predictions.get('third_down_conv', 0.4), 0.5,
                "Third down analysis from AI", ["Conversion efficiency"]
            ),
            time_of_possession=PredictionWithConfidence(
                predictions.get('time_of_poss', 30.0), 0.5,
                "TOP analysis from AI", ["Game control", "Pace"]
            ),
            sacks=PredictionWithConfidence(
                predictions.get('total_sacks', 3), 0.5,
                "Sack analysis from AI", ["Pass rush", "O-line protection"]
            ),
            penalties=PredictionWithConfidence(
                predictions.get('total_penalties', 8), 0.5,
                "Penalty analysis from AI", ["Discipline", "Officiating"]
            ),

            # Environmental/advanced predictions from AI analysis
            weather_impact=PredictionWithConfidence(
                predictions.get('weather_impact', 0.3), 0.6,
                "Weather analysis from AI", ["Conditions", "Playing style"]
            ),
            injury_impact=PredictionWithConfidence(
                predictions.get('injury_impact', 0.4), 0.7,
                "Injury analysis from AI", ["Key players", "Depth chart"]
            ),
            momentum_analysis=PredictionWithConfidence(
                predictions.get('momentum_factor', 0.6), 0.5,
                "Momentum analysis from AI", ["Recent form", "Confidence"]
            ),
            special_teams=PredictionWithConfidence(
                predictions.get('special_teams', 0.5), 0.4,
                "Special teams analysis from AI", ["Field position", "Return game"]
            ),
            coaching_matchup=PredictionWithConfidence(
                predictions.get('coaching_edge', 0.6), 0.5,
                "Coaching analysis from AI", ["Strategy", "Adjustments"]
            ),

            # Meta information
            confidence_overall=ai_analysis.get('confidence_overall', 0.6),
            reasoning=ai_analysis.get('reasoning', f"Analysis from {expert_config['name']}"),
            key_factors=ai_analysis.get('key_factors', ['Expert analysis']),
            prediction_timestamp=datetime.now(),
            memory_influences=memory_influences
        )

        return prediction

    async def _create_fallback_prediction(self, expert_id: str, expert_config: Dict, game_context: GameContext) -> ComprehensiveExpertPrediction:
        """
        Create a safe fallback prediction when analysis fails.

        This ensures the system can always return a valid prediction even when
        AI analysis or memory retrieval fails.
        """
        logger.warning(f"⚠️ Creating fallback prediction for {expert_config['name']}")

        # Create minimal AI analysis for fallback
        fallback_analysis = {
            'analysis_text': f"Fallback analysis for {expert_config['name']}",
            'confidence_overall': 0.5,
            'key_factors': ['Fallback analysis'],
            'reasoning': 'Technical issues prevented full analysis',
            'predictions': {
                'winner': 'home',
                'confidence': 0.5,
                'spread': 0.0,
                'total': 45.0
            }
        }

        # Use the same prediction building logic with fallback data
        return await self._build_comprehensive_prediction(
            expert_id, expert_config, game_context, [], fallback_analysis
        )

    def get_analysis_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the orchestrator."""
        success_rate = (self.analysis_stats['successful_analyses'] /
                       max(1, self.analysis_stats['total_analyses'])) * 100

        return {
            'total_analyses': self.analysis_stats['total_analyses'],
            'successful_analyses': self.analysis_stats['successful_analyses'],
            'success_rate': f"{success_rate:.1f}%",
            'memory_retrievals': self.analysis_stats['memory_retrievals'],
            'ai_calls': self.analysis_stats['ai_calls'],
            'error_count': len(self.analysis_stats['errors']),
            'recent_errors': self.analysis_stats['errors'][-5:] if self.analysis_stats['errors'] else []
        }

    async def initialize(self):
        """Initialize the orchestrator and its dependencies."""
        try:
            await self.memory_service.initialize()
            logger.info("✅ AI Expert Orchestrator initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI Expert Orchestrator: {e}")
            raise

    async def close(self):
        """Clean up resources."""
        try:
            await self.memory_service.close()
            logger.info("✅ AI Expert Orchestrator closed successfully")
        except Exception as e:
            logger.error(f"❌ Error closing AI Expert Orchestrator: {e}")
    async def _create_comprehensive_fallback_prediction(
        self,
        expert_id: str,
        expert_config: Dict[str, Any],
        game_context: GameContext,
        error_message: str
    ) -> ComprehensiveExpertPrediction:
        """
        Create a comprehensive fallback prediction when main analysis fails.

        Uses the graceful degradation system to create a minimal but valid
        prediction structure with fallback values.

        Args:
            expert_id: Expert identifier
            expert_config: Expert configuration
            game_context: Game context
            error_message: Original error message

        Returns:
            ComprehensiveExpertPrediction with fallback values
        """
        logger.info(f"🔄 Creating comprehensive fallback prediction for {expert_config['name']}")

        # Create minimal successful predictions (empty since everything failed)
        successful_predictions = {}

        # All categories failed
        failed_categories = {
            'game_winner', 'point_spread', 'total_points', 'moneyline', 'exact_score', 'margin_of_victory',
            'q1_score', 'q2_score', 'q3_score', 'q4_score', 'first_half_winner', 'highest_scoring_quarter',
            'turnover_differential', 'red_zone_efficiency', 'third_down_conversion', 'time_of_possession',
            'sacks', 'penalties', 'weather_impact', 'injury_impact', 'momentum_analysis',
            'special_teams', 'coaching_matchup'
        }

        # Create memory influence indicating system failure
        memory_influences = [MemoryInfluence(
            memory_id='system_failure',
            similarity_score=0.0,
            temporal_weight=0.0,
            influence_strength=0.0,
            memory_summary=f'System failure: {error_message[:100]}',
            why_relevant='System error prevented normal analysis',
            memory_type='system_error'
        )]

        # Use graceful degradation to create partial prediction
        return await self.degradation_manager.create_partial_prediction(
            expert_id=expert_id,
            expert_name=expert_config['name'],
            game_context=game_context,
            successful_predictions=successful_predictions,
            failed_categories=failed_categories,
            memory_influences=memory_influences
        )

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error handling statistics"""
        return self.error_handler.get_error_statistics()

    def get_degradation_statistics(self) -> Dict[str, Any]:
        """Get graceful degradation statistics"""
        return self.degradation_manager.get_degradation_statistics()

    def get_performance_health_report(self) -> Dict[str, Any]:
        """Get comprehensive performance and health report"""
        return {
            'analysis_stats': self.get_analysis_stats(),
            'error_stats': self.get_error_statistics(),
            'degradation_stats': self.get_degradation_statistics(),
            'performance_health': self.performance_monitor.get_system_health_report() if self.performance_monitor else None,
            'cache_stats': self.memory_cache.get_stats() if self.memory_cache else None,
            'api_call_stats': self.api_call_manager.get_stats() if self.api_call_manager else None
        }
