"""
Bankroll Management Service

Tracks expert virtual bankrolls, calculates risk metrics, and detects elimination status.

Author: Financial Systems Engineer
Created: 2025-09-29
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics
from decimal import Decimal

logger = logging.getLogger(__name__)


class BankrollManager:
    """Manage expert virtual bankrolls and risk metrics."""

    # Risk thresholds
    SAFE_THRESHOLD = 0.70        # >= 70% of starting balance
    AT_RISK_THRESHOLD = 0.40     # 40-70% of starting balance
    DANGER_THRESHOLD = 0.20      # 20-40% of starting balance
    CRITICAL_THRESHOLD = 0.01    # 1-20% of starting balance (almost eliminated)

    # Volatility thresholds
    LOW_VOLATILITY = 0.10        # Standard deviation < 10%
    MEDIUM_VOLATILITY = 0.25     # Standard deviation 10-25%
    HIGH_VOLATILITY = 0.25       # Standard deviation > 25%

    def __init__(self, db_connection):
        """
        Initialize bankroll manager with database connection.

        Args:
            db_connection: Database connection (supabase client or similar)
        """
        self.db = db_connection
        self.logger = logging.getLogger(self.__class__.__name__)

    def update_balance(
        self,
        expert_id: str,
        bet_amount: float,
        payout_amount: float,
        result: str
    ) -> Dict:
        """
        Update expert bankroll after bet settlement.

        Args:
            expert_id: Expert identifier
            bet_amount: Amount that was wagered
            payout_amount: Amount returned (includes original bet if won)
            result: Bet result ('won', 'lost', 'push')

        Returns:
            Dict with updated bankroll info:
            {
                'previous_balance': float,
                'new_balance': float,
                'net_change': float,
                'elimination_risk_level': str,
                'was_eliminated': bool
            }
        """
        # Get current bankroll
        response = self.db.table('expert_virtual_bankrolls')\
            .select('*')\
            .eq('expert_id', expert_id)\
            .single()\
            .execute()

        if not response.data:
            raise ValueError(f"No bankroll found for expert {expert_id}")

        bankroll = response.data
        previous_balance = float(bankroll['current_balance'])

        # Calculate new balance
        if result == 'won':
            net_change = payout_amount - bet_amount
        elif result == 'lost':
            net_change = -bet_amount
        elif result == 'push':
            net_change = 0.0
        else:
            raise ValueError(f"Invalid bet result: {result}")

        new_balance = previous_balance + net_change

        # Check for elimination
        was_eliminated = new_balance <= 0
        if was_eliminated:
            new_balance = 0.0

        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(expert_id, new_balance, previous_balance)

        # Determine elimination risk level
        starting_balance = float(bankroll['starting_balance'])
        risk_level = self._determine_risk_level(new_balance, starting_balance)

        # Update database
        update_data = {
            'current_balance': new_balance,
            'elimination_risk_level': risk_level,
            'risk_metrics': risk_metrics,
            'updated_at': datetime.utcnow().isoformat()
        }

        if was_eliminated:
            update_data['season_status'] = 'eliminated'
            update_data['elimination_date'] = datetime.utcnow().isoformat()

        self.db.table('expert_virtual_bankrolls')\
            .update(update_data)\
            .eq('expert_id', expert_id)\
            .execute()

        self.logger.info(
            f"[{expert_id}] Balance updated: ${previous_balance:.2f} -> ${new_balance:.2f} "
            f"(change: {net_change:+.2f}, risk: {risk_level})"
        )

        if was_eliminated:
            self.logger.warning(f"[{expert_id}] ⚠️ ELIMINATED - Bankroll depleted")

        return {
            'previous_balance': previous_balance,
            'new_balance': new_balance,
            'net_change': net_change,
            'elimination_risk_level': risk_level,
            'was_eliminated': was_eliminated,
            'risk_metrics': risk_metrics
        }

    def get_bankroll(self, expert_id: str) -> Dict:
        """
        Get current bankroll status for an expert.

        Args:
            expert_id: Expert identifier

        Returns:
            Dict with bankroll information
        """
        response = self.db.table('expert_virtual_bankrolls')\
            .select('*')\
            .eq('expert_id', expert_id)\
            .single()\
            .execute()

        if not response.data:
            raise ValueError(f"No bankroll found for expert {expert_id}")

        return response.data

    def get_all_bankrolls(self) -> List[Dict]:
        """
        Get bankrolls for all experts.

        Returns:
            List of bankroll records
        """
        response = self.db.table('expert_virtual_bankrolls')\
            .select('*')\
            .order('current_balance', desc=True)\
            .execute()

        return response.data or []

    def detect_elimination(self, expert_id: str) -> bool:
        """
        Check if expert should be eliminated.

        Args:
            expert_id: Expert identifier

        Returns:
            True if expert is eliminated, False otherwise
        """
        bankroll = self.get_bankroll(expert_id)
        return float(bankroll['current_balance']) <= 0

    def get_leaderboard(self, season: Optional[int] = None) -> List[Dict]:
        """
        Get bankroll leaderboard ranked by current balance.

        Args:
            season: Optional season filter

        Returns:
            List of experts ranked by balance
        """
        query = self.db.table('expert_virtual_bankrolls')\
            .select('expert_id, current_balance, starting_balance, season_status, elimination_risk_level, risk_metrics')\
            .order('current_balance', desc=True)

        if season:
            query = query.eq('season', season)

        response = query.execute()

        leaderboard = []
        for idx, record in enumerate(response.data or [], start=1):
            current = float(record['current_balance'])
            starting = float(record['starting_balance'])
            roi = ((current - starting) / starting) * 100 if starting > 0 else 0

            leaderboard.append({
                'rank': idx,
                'expert_id': record['expert_id'],
                'current_balance': current,
                'starting_balance': starting,
                'roi_percentage': round(roi, 2),
                'season_status': record['season_status'],
                'elimination_risk_level': record['elimination_risk_level'],
                'risk_metrics': record['risk_metrics'] or {}
            })

        return leaderboard

    def _calculate_risk_metrics(
        self,
        expert_id: str,
        current_balance: float,
        previous_balance: float
    ) -> Dict:
        """
        Calculate risk metrics including volatility, Sharpe ratio, and max drawdown.

        Args:
            expert_id: Expert identifier
            current_balance: Current bankroll balance
            previous_balance: Previous bankroll balance

        Returns:
            Dict with risk metrics
        """
        # Fetch bet history for calculations
        response = self.db.table('expert_virtual_bets')\
            .select('bankroll_after, bet_placed_at')\
            .eq('expert_id', expert_id)\
            .not_.is_('bankroll_after', 'null')\
            .order('bet_placed_at', desc=False)\
            .execute()

        bet_history = response.data or []

        if len(bet_history) < 2:
            # Not enough data for meaningful metrics
            return {
                'volatility': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_streak': 0,
                'lose_streak': 0,
                'total_bets': len(bet_history)
            }

        # Calculate returns
        balances = [float(bet['bankroll_after']) for bet in bet_history]
        balances.append(current_balance)  # Include current balance

        returns = []
        for i in range(1, len(balances)):
            ret = (balances[i] - balances[i-1]) / balances[i-1] if balances[i-1] > 0 else 0
            returns.append(ret)

        # Volatility (standard deviation of returns)
        volatility = statistics.stdev(returns) if len(returns) > 1 else 0.0

        # Sharpe Ratio (mean return / volatility)
        # Assuming risk-free rate = 0 for simplicity
        mean_return = statistics.mean(returns) if returns else 0.0
        sharpe_ratio = (mean_return / volatility) if volatility > 0 else 0.0

        # Max Drawdown
        max_drawdown = self._calculate_max_drawdown(balances)

        # Win/Lose Streaks
        win_streak, lose_streak = self._calculate_streaks(expert_id)

        return {
            'volatility': round(volatility, 4),
            'sharpe_ratio': round(sharpe_ratio, 4),
            'max_drawdown': round(max_drawdown, 4),
            'win_streak': win_streak,
            'lose_streak': lose_streak,
            'total_bets': len(bet_history),
            'calculated_at': datetime.utcnow().isoformat()
        }

    def _calculate_max_drawdown(self, balances: List[float]) -> float:
        """
        Calculate maximum drawdown from peak.

        Args:
            balances: List of historical balances

        Returns:
            Maximum drawdown as a percentage
        """
        if not balances:
            return 0.0

        peak = balances[0]
        max_dd = 0.0

        for balance in balances:
            if balance > peak:
                peak = balance

            drawdown = (peak - balance) / peak if peak > 0 else 0
            max_dd = max(max_dd, drawdown)

        return max_dd

    def _calculate_streaks(self, expert_id: str) -> Tuple[int, int]:
        """
        Calculate current win streak and lose streak.

        Args:
            expert_id: Expert identifier

        Returns:
            Tuple of (win_streak, lose_streak)
        """
        # Get recent bet results
        response = self.db.table('expert_virtual_bets')\
            .select('result')\
            .eq('expert_id', expert_id)\
            .in_('result', ['won', 'lost'])\
            .order('bet_placed_at', desc=True)\
            .limit(50)\
            .execute()

        results = [bet['result'] for bet in (response.data or [])]

        if not results:
            return 0, 0

        # Calculate current streak
        current_streak = 1
        streak_type = results[0]

        for result in results[1:]:
            if result == streak_type:
                current_streak += 1
            else:
                break

        win_streak = current_streak if streak_type == 'won' else 0
        lose_streak = current_streak if streak_type == 'lost' else 0

        return win_streak, lose_streak

    def _determine_risk_level(self, current_balance: float, starting_balance: float) -> str:
        """
        Determine elimination risk level based on balance percentage.

        Args:
            current_balance: Current bankroll balance
            starting_balance: Starting bankroll balance

        Returns:
            Risk level: 'safe', 'at_risk', 'danger', 'critical'
        """
        if starting_balance <= 0:
            return 'critical'

        percentage = current_balance / starting_balance

        if percentage >= self.SAFE_THRESHOLD:
            return 'safe'
        elif percentage >= self.AT_RISK_THRESHOLD:
            return 'at_risk'
        elif percentage >= self.DANGER_THRESHOLD:
            return 'danger'
        else:
            return 'critical'