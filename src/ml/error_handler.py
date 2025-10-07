#!/usr/bin/env python3
"""
Comprehensive Error Handling and Fallm

Implements graceful degradation, fallback mechanisms, and comprehensive
error handling for the NFL Expert Prediction System.

Requirements: 1.5, 2.6, 10.5
"""

import logging
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Union, Type
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors"""
    MEMORY_RETRIEVAL = "memory_retrieval"
    AI_GENERATION = "ai_generation"
    PREDICTION_PARSING = "prediction_parsing"
    DATABASE_CONNECTION = "database_connection"
    API_RATE_LIMIT = "api_rate_limit"
    NETWORK_TIMEOUT = "network_timeout"
    VALIDATION_ERROR = "validation_error"
    CONFIGURATION_ERROR = "configuration_error"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for error handling"""
    expert_id: Optional[str] = None
    game_id: Optional[str] = None
    operation_name: Optional[str] = None
    model_name: Optional[str] = None
    attempt_number: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorRecord:
    """Record of an error occurrence"""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    exception: Optional[Exception]
    context: ErrorContext
    timestamp: datetime
    stack_trace: Optional[str] = None
    resolution_attempted: bool = False
    resolution_successful: bool = False
    fallback_used: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage"""
        return {
            'error_id': self.error_id,
            'category': self.category.value,
            'severity': self.severity.value,
            'message': self.message,
            'exception_type': type(self.exception).__name__ if self.exception else None,
            'context': {
                'expert_id': self.context.expert_id,
                'game_id': self.context.game_id,
                'operation_name': self.context.operation_name,
                'model_name': self.context.model_name,
                'attempt_number': self.context.attempt_number,
                'metadata': self.context.metadata
            },
            'timestamp': self.timestamp.isoformat(),
            'stack_trace': self.stack_trace,
            'resolution_attempted': self.resolution_attempted,
            'resolution_successful': self.resolution_successful,
            'fallback_used': self.fallback_used
        }


class FallbackStrategy:
    """Base class for fallback strategies"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    async def execute(self, context: ErrorContext, original_error: Exception) -> Any:
        """Execute the fallback strategy"""
        raise NotImplementedError("Subclasses must implement execute method")

    def is_applicable(self, error_category: ErrorCategory, context: ErrorContext) -> bool:
        """Check if this fallback strategy is applicable"""
        return True


class MemoryRetrievalFallback(FallbackStrategy):
    """Fallback strategy for memory retrieval failures"""

    def __init__(self):
        super().__init__(
            name="memory_retrieval_fallback",
            description="Provides empty memory list when memory retrieval fails"
        )

    async def execute(self, context: ErrorContext, original_error: Exception) -> List[Dict[str, Any]]:
        """Return empty memory list with explanation"""
        logger.warning(f"🔄 Using memory retrieval fallback for {context.expert_id}: {original_error}")

        return [{
            'memory_id': 'fallback_memory',
            'memory_type': 'fallback',
            'similarity_score': 0.0,
            'relevance_explanation': f'Memory retrieval failed: {str(original_error)[:100]}',
            'bucket_type': 'fallback',
            'lessons_learned': ['Memory system temporarily unavailable'],
            'contextual_factors': [{'factor': 'system_error', 'value': 'memory_unavailable'}]
        }]

    def is_applicable(self, error_category: ErrorCategory, context: ErrorContext) -> bool:
        return error_category in [ErrorCategory.MEMORY_RETRIEVAL, ErrorCategory.DATABASE_CONNECTION]


