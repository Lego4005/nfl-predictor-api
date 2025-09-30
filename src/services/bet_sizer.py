"""
Bet Sizing Service with Kelly Criterion

This module implements Kelly Criterion bet sizing with personality-based adjustments
and safety caps to prevent excessive risk-taking.

Kelly Criterion Formula:
    f* = (bp - q) / b
    where:
        f* = optimal fraction of bankroll to bet
        b = decimal odds - 1
        p = probability of winning
        q = 1 - p (probability of losing)

Author: Financial Systems Engineer
Created: 2025-09-29
"""

import logging
from typing import Dict, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)


class BetSizer:
    """Calculate optimal bet sizes using Kelly Criterion with personality adjustments."""

    # Personality-based Kelly multipliers
    PERSONALITY_ADJUSTMENTS = {
        'gambler': 1.5,      # Aggressive - 150% of Kelly
        'scholar': 1.0,      # Pure Kelly - 100% of Kelly
        'conservative': 0.5, # Cautious - 50% of Kelly (Fractional Kelly)
        'rebel': 1.2,        # Contrarian but controlled - 120% of Kelly
        'analyst': 0.8,      # Data-driven but careful - 80% of Kelly
        'veteran': 0.7,      # Experienced and cautious - 70% of Kelly
        'rookie': 0.6,       # Inexperienced and careful - 60% of Kelly
        'specialist': 0.9,   # Expert in specific areas - 90% of Kelly
        'default': 0.75      # Default safe multiplier - 75% of Kelly
    }

    # Safety caps
    MAX_BET_PERCENTAGE = 0.30  # Never bet more than 30% of bankroll
    MIN_BET_AMOUNT = 5.0       # Minimum bet size
    MAX_BET_AMOUNT = 50000.0   # Maximum bet size (safety)
    MIN_CONFIDENCE = 0.70      # Minimum confidence to place bet
    MIN_EDGE = 0.02            # Minimum edge required (2%)

    def __init__(self):
        """Initialize the bet sizer."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def calculate_kelly_criterion(
        self,
        win_probability: float,
        odds: str,
        bankroll: float
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate optimal bet size using Kelly Criterion.

        Args:
            win_probability: Probability of winning (0-1)
            odds: Vegas odds in American format ('+150', '-110', 'EVEN')
            bankroll: Current bankroll amount

        Returns:
            Tuple of (bet_fraction, metadata_dict)
            bet_fraction: Optimal fraction of bankroll to bet (0-1)
            metadata: Dict with 'decimal_odds', 'implied_prob', 'edge', 'kelly_fraction'
        """
        # Convert American odds to decimal odds
        decimal_odds = self._american_to_decimal(odds)

        # Calculate implied probability from odds
        implied_prob = 1.0 / decimal_odds

        # Calculate edge (our probability vs market probability)
        edge = win_probability - implied_prob

        # Kelly Criterion formula: f* = (bp - q) / b
        # where b = decimal_odds - 1, p = win_probability, q = 1 - win_probability
        b = decimal_odds - 1.0
        p = win_probability
        q = 1.0 - p

        # Calculate Kelly fraction
        if b <= 0:
            kelly_fraction = 0.0
        else:
            kelly_fraction = (b * p - q) / b

        # Kelly fraction should never be negative
        kelly_fraction = max(0.0, kelly_fraction)

        # Cap at maximum bet percentage for safety
        kelly_fraction = min(kelly_fraction, self.MAX_BET_PERCENTAGE)

        metadata = {
            'decimal_odds': round(decimal_odds, 3),
            'implied_prob': round(implied_prob, 4),
            'edge': round(edge, 4),
            'kelly_fraction': round(kelly_fraction, 4)
        }

        self.logger.debug(
            f"Kelly calculation: win_prob={p:.3f}, odds={odds}, "
            f"decimal={decimal_odds:.3f}, edge={edge:.3f}, kelly={kelly_fraction:.3f}"
        )

        return kelly_fraction, metadata

    def apply_personality_adjustment(
        self,
        expert_personality: str,
        kelly_fraction: float
    ) -> Tuple[float, float]:
        """
        Apply personality-based adjustment to Kelly Criterion recommendation.

        Args:
            expert_personality: Personality type ('gambler', 'scholar', etc.)
            kelly_fraction: Kelly Criterion fraction (0-1)

        Returns:
            Tuple of (adjusted_fraction, adjustment_multiplier)
        """
        personality = expert_personality.lower()
        multiplier = self.PERSONALITY_ADJUSTMENTS.get(
            personality,
            self.PERSONALITY_ADJUSTMENTS['default']
        )

        adjusted_fraction = kelly_fraction * multiplier

        # Always respect the maximum bet cap
        adjusted_fraction = min(adjusted_fraction, self.MAX_BET_PERCENTAGE)

        self.logger.debug(
            f"Personality adjustment: {personality} -> {multiplier}x Kelly "
            f"({kelly_fraction:.3f} -> {adjusted_fraction:.3f})"
        )

        return adjusted_fraction, multiplier

    def get_bet_size(
        self,
        expert_id: str,
        expert_personality: str,
        confidence: float,
        odds: str,
        bankroll: float
    ) -> Dict:
        """
        Calculate final bet size with all adjustments and validations.

        This is the main entry point for bet sizing. It combines Kelly Criterion,
        personality adjustments, and safety caps.

        Args:
            expert_id: Expert identifier
            expert_personality: Expert personality type
            confidence: Prediction confidence (0-1)
            odds: Vegas odds in American format
            bankroll: Current bankroll balance

        Returns:
            Dict with bet details:
            {
                'should_bet': bool,
                'bet_amount': float,
                'bet_fraction': float,
                'kelly_suggested': float,
                'personality_adjustment': float,
                'edge': float,
                'reasoning': str,
                'metadata': dict
            }
        """
        result = {
            'should_bet': False,
            'bet_amount': 0.0,
            'bet_fraction': 0.0,
            'kelly_suggested': 0.0,
            'personality_adjustment': 1.0,
            'edge': 0.0,
            'reasoning': '',
            'metadata': {}
        }

        # Validation: Check minimum confidence
        if confidence < self.MIN_CONFIDENCE:
            result['reasoning'] = f"Confidence {confidence:.2%} below minimum {self.MIN_CONFIDENCE:.2%}"
            self.logger.info(f"[{expert_id}] {result['reasoning']}")
            return result

        # Validation: Check bankroll
        if bankroll <= 0:
            result['reasoning'] = "Expert eliminated (bankroll <= 0)"
            self.logger.warning(f"[{expert_id}] {result['reasoning']}")
            return result

        # Calculate Kelly Criterion
        kelly_fraction, kelly_metadata = self.calculate_kelly_criterion(
            win_probability=confidence,
            odds=odds,
            bankroll=bankroll
        )

        # Check for positive edge
        edge = kelly_metadata['edge']
        if edge < self.MIN_EDGE:
            result['reasoning'] = f"Edge {edge:.2%} below minimum {self.MIN_EDGE:.2%}"
            result['metadata'] = kelly_metadata
            self.logger.info(f"[{expert_id}] {result['reasoning']}")
            return result

        # Apply personality adjustment
        adjusted_fraction, personality_multiplier = self.apply_personality_adjustment(
            expert_personality=expert_personality,
            kelly_fraction=kelly_fraction
        )

        # Calculate bet amount
        bet_amount = bankroll * adjusted_fraction

        # Apply minimum and maximum bet constraints
        if bet_amount < self.MIN_BET_AMOUNT:
            result['reasoning'] = f"Bet size ${bet_amount:.2f} below minimum ${self.MIN_BET_AMOUNT:.2f}"
            result['metadata'] = kelly_metadata
            self.logger.info(f"[{expert_id}] {result['reasoning']}")
            return result

        bet_amount = min(bet_amount, self.MAX_BET_AMOUNT)

        # Round to 2 decimal places
        bet_amount = float(Decimal(str(bet_amount)).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        ))

        # Success - bet should be placed
        result['should_bet'] = True
        result['bet_amount'] = bet_amount
        result['bet_fraction'] = adjusted_fraction
        result['kelly_suggested'] = kelly_fraction
        result['personality_adjustment'] = personality_multiplier
        result['edge'] = edge
        result['metadata'] = kelly_metadata
        result['reasoning'] = (
            f"Kelly: {kelly_fraction:.2%}, "
            f"{expert_personality} adjustment: {personality_multiplier}x, "
            f"Final: ${bet_amount:.2f} ({adjusted_fraction:.2%} of bankroll)"
        )

        self.logger.info(
            f"[{expert_id}] Bet approved: ${bet_amount:.2f} "
            f"(confidence={confidence:.2%}, edge={edge:.2%})"
        )

        return result

    def _american_to_decimal(self, odds: str) -> float:
        """
        Convert American odds format to decimal odds.

        Args:
            odds: American odds ('+150', '-110', 'EVEN')

        Returns:
            Decimal odds (e.g., 2.50 for +150, 1.91 for -110)
        """
        odds = odds.strip().upper()

        if odds == 'EVEN':
            return 2.0

        # Remove '+' or '-' prefix
        sign = odds[0]
        value = abs(int(odds))

        if sign == '+':
            # Positive odds: decimal = (odds / 100) + 1
            return (value / 100.0) + 1.0
        else:
            # Negative odds: decimal = (100 / odds) + 1
            return (100.0 / value) + 1.0

    def validate_bet_constraints(
        self,
        bet_amount: float,
        bankroll: float,
        max_bet_percentage: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Validate bet against constraints.

        Args:
            bet_amount: Proposed bet amount
            bankroll: Current bankroll
            max_bet_percentage: Optional custom max percentage (overrides default)

        Returns:
            Tuple of (is_valid, reason)
        """
        max_pct = max_bet_percentage or self.MAX_BET_PERCENTAGE

        if bet_amount < self.MIN_BET_AMOUNT:
            return False, f"Bet ${bet_amount:.2f} below minimum ${self.MIN_BET_AMOUNT:.2f}"

        if bet_amount > bankroll:
            return False, f"Bet ${bet_amount:.2f} exceeds bankroll ${bankroll:.2f}"

        bet_percentage = bet_amount / bankroll
        if bet_percentage > max_pct:
            return False, f"Bet {bet_percentage:.2%} exceeds maximum {max_pct:.2%}"

        return True, "Valid bet"


# Singleton instance
_bet_sizer_instance = None


def get_bet_sizer() -> BetSizer:
    """Get singleton BetSizer instance."""
    global _bet_sizer_instance
    if _bet_sizer_instance is None:
        _bet_sizer_instance = BetSizer()
    return _bet_sizer_instance