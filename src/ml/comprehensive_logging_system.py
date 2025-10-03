#!/usr/bin/env python3
"""
Comprehensive Logging System for NFL Prediction System

Logs all prediction inputs, reasoning, outcomes, memory usage, and LLM performance.

Requirements: 9.1, 9.2, 9.3
"""

import logging
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import sys

logger = logging.getLogger(__name__)


class PredictionLogger:
    """Comprehensive logger for prediction system"""

    def __init__(self, log_dir: str = "logs/predictions"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create separate log files for different aspects
        self.prediction_log_file = self.log_dir / f"predictions_{datetime.now().strftime('%Y%m%d')}.jsonl"
        self.memory_log_file = self.log_dir / f"memory_{datetime.now().strftime('%Y%m%d')}.jsonl"
        self.llm_log_file = self.log_dir / f"llm_{datetime.now().strftime('%Y%m%d')}.jsonl"
        self.outcome_log_file = self.log_dir / f"outcomes_{datetime.now().strftime('%Y%m%d')}.jsonl"

        logger.info(f"📝 Comprehensive Logging System initialized")
        logger.info(f"   Log directory: {self.log_dir}")

    def log_prediction(
        self,
        expert_id: str,
        expert_name: str,
        game_context: Dict[str, Any],
        prediction: Dict[str, Any],
        input_data: Dict[str, Any]
    ):
        """Log a complete prediction with all inputs and outputs"""

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'log_type': 'prediction',
            'expert_id': expert_id,
            'expert_name': expert_name,
            'game_context': {
                'game_id': game_context.get('game_id'),
                'home_team': game_context.get('home_team'),
                'away_team': game_context.get('away_team'),
                'season': game_context.get('season'),
                'week': game_context.get('week'),
                'game_date': game_context.get('game_date')
            },
            'input_data': {
                'weather': input_data.get('weather'),
                'injuries': input_data.get('injuries'),
                'betting_lines': input_data.get('line_movement'),
                'team_stats': input_data.get('team_stats')
            },
            'prediction': {
                'winner': prediction.get('winner_prediction'),
                'confidence': prediction.get('winner_confidence'),
                'spread': prediction.get('spread_prediction'),
                'total': prediction.get('total_prediction'),
                'reasoning': prediction.get('reasoning', '')[:500],  # Truncate for log
                'reasoning_length': len(prediction.get('reasoning', ''))
            },
            'metadata': {
                'llm_powered': prediction.get('llm_powered', False),
                'memory_enhanced': prediction.get('memory_enhanced', False),
                'memories_consulted': prediction.get('memories_consulted', 0)
            }
        }

        self._write_log_entry(self.prediction_log_file, log_entry)
        logger.info(f"📝 Logged prediction: {expert_name} - {game_context.get('away_team')} @ {game_context.get('home_team')}")

    def log_memory_usage(
        self,
        expert_id: str,
        expert_name: str,
        game_context: Dict[str, Any],
        memories_retrieved: List[Dict[str, Any]],
        memory_impact: Dict[str, Any]
    ):
        """Log memory retrieval and usage"""

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'log_type': 'memory_usage',
            'expert_id': expert_id,
            'expert_name': expert_name,
            'game_context': {
                'game_id': game_context.get('game_id'),
                'home_team': game_context.get('home_team'),
                'away_team': game_context.get('away_team')
            },
            'memory_retrieval': {
                'memories_found': len(memories_retrieved),
                'memory_ids': [m.get('memory_id') for m in memories_retrieved],
                'similarity_scores': [m.get('similarity_score', 0.0) for m in memories_retrieved],
                'memory_types': [m.get('memory_type') for m in memories_retrieved]
            },
            'memory_impact': {
                'confidence_adjustment': memory_impact.get('confidence_adjustment', 0.0),
                'learned_principles_applied': memory_impact.get('learned_principles', []),
                'success_rate_from_memories': memory_impact.get('memory_success_rate', 0.0)
            }
        }

        self._write_log_entry(self.memory_log_file, log_entry)
        logger.info(f"🧠 Logged memory usage: {expert_name} - {len(memories_retrieved)} memories retrieved")

    def log_llm_interaction(
        self,
        expert_id: str,
        expert_name: str,
        game_context: Dict[str, Any],
        llm_request: Dict[str, Any],
        llm_response: Dict[str, Any],
        performance_metrics: Dict[str, Any]
    ):
        """Log LLM interaction details"""

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'log_type': 'llm_interaction',
            'expert_id': expert_id,
            'expert_name': expert_name,
            'game_context': {
                'game_id': game_context.get('game_id'),
                'home_team': game_context.get('home_team'),
                'away_team': game_context.get('away_team')
            },
            'llm_request': {
                'model': llm_request.get('model'),
                'temperature': llm_request.get('temperature'),
                'max_tokens': llm_request.get('max_tokens'),
                'system_message_length': len(llm_request.get('system_message', '')),
                'user_message_length': len(llm_request.get('user_message', ''))
            },
            'llm_response': {
                'response_length': len(llm_response.get('content', '')),
                'tokens_used': llm_response.get('tokens_used'),
                'prompt_tokens': llm_response.get('prompt_tokens'),
                'completion_tokens': llm_response.get('completion_tokens'),
                'response_preview': llm_response.get('content', '')[:200]
            },
            'performance': {
                'response_time': performance_metrics.get('response_time', 0.0),
                'tokens_per_second': performance_metrics.get('tokens_per_second', 0.0),
                'parse_successful': performance_metrics.get('parse_successful', False),
                'parse_errors': performance_metrics.get('parse_errors', [])
            }
        }

        self._write_log_entry(self.llm_log_file, log_entry)
        logger.info(f"🤖 Logged LLM interaction: {expert_name} - {performance_metrics.get('response_time', 0):.2f}s, {llm_response.get('tokens_used', 0)} tokens")

    def log_outcome(
        self,
        game_id: str,
        game_context: Dict[str, Any],
        actual_outcome: Dict[str, Any],
        predictions: List[Dict[str, Any]]
    ):
        """Log actual game outcome and compare with predictions"""

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'log_type': 'outcome',
            'game_id': game_id,
            'game_context': {
                'home_team': game_context.get('home_team'),
                'away_team': game_context.get('away_team'),
                'season': game_context.get('season'),
                'week': game_context.get('week')
            },
            'actual_outcome': {
                'winner': actual_outcome.get('winner'),
                'final_score': actual_outcome.get('final_score'),
                'spread': actual_outcome.get('spread'),
                'total_points': actual_outcome.get('total_points')
            },
            'predictions_comparison': []
        }

        # Compare each prediction with actual outcome
        for pred in predictions:
            comparison = {
                'expert_id': pred.get('expert_id'),
                'expert_name': pred.get('expert_name'),
                'predicted_winner': pred.get('winner_prediction'),
                'predicted_confidence': pred.get('winner_confidence'),
                'winner_correct': pred.get('winner_prediction') == actual_outcome.get('winner'),
                'spread_error': abs(pred.get('spread_prediction', 0) - actual_outcome.get('spread', 0)),
                'total_error': abs(pred.get('total_prediction', 0) - actual_outcome.get('total_points', 0))
            }
            log_entry['predictions_comparison'].append(comparison)

        self._write_log_entry(self.outcome_log_file, log_entry)
        logger.info(f"🏈 Logged outcome: {game_context.get('away_team')} @ {game_context.get('home_team')} - Winner: {actual_outcome.get('winner')}")

    def _write_log_entry(self, log_file: Path, entry: Dict[str, Any]):
        """Write a log entry to file in JSONL format"""
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            logger.error(f"❌ Error writing log entry: {e}")

    def get_log_summary(self, log_type: str = 'prediction', days: int = 1) -> Dict[str, Any]:
        """Get summary of logs for specified type and time period"""

        log_file_map = {
            'prediction': self.prediction_log_file,
            'memory': self.memory_log_file,
            'llm': self.llm_log_file,
            'outcome': self.outcome_log_file
        }

        log_file = log_file_map.get(log_type)
        if not log_file or not log_file.exists():
            return {'error': f'Log file not found for type: {log_type}'}

        # Read and parse log entries
        entries = []
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"❌ Error reading log file: {e}")
            return {'error': str(e)}

        # Generate summary based on log type
        if log_type == 'prediction':
            return self._summarize_predictions(entries)
        elif log_type == 'memory':
            return self._summarize_memory_usage(entries)
        elif log_type == 'llm':
            return self._summarize_llm_performance(entries)
        elif log_type == 'outcome':
            return self._summarize_outcomes(entries)

        return {'total_entries': len(entries)}

    def _summarize_predictions(self, entries: List[Dict]) -> Dict[str, Any]:
        """Summarize prediction log entries"""
        if not entries:
            return {'total_predictions': 0}

        return {
            'total_predictions': len(entries),
            'experts': list(set(e['expert_name'] for e in entries)),
            'llm_powered_count': sum(1 for e in entries if e.get('metadata', {}).get('llm_powered')),
            'memory_enhanced_count': sum(1 for e in entries if e.get('metadata', {}).get('memory_enhanced')),
            'average_confidence': sum(e['prediction']['confidence'] for e in entries) / len(entries),
            'average_reasoning_length': sum(e['prediction']['reasoning_length'] for e in entries) / len(entries)
        }

    def _summarize_memory_usage(self, entries: List[Dict]) -> Dict[str, Any]:
        """Summarize memory usage log entries"""
        if not entries:
            return {'total_memory_retrievals': 0}

        return {
            'total_memory_retrievals': len(entries),
            'total_memories_retrieved': sum(e['memory_retrieval']['memories_found'] for e in entries),
            'average_memories_per_prediction': sum(e['memory_retrieval']['memories_found'] for e in entries) / len(entries),
            'average_confidence_adjustment': sum(abs(e['memory_impact']['confidence_adjustment']) for e in entries) / len(entries)
        }

    def _summarize_llm_performance(self, entries: List[Dict]) -> Dict[str, Any]:
        """Summarize LLM performance log entries"""
        if not entries:
            return {'total_llm_calls': 0}

        return {
            'total_llm_calls': len(entries),
            'total_tokens_used': sum(e['llm_response']['tokens_used'] or 0 for e in entries),
            'average_response_time': sum(e['performance']['response_time'] for e in entries) / len(entries),
            'average_tokens_per_call': sum(e['llm_response']['tokens_used'] or 0 for e in entries) / len(entries),
            'parse_success_rate': sum(1 for e in entries if e['performance']['parse_successful']) / len(entries)
        }

    def _summarize_outcomes(self, entries: List[Dict]) -> Dict[str, Any]:
        """Summarize outcome log entries"""
        if not entries:
            return {'total_outcomes': 0}

        all_comparisons = []
        for entry in entries:
            all_comparisons.extend(entry.get('predictions_comparison', []))

        if not all_comparisons:
            return {'total_outcomes': len(entries), 'total_predictions': 0}

        return {
            'total_outcomes': len(entries),
            'total_predictions': len(all_comparisons),
            'overall_accuracy': sum(1 for c in all_comparisons if c['winner_correct']) / len(all_comparisons),
            'average_spread_error': sum(c['spread_error'] for c in all_comparisons) / len(all_comparisons),
            'average_total_error': sum(c['total_error'] for c in all_comparisons) / len(all_comparisons)
        }


# Global instance
_prediction_logger = None

def get_prediction_logger(log_dir: str = "logs/predictions") -> PredictionLogger:
    """Get global prediction logger instance"""
    global _prediction_logger
    if _prediction_logger is None:
        _prediction_logger = PredictionLogger(log_dir=log_dir)
    return _prediction_logger