class AIGenerationFallback(FallbackStrategy):
    """Fallback strategy for AI generation failures"""

    def __init__(self):
        super().__init__(
            name="ai_generation_fallback",
            description="Provides basic analysis when AI generation fails"
        )

    async def execute(self, context: ErrorContext, original_error: Exception) -> Dict[str, Any]:
        """Return basic fallback analysis"""
        logger.warning(f"🔄 Using AI generation fallback for {context.expert_id}: {original_error}")

        # Create basic fallback analysis based on expert type
        expert_id = context.expert_id or 'unknown'

        # Basic predictions based on NFL averages
        fallback_analysis = {
            'analysis_text': f"Fallback analysis for {expert_id} due to AI unavailability",
            'confidence_overall': 0.3,  # Low confidence for fallback
            'key_factors': ['AI analysis unavailable', 'Using statistical averages'],
            'reasoning': f"AI generation failed: {str(original_error)[:100]}. Using fallback predictions.",
            'memory_influence': 'Unable to process due to AI error',
            'predictions': self._generate_basic_predictions(expert_id),
            'fallback_used': True,
            'original_error': str(original_error)
        }

        return fallback_analysis

    def _generate_basic_predictions(self, expert_id: str) -> Dict[str, Any]:
        """Generate basic predictions using NFL statistical averages"""
        # Adjust predictions slightly based on expert personality
        conservative_adjustment = 0.0
        if 'conservative' in expert_id.lower():
            conservative_adjustment = -0.05
        elif 'risk' in expert_id.lower() or 'gambler' in expert_id.lower():
            conservative_adjustment = 0.05

        base_confidence = 0.5 + conservative_adjustment

        return {
            'winner': 'home',  # Slight home field advantage
            'winner_confidence': max(0.1, min(0.9, base_confidence + 0.05)),
            'spread': 0.0,  # Neutral spread
            'spread_confidence': max(0.1, min(0.9, base_confidence)),
            'total': 'over',
            'total_points': 45.0,  # NFL average
            'total_confidence': max(0.1, min(0.9, base_confidence)),
            'exact_score': '24-21',
            'margin': 3
        }

    def is_applicable(self, error_category: ErrorCategory, context: ErrorContext) -> bool:
        return error_category == ErrorCategory.AI_GENERATION


class PredictionParsingFallback(FallbackStrategy):
    """Fallback strategy for prediction parsing failures"""

    def __init__(self):
        super().__init__(
            name="prediction_parsing_fallback",
            description="Provides structured predictions when parsing fails"
        )

    async def execute(self, context: ErrorContext, original_error: Exception) -> Dict[str, Any]:
        """Return structured fallback predictions"""
        logger.warning(f"🔄 Using prediction parsing fallback for {context.expert_id}: {original_error}")

        return {
            'parsing_success': False,
            'parsing_errors': [str(original_error)],
            'analysis_text': f"Parsing failed for {context.expert_id}: {str(original_error)[:100]}",
            'confidence_overall': 0.25,
            'key_factors': ['Parsing error', 'Using fallback structure'],
            'reasoning': 'AI response could not be parsed, using fallback predictions',
            'predictions': self._generate_structured_fallback(),
            'fallback_used': True
        }

    def _generate_structured_fallback(self) -> Dict[str, Any]:
        """Generate structured fallback predictions"""
        return {
            # Core predictions
            'game_winner': {'prediction': 'home', 'confidence': 0.52, 'reasoning': 'Home field advantage'},
            'point_spread': {'prediction': -2.5, 'confidence': 0.48, 'reasoning': 'Slight home favorite'},
            'total_points': {'prediction': 'over', 'confidence': 0.50, 'reasoning': 'Average scoring expected'},

            # Quarter predictions
            'q1_score': {'home': 7, 'away': 3, 'confidence': 0.45},
            'q2_score': {'home': 10, 'away': 7, 'confidence': 0.45},
            'q3_score': {'home': 3, 'away': 7, 'confidence': 0.45},
            'q4_score': {'home': 4, 'away': 4, 'confidence': 0.45},

            # Situational predictions
            'turnover_differential': {'prediction': 0, 'confidence': 0.40},
            'red_zone_efficiency': {'prediction': 0.6, 'confidence': 0.40},
            'third_down_conversion': {'prediction': 0.4, 'confidence': 0.40}
        }

    def is_applicable(self, error_category: ErrorCategory, context: ErrorContext) -> bool:
        return error_category == ErrorCategory.PREDICTION_PARSING


class ModelFallbackStrategy(FallbackStrategy):
    """Fallback strategy for model unavailability"""

    def __init__(self, fallback_models: Dict[str, str]):
        super().__init__(
            name="model_fallback",
            description="Switches to backup models when primary models are unavailable"
        )
        self.fallback_models = fallback_models

    async def execute(self, context: ErrorContext, original_error: Exception) -> str:
        """Return fallback model for the given context"""
        original_model = context.model_name or 'unknown'

        # Extract provider from model name
        provider = original_model.split('/')[0] if '/' in original_model else original_model

        # Get fallback model
        fallback_model = self.fallback_models.get(provider, self.fallback_models.get('default', 'gpt-3.5-turbo'))

        logger.warning(f"🔄 Using model fallback: {original_model} -> {fallback_model}")

        return fallback_model

    def is_applicable(self, error_category: ErrorCategory, context: ErrorContext) -> bool:
        return error_category in [ErrorCategory.API_RATE_LIMIT, ErrorCategory.NETWORK_TIMEOUT]


