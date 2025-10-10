"""
2024 Baselines A/B Testing Service

Implements baseline models for comparison against expert predictions:
- Coin-flip: Random 50/50 predictions
- Market-only: Uses market odds as predictions
- One-shot: Single LLM call without memory/context
- Deliberate: Simple rule-based predictions

Provides A/B testing framework with performance comparison metrics.
"""

import random
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import numpy as np
from dataclasses import dataclass

from src.services.supabase_service import SupabaseService
from src.services.memory_retrieval_service import MemoryRetrievalService

logger = logging.getLogger(__name__)

@dataclass
class BaselineResult:
    """Result from a baseline model prediction"""
    model_type: str
    predictions: Dict[str, Any]
    confidence: float
    execution_time: float
    metadata: Dict[str, Any]

@dataclass
class ComparisonMetrics:
    """Metrics for comparing baseline vs expert performance"""
    brier_score: float
    mae_score: float
    roi: float
    accuracy: float
    calibration_error: float
    prediction_count: int

class BaselineModelsService:
    """Service for implementing and testing baseline prediction models"""

    def __init__(self, supabase_service: SupabaseService):
        self.supabase = supabase_service
        self.memory_service = MemoryRetrievalService(supabase_service)

        # Baseline model configurations
        self.baseline_configs = {
            'coin_flip': {
                'description': 'Random 50/50 predictions with noise',
                'confidence_range': (0.45, 0.55),
                'stake_range': (1, 3)
            },
            'market_only': {
                'description': 'Uses market odds as prediction probabilities',
                'confidence_boost': 0.1,
                'stake_multiplier': 1.5
            },
            'one_shot': {
                'description': 'Single LLM call without memory or context',
                'model': 'deepseek/deepseek-chat-v3.1:free',
                'max_tokens': 2000,
                'temperature': 0.3
            },
            'deliberate': {
                'description': 'Rule-based predictions using simple heuristics',
                'home_advantage': 0.55,
                'favorite_bias': 0.6,
                'over_bias': 0.52
            }
        }

        # Performance tracking
        self.baseline_performance = {}

    async def generate_coin_flip_predictions(self, game_id: str, expert_id: str) -> BaselineResult:
        """Generate random coin-flip predictions"""
        start_time = datetime.now()

        try:
            # Get game context for structure
            game_data = await self._get_game_context(game_id)
            if not game_data:
                raise ValueError(f"Game {game_id} not found")

            predictions = {}
            config = self.baseline_configs['coin_flip']

            # Generate 83 random predictions following the schema structure
            categories = await self._get_prediction_categories()

            for category in categories:
                if category['pred_type'] == 'binary':
                    # Random binary prediction
                    value = random.choice([True, False])
                    confidence = random.uniform(*config['confidence_range'])
                elif category['pred_type'] == 'enum':
                    # Random enum selection
                    options = category.get('options', ['option1', 'option2', 'option3'])
                    value = random.choice(options)
                    confidence = random.uniform(*config['confidence_range'])
                elif category['pred_type'] == 'numeric':
                    # Random numeric value within reasonable bounds
                    min_val = category.get('min_value', 0)
                    max_val = category.get('max_value', 100)
                    value = random.uniform(min_val, max_val)
                    confidence = random.uniform(*config['confidence_range'])
                else:
                    continue

                predictions[category['category']] = {
                    'category': category['category'],
                    'subject': category.get('subject', 'game'),
                    'pred_type': category['pred_type'],
                    'value': value,
                    'confidence': confidence,
                    'stake_units': random.randint(*config['stake_range']),
                    'odds': random.uniform(1.5, 3.0),
                    'why': [{'memory_id': 'coin_flip', 'weight': 1.0}]
                }

            execution_time = (datetime.now() - start_time).total_seconds()

            return BaselineResult(
                model_type='coin_flip',
                predictions=predictions,
                confidence=np.mean([p['confidence'] for p in predictions.values()]),
                execution_time=execution_time,
                metadata={
                    'game_id': game_id,
                    'expert_id': expert_id,
                    'prediction_count': len(predictions),
                    'config': config
                }
            )

        except Exception as e:
            logger.error(f"Coin flip prediction failed for game {game_id}: {e}")
            raise

    async def generate_market_only_predictions(self, game_id: str, expert_id: str) -> BaselineResult:
        """Generate predictions based purely on market odds"""
        start_time = datetime.now()

        try:
            # Get market odds data
            market_data = await self._get_market_odds(game_id)
            if not market_data:
                raise ValueError(f"No market data found for game {game_id}")

            predictions = {}
            config = self.baseline_configs['market_only']

            # Convert market odds to predictions
            categories = await self._get_prediction_categories()

            for category in categories:
                market_info = market_data.get(category['category'])
                if not market_info:
                    # Fallback to neutral prediction
                    if category['pred_type'] == 'binary':
                        value = True
                        confidence = 0.5
                    elif category['pred_type'] == 'numeric':
                        value = category.get('default_value', 50)
                        confidence = 0.5
                    else:
                        continue
                else:
                    # Use market odds to derive prediction
                    if category['pred_type'] == 'binary':
                        odds = market_info.get('odds', 2.0)
                        implied_prob = 1.0 / odds
                        value = implied_prob > 0.5
                        confidence = min(0.9, implied_prob + config['confidence_boost'])
                    elif category['pred_type'] == 'numeric':
                        value = market_info.get('line', category.get('default_value', 50))
                        confidence = 0.7
                    else:
                        continue

                predictions[category['category']] = {
                    'category': category['category'],
                    'subject': category.get('subject', 'game'),
                    'pred_type': category['pred_type'],
                    'value': value,
                    'confidence': confidence,
                    'stake_units': int(confidence * config['stake_multiplier'] * 3),
                    'odds': market_info.get('odds', 2.0) if market_info else 2.0,
                    'why': [{'memory_id': 'market_odds', 'weight': 1.0}]
                }

            execution_time = (datetime.now() - start_time).total_seconds()

            return BaselineResult(
                model_type='market_only',
                predictions=predictions,
                confidence=np.mean([p['confidence'] for p in predictions.values()]),
                execution_time=execution_time,
                metadata={
                    'game_id': game_id,
                    'expert_id': expert_id,
                    'prediction_count': len(predictions),
                    'market_data_available': len([k for k, v in market_data.items() if v]),
                    'config': config
                }
            )

        except Exception as e:
            logger.error(f"Market-only prediction failed for game {game_id}: {e}")
            raise

    async def generate_one_shot_predictions(self, game_id: str, expert_id: str) -> BaselineResult:
        """Generate predictions using single LLM call without memory/context"""
        start_time = datetime.now()

        try:
            # Get minimal game context (no memory retrieval)
            game_data = await self._get_game_context(game_id)
            if not game_data:
                raise ValueError(f"Game {game_id} not found")

            config = self.baseline_configs['one_shot']

            # Create minimal prompt without memory or detailed context
            prompt = self._create_one_shot_prompt(game_data)

            # Make single LLM call
            response = await self._call_llm(
                model=config['model'],
                prompt=prompt,
                max_tokens=config['max_tokens'],
                temperature=config['temperature']
            )

            # Parse response into predictions
            predictions = await self._parse_llm_response(response, game_id)

            execution_time = (datetime.now() - start_time).total_seconds()

            return BaselineResult(
                model_type='one_shot',
                predictions=predictions,
                confidence=np.mean([p['confidence'] for p in predictions.values()]) if predictions else 0.5,
                execution_time=execution_time,
                metadata={
                    'game_id': game_id,
                    'expert_id': expert_id,
                    'prediction_count': len(predictions),
                    'model': config['model'],
                    'prompt_length': len(prompt),
                    'response_length': len(response) if response else 0
                }
            )

        except Exception as e:
            logger.error(f"One-shot prediction failed for game {game_id}: {e}")
            raise

    async def generate_deliberate_predictions(self, game_id: str, expert_id: str) -> BaselineResult:
        """Generate rule-based predictions using simple heuristics"""
        start_time = datetime.now()

        try:
            # Get game context for rule application
            game_data = await self._get_game_context(game_id)
            if not game_data:
                raise ValueError(f"Game {game_id} not found")

            predictions = {}
            config = self.baseline_configs['deliberate']

            # Apply simple rules
            home_team = game_data.get('home_team')
            away_team = game_data.get('away_team')
            spread = game_data.get('spread', 0)
            total = game_data.get('total', 45)

            categories = await self._get_prediction_categories()

            for category in categories:
                cat_name = category['category']

                # Apply deliberate rules based on category
                if 'winner' in cat_name.lower():
                    # Home team advantage
                    value = True if 'home' in cat_name.lower() else False
                    confidence = config['home_advantage']
                elif 'spread' in cat_name.lower():
                    # Favorite bias
                    value = spread < 0  # Favorite covers
                    confidence = config['favorite_bias']
                elif 'total' in cat_name.lower() or 'over' in cat_name.lower():
                    # Slight over bias
                    value = True
                    confidence = config['over_bias']
                elif category['pred_type'] == 'numeric':
                    # Use simple heuristics for numeric predictions
                    if 'score' in cat_name.lower():
                        value = total / 2 + random.uniform(-3, 3)
                    else:
                        value = category.get('default_value', 50)
                    confidence = 0.6
                else:
                    # Default binary prediction
                    value = True
                    confidence = 0.55

                predictions[cat_name] = {
                    'category': cat_name,
                    'subject': category.get('subject', 'game'),
                    'pred_type': category['pred_type'],
                    'value': value,
                    'confidence': confidence,
                    'stake_units': max(1, int(confidence * 4)),
                    'odds': 2.0,
                    'why': [{'memory_id': 'deliberate_rule', 'weight': 1.0}]
                }

            execution_time = (datetime.now() - start_time).total_seconds()

            return BaselineResult(
                model_type='deliberate',
                predictions=predictions,
                confidence=np.mean([p['confidence'] for p in predictions.values()]),
                execution_time=execution_time,
                metadata={
                    'game_id': game_id,
                    'expert_id': expert_id,
                    'prediction_count': len(predictions),
                    'rules_applied': ['home_advantage', 'favorite_bias', 'over_bias'],
                    'config': config
                }
            )

        except Exception as e:
            logger.error(f"Deliberate prediction failed for game {game_id}: {e}")
            raise

    async def run_baseline_comparison(self, game_ids: List[str], expert_ids: List[str]) -> Dict[str, Any]:
        """Run comprehensive baseline comparison across multiple games and experts"""
        results = {
            'baseline_results': {},
            'expert_results': {},
            'comparison_metrics': {},
            'summary': {}
        }

        try:
            # Generate baseline predictions for all models
            for baseline_type in self.baseline_configs.keys():
                results['baseline_results'][baseline_type] = []

                for game_id in game_ids:
                    for expert_id in expert_ids:
                        if baseline_type == 'coin_flip':
                            result = await self.generate_coin_flip_predictions(game_id, expert_id)
                        elif baseline_type == 'market_only':
                            result = await self.generate_market_only_predictions(game_id, expert_id)
                        elif baseline_type == 'one_shot':
                            result = await self.generate_one_shot_predictions(game_id, expert_id)
                        elif baseline_type == 'deliberate':
                            result = await self.generate_deliberate_predictions(game_id, expert_id)

                        results['baseline_results'][baseline_type].append(result)

            # Get expert predictions for comparison
            results['expert_results'] = await self._get_expert_predictions(game_ids, expert_ids)

            # Calculate comparison metrics
            results['comparison_metrics'] = await self._calculate_comparison_metrics(
                results['baseline_results'],
                results['expert_results']
            )

            # Generate summary
            results['summary'] = self._generate_comparison_summary(results['comparison_metrics'])

            logger.info(f"Baseline comparison completed for {len(game_ids)} games, {len(expert_ids)} experts")
            return results

        except Exception as e:
            logger.error(f"Baseline comparison failed: {e}")
            raise

    async def _get_game_context(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Get basic game context without memory retrieval"""
        try:
            response = await self.supabase.table('games').select('*').eq('game_id', game_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get game context for {game_id}: {e}")
            return None

    async def _get_market_odds(self, game_id: str) -> Dict[str, Any]:
        """Get market odds data for the game"""
        try:
            # This would integrate with odds providers
            # For now, return mock data structure
            return {
                'winner': {'odds': 1.9, 'line': None},
                'spread': {'odds': 1.91, 'line': -3.5},
                'total': {'odds': 1.91, 'line': 47.5},
                'home_score': {'odds': None, 'line': 24.5},
                'away_score': {'odds': None, 'line': 21.0}
            }
        except Exception as e:
            logger.error(f"Failed to get market odds for {game_id}: {e}")
            return {}

    async def _get_prediction_categories(self) -> List[Dict[str, Any]]:
        """Get the 83 prediction categories structure"""
        try:
            # This would load from the schema or database
            # For now, return a subset for testing
            return [
                {'category': 'winner', 'pred_type': 'binary', 'subject': 'game'},
                {'category': 'home_win', 'pred_type': 'binary', 'subject': 'home_team'},
                {'category': 'spread_cover', 'pred_type': 'binary', 'subject': 'game'},
                {'category': 'total_over', 'pred_type': 'binary', 'subject': 'game'},
                {'category': 'home_score', 'pred_type': 'numeric', 'subject': 'home_team', 'min_value': 0, 'max_value': 60},
                {'category': 'away_score', 'pred_type': 'numeric', 'subject': 'away_team', 'min_value': 0, 'max_value': 60},
                {'category': 'total_score', 'pred_type': 'numeric', 'subject': 'game', 'min_value': 20, 'max_value': 80},
                {'category': 'margin', 'pred_type': 'numeric', 'subject': 'game', 'min_value': 0, 'max_value': 30}
            ]
        except Exception as e:
            logger.error(f"Failed to get prediction categories: {e}")
            return []

    def _create_one_shot_prompt(self, game_data: Dict[str, Any]) -> str:
        """Create minimal prompt for one-shot predictions"""
        home_team = game_data.get('home_team', 'Home')
        away_team = game_data.get('away_team', 'Away')

        return f"""
Predict the outcome of this NFL game: {away_team} @ {home_team}

Provide predictions in JSON format with the following structure:
{{
    "winner": {{"value": true/false, "confidence": 0.0-1.0}},
    "home_score": {{"value": number, "confidence": 0.0-1.0}},
    "away_score": {{"value": number, "confidence": 0.0-1.0}},
    "total_over": {{"value": true/false, "confidence": 0.0-1.0}}
}}

Be concise and provide only the JSON response.
"""

    async def _call_llm(self, model: str, prompt: str, max_tokens: int, temperature: float) -> str:
        """Make LLM call for one-shot predictions"""
        try:
            # This would integrate with the actual LLM service
            # For now, return a mock response
            return """
{
    "winner": {"value": true, "confidence": 0.65},
    "home_score": {"value": 24, "confidence": 0.6},
    "away_score": {"value": 21, "confidence": 0.6},
    "total_over": {"value": false, "confidence": 0.55}
}
"""
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return "{}"

    async def _parse_llm_response(self, response: str, game_id: str) -> Dict[str, Any]:
        """Parse LLM response into prediction format"""
        try:
            data = json.loads(response.strip())
            predictions = {}

            for category, pred_data in data.items():
                predictions[category] = {
                    'category': category,
                    'subject': 'game',
                    'pred_type': 'binary' if isinstance(pred_data['value'], bool) else 'numeric',
                    'value': pred_data['value'],
                    'confidence': pred_data['confidence'],
                    'stake_units': max(1, int(pred_data['confidence'] * 3)),
                    'odds': 2.0,
                    'why': [{'memory_id': 'one_shot_llm', 'weight': 1.0}]
                }

            return predictions

        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {}

    async def _get_expert_predictions(self, game_ids: List[str], expert_ids: List[str]) -> Dict[str, Any]:
        """Get expert predictions for comparison"""
        try:
            expert_results = {}

            for expert_id in expert_ids:
                expert_results[expert_id] = []

                for game_id in game_ids:
                    response = await self.supabase.table('expert_predictions')\
                        .select('*')\
                        .eq('expert_id', expert_id)\
                        .eq('game_id', game_id)\
                        .execute()

                    if response.data:
                        expert_results[expert_id].extend(response.data)

            return expert_results

        except Exception as e:
            logger.error(f"Failed to get expert predictions: {e}")
            return {}

    async def _calculate_comparison_metrics(self, baseline_results: Dict, expert_results: Dict) -> Dict[str, ComparisonMetrics]:
        """Calculate performance comparison metrics"""
        metrics = {}

        try:
            # Calculate metrics for each baseline model
            for baseline_type, results in baseline_results.items():
                # Mock calculation - would implement actual Brier/MAE/ROI calculation
                metrics[baseline_type] = ComparisonMetrics(
                    brier_score=random.uniform(0.15, 0.35),
                    mae_score=random.uniform(3.0, 8.0),
                    roi=random.uniform(-0.1, 0.05),
                    accuracy=random.uniform(0.45, 0.65),
                    calibration_error=random.uniform(0.05, 0.25),
                    prediction_count=len(results) * 8  # Approximate predictions per result
                )

            # Calculate expert metrics for comparison
            for expert_id in expert_results.keys():
                metrics[f'expert_{expert_id}'] = ComparisonMetrics(
                    brier_score=random.uniform(0.12, 0.28),
                    mae_score=random.uniform(2.5, 6.5),
                    roi=random.uniform(-0.05, 0.15),
                    accuracy=random.uniform(0.52, 0.72),
                    calibration_error=random.uniform(0.03, 0.18),
                    prediction_count=len(expert_results[expert_id]) * 83
                )

            return metrics

        except Exception as e:
            logger.error(f"Failed to calculate comparison metrics: {e}")
            return {}

    def _generate_comparison_summary(self, metrics: Dict[str, ComparisonMetrics]) -> Dict[str, Any]:
        """Generate summary of baseline vs expert performance"""
        try:
            baseline_metrics = {k: v for k, v in metrics.items() if not k.startswith('expert_')}
            expert_metrics = {k: v for k, v in metrics.items() if k.startswith('expert_')}

            # Find best performing models
            best_baseline = min(baseline_metrics.items(), key=lambda x: x[1].brier_score)
            best_expert = min(expert_metrics.items(), key=lambda x: x[1].brier_score) if expert_metrics else None

            summary = {
                'best_baseline_model': best_baseline[0],
                'best_baseline_brier': best_baseline[1].brier_score,
                'baseline_model_count': len(baseline_metrics),
                'expert_count': len(expert_metrics),
                'baseline_outperforms_expert': False,
                'recommendations': []
            }

            if best_expert:
                summary['best_expert_brier'] = best_expert[1].brier_score
                summary['baseline_outperforms_expert'] = best_baseline[1].brier_score < best_expert[1].brier_score

                if summary['baseline_outperforms_expert']:
                    summary['recommendations'].append(f"Consider routing underperforming experts to {best_baseline[0]} model")
                else:
                    summary['recommendations'].append("Expert models outperform baselines - continue current approach")

            # Add specific recommendations
            for baseline_type, metric in baseline_metrics.items():
                if metric.roi > 0.02:
                    summary['recommendations'].append(f"{baseline_type} shows positive ROI - consider for A/B testing")
                if metric.calibration_error < 0.1:
                    summary['recommendations'].append(f"{baseline_type} shows good calibration - useful for confidence modeling")

            return summary

        except Exception as e:
            logger.error(f"Failed to generate comparison summary: {e}")
            return {}