class ComprehensiveErrorHandler:
    """
    Comprehensive error handling system with fallback strategies.

    Provides graceful degradation when components fail and maintains
    system operation even under adverse conditions.
    """

    def __init__(self):
        self.fallback_strategies: Dict[ErrorCategory, List[FallbackStrategy]] = {}
        self.error_history: List[ErrorRecord] = []
        self.error_counts: Dict[ErrorCategory, int] = {}

        # Initialize default fallback strategies
        self._initialize_default_fallbacks()

        logger.info("✅ Comprehensive Error Handler initialized")

    def _initialize_default_fallbacks(self):
        """Initialize default fallback strategies"""
        # Memory retrieval fallbacks
        self.register_fallback_strategy(ErrorCategory.MEMORY_RETRIEVAL, MemoryRetrievalFallback())

        # AI generation fallbacks
        self.register_fallback_strategy(ErrorCategory.AI_GENERATION, AIGenerationFallback())

        # Prediction parsing fallbacks
        self.register_fallback_strategy(ErrorCategory.PREDICTION_PARSING, PredictionParsingFallback())

        # Model fallbacks
        default_model_fallbacks = {
            'openai': 'anthropic/claude-3-haiku',
            'anthropic': 'openai/gpt-3.5-turbo',
            'google': 'openai/gpt-3.5-turbo',
            'x-ai': 'openai/gpt-3.5-turbo',
            'deepseek': 'openai/gpt-3.5-turbo',
            'default': 'openai/gpt-3.5-turbo'
        }
        model_fallback = ModelFallbackStrategy(default_model_fallbacks)
        self.register_fallback_strategy(ErrorCategory.API_RATE_LIMIT, model_fallback)
        self.register_fallback_strategy(ErrorCategory.NETWORK_TIMEOUT, model_fallback)

        # Database connection fallbacks
        self.register_fallback_strategy(ErrorCategory.DATABASE_CONNECTION, MemoryRetrievalFallback())

    def register_fallback_strategy(self, category: ErrorCategory, strategy: FallbackStrategy):
        """Register a fallback strategy for an error category"""
        if category not in self.fallback_strategies:
            self.fallback_strategies[category] = []
        self.fallback_strategies[category].append(strategy)
        logger.debug(f"Registered fallback strategy '{strategy.name}' for {category.value}")

    def categorize_error(self, error: Exception, context: ErrorContext) -> ErrorCategory:
        """Categorize an error based on its type and context"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()

        # Memory retrieval errors
        if 'memory' in error_str or 'retrieval' in error_str:
            return ErrorCategory.MEMORY_RETRIEVAL

        # Database connection errors
        if any(keyword in error_str for keyword in ['connection', 'database', 'supabase', 'postgres']):
            return ErrorCategory.DATABASE_CONNECTION

        # API rate limiting
        if any(keyword in error_str for keyword in ['rate limit', 'too many requests', '429']):
            return ErrorCategory.API_RATE_LIMIT

        # Network timeouts
        if any(keyword in error_str for keyword in ['timeout', 'network', 'connection reset']):
            return ErrorCategory.NETWORK_TIMEOUT

        # AI generation errors
        if any(keyword in error_str for keyword in ['ai', 'model', 'generation', 'openai', 'anthropic']):
            return ErrorCategory.AI_GENERATION

        # Parsing errors
        if any(keyword in error_str for keyword in ['parse', 'json', 'format', 'invalid']):
            return ErrorCategory.PREDICTION_PARSING

        # Validation errors
        if 'validation' in error_str or 'valueerror' in error_type:
            return ErrorCategory.VALIDATION_ERROR

        # Configuration errors
        if any(keyword in error_str for keyword in ['config', 'setting', 'parameter']):
            return ErrorCategory.CONFIGURATION_ERROR

        return ErrorCategory.UNKNOWN

    def determine_severity(self, error: Exception, category: ErrorCategory, context: ErrorContext) -> ErrorSeverity:
        """Determine the severity of an error"""
        # Critical errors that prevent system operation
        if category in [ErrorCategory.DATABASE_CONNECTION, ErrorCategory.CONFIGURATION_ERROR]:
            return ErrorSeverity.CRITICAL

        # High severity errors that significantly impact functionality
        if category in [ErrorCategory.AI_GENERATION] and context.attempt_number > 2:
            return ErrorSeverity.HIGH

        # Medium severity errors that can be worked around
        if category in [ErrorCategory.MEMORY_RETRIEVAL, ErrorCategory.API_RATE_LIMIT]:
            return ErrorSeverity.MEDIUM

        # Low severity errors that have minimal impact
        return ErrorSeverity.LOW

    async def handle_error(
        self,
        error: Exception,
        context: ErrorContext,
        operation_name: str = "unknown_operation"
    ) -> Any:
        """
        Handle an error with appropriate fallback strategy.

        Args:
            error: The exception that occurred
            context: Context information about the error
            operation_name: Name of the operation that failed

        Returns:
            Fallback result or raises the original error if no fallback available
        """
        # Categorize and assess the error
        category = self.categorize_error(error, context)
        severity = self.determine_severity(error, category, context)

        # Create error record
        error_record = ErrorRecord(
            error_id=f"{category.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{context.expert_id or 'unknown'}",
            category=category,
            severity=severity,
            message=str(error),
            exception=error,
            context=context,
            timestamp=datetime.now(),
            stack_trace=traceback.format_exc()
        )

        # Log the error
        self._log_error(error_record)

        # Update error counts
        self.error_counts[category] = self.error_counts.get(category, 0) + 1

        # Try to apply fallback strategies
        if category in self.fallback_strategies:
            for strategy in self.fallback_strategies[category]:
                if strategy.is_applicable(category, context):
                    try:
                        logger.info(f"🔄 Applying fallback strategy '{strategy.name}' for {category.value}")

                        error_record.resolution_attempted = True
                        result = await strategy.execute(context, error)
                        error_record.resolution_successful = True
                        error_record.fallback_used = strategy.name

                        # Store error record
                        self.error_history.append(error_record)

                        return result

                    except Exception as fallback_error:
                        logger.error(f"❌ Fallback strategy '{strategy.name}' failed: {fallback_error}")
                        continue

        # No applicable fallback found
        error_record.resolution_attempted = False
        self.error_history.append(error_record)

        logger.error(f"❌ No fallback available for {category.value} error: {error}")
        raise error

    def _log_error(self, error_record: ErrorRecord):
        """Log error with appropriate level based on severity"""
        log_message = f"{error_record.category.value.upper()}: {error_record.message}"

        if error_record.context.expert_id:
            log_message += f" (Expert: {error_record.context.expert_id})"

        if error_record.context.operation_name:
            log_message += f" (Operation: {error_record.context.operation_name})"

        if error_record.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error_record.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error_record.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error handling statistics"""
        total_errors = len(self.error_history)
        successful_fallbacks = sum(1 for e in self.error_history if e.resolution_successful)

        return {
            'total_errors': total_errors,
            'successful_fallbacks': successful_fallbacks,
            'fallback_success_rate': successful_fallbacks / total_errors if total_errors > 0 else 0,
            'error_counts_by_category': dict(self.error_counts),
            'recent_errors': [e.to_dict() for e in self.error_history[-10:]],  # Last 10 errors
            'registered_fallback_strategies': {
                category.value: [s.name for s in strategies]
                for category, strategies in self.fallback_strategies.items()
            }
        }

    def clear_error_history(self):
        """Clear error history (useful for testing)"""
        self.error_history.clear()
        self.error_counts.clear()
        logger.info("🗑️ Error history cleared")


# Global error handler instance
_global_error_handler: Optional[ComprehensiveErrorHandler] = None


def get_error_handler() -> ComprehensiveErrorHandler:
    """Get the global error handler instance"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ComprehensiveErrorHandler()
    return _global_error_handler


async def handle_error_with_fallback(
    error: Exception,
    expert_id: Optional[str] = None,
    game_id: Optional[str] = None,
    operation_name: str = "unknown_operation",
    model_name: Optional[str] = None,
    attempt_number: int = 1,
    metadata: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Convenience function to handle errors with fallback.

    Args:
        error: The exception that occurred
        expert_id: Expert ID if applicable
        game_id: Game ID if applicable
        operation_name: Name of the operation that failed
        model_name: Model name if applicable
        attempt_number: Current attempt number
        metadata: Additional metadata

    Returns:
        Fallback result or raises the original error
    """
    context = ErrorContext(
        expert_id=expert_id,
        game_id=game_id,
        operation_name=operation_name,
        model_name=model_name,
        attempt_number=attempt_number,
        metadata=metadata or {}
    )

    error_handler = get_error_handler()
    return await error_handler.handle_error(error, context, operation_name)
