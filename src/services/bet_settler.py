"""
Bet Settlement Service

Processes game results and settles pending bets with payout calculations.

Author: Financial Systems Engineer
Created: 2025-09-29
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from .bankroll_manager import BankrollManager

logger = logging.getLogger(__name__)


class BetSettler:
    """Settle bets after game completion and update bankrolls."""

    def __init__(self, db_connection):
        """
        Initialize bet settler with database connection.

        Args:
            db_connection: Database connection (supabase client or similar)
        """
        self.db = db_connection
        self.bankroll_manager = BankrollManager(db_connection)
        self.logger = logging.getLogger(self.__class__.__name__)

    def settle_game_bets(self, game_id: str, game_result: Dict) -> Dict:
        """
        Settle all pending bets for a completed game.

        Args:
            game_id: Game identifier
            game_result: Dict with actual game outcome:
                {
                    'home_score': int,
                    'away_score': int,
                    'home_team': str,
                    'away_team': str,
                    'spread_result': str ('home_covered', 'away_covered', 'push'),
                    'total_result': str ('over', 'under', 'push'),
                    'winner': str ('home', 'away', 'tie')
                }

        Returns:
            Dict with settlement summary:
            {
                'game_id': str,
                'bets_settled': int,
                'total_payouts': float,
                'experts_eliminated': List[str]
            }
        """
        summary = {
            'game_id': game_id,
            'bets_settled': 0,
            'total_payouts': 0.0,
            'experts_eliminated': []
        }

        # Get all pending bets for this game
        pending_bets = self.db.table('expert_virtual_bets')\
            .select('*')\
            .eq('game_id', game_id)\
            .eq('result', 'pending')\
            .execute()

        if not pending_bets.data:
            self.logger.info(f"No pending bets found for game {game_id}")
            return summary

        self.logger.info(
            f"Settling {len(pending_bets.data)} bets for game {game_id}"
        )

        # Process each bet
        for bet in pending_bets.data:
            try:
                settlement = self._settle_single_bet(bet, game_result)

                summary['bets_settled'] += 1
                summary['total_payouts'] += settlement['payout_amount']

                if settlement['expert_eliminated']:
                    summary['experts_eliminated'].append(bet['expert_id'])

            except Exception as e:
                self.logger.error(
                    f"Error settling bet {bet['id']}: {str(e)}",
                    exc_info=True
                )

        self.logger.info(
            f"Game {game_id} settlement complete: {summary['bets_settled']} bets, "
            f"${summary['total_payouts']:.2f} in payouts, "
            f"{len(summary['experts_eliminated'])} experts eliminated"
        )

        return summary

    def settle_single_bet(self, bet_id: str, game_result: Dict) -> Dict:
        """
        Settle a single bet by ID.

        Args:
            bet_id: Bet identifier (UUID)
            game_result: Game outcome dict

        Returns:
            Settlement result dict
        """
        # Get bet record
        response = self.db.table('expert_virtual_bets')\
            .select('*')\
            .eq('id', bet_id)\
            .single()\
            .execute()

        if not response.data:
            raise ValueError(f"Bet {bet_id} not found")

        bet = response.data

        if bet['result'] != 'pending':
            self.logger.warning(f"Bet {bet_id} already settled with result: {bet['result']}")
            return {
                'already_settled': True,
                'result': bet['result']
            }

        return self._settle_single_bet(bet, game_result)

    def _settle_single_bet(self, bet: Dict, game_result: Dict) -> Dict:
        """
        Internal method to settle a single bet.

        Args:
            bet: Bet record from database
            game_result: Game outcome dict

        Returns:
            Settlement result dict
        """
        # Determine bet outcome
        bet_result = self._determine_bet_result(
            bet['prediction_category'],
            game_result
        )

        # Calculate payout using database function
        payout_amount = self._calculate_payout(
            bet_amount=float(bet['bet_amount']),
            vegas_odds=bet['vegas_odds'],
            result=bet_result
        )

        # Get bankroll before
        bankroll_before = float(bet['bankroll_before'])

        # Calculate new balance
        if bet_result == 'won':
            bankroll_after = bankroll_before + (payout_amount - float(bet['bet_amount']))
        elif bet_result == 'lost':
            bankroll_after = bankroll_before - float(bet['bet_amount'])
        elif bet_result == 'push':
            bankroll_after = bankroll_before  # No change on push
        else:
            raise ValueError(f"Invalid bet result: {bet_result}")

        # Update bet record
        self.db.table('expert_virtual_bets')\
            .update({
                'result': bet_result,
                'payout_amount': payout_amount,
                'bankroll_after': bankroll_after,
                'updated_at': datetime.utcnow().isoformat()
            })\
            .eq('id', bet['id'])\
            .execute()

        # Update bankroll
        bankroll_update = self.bankroll_manager.update_balance(
            expert_id=bet['expert_id'],
            bet_amount=float(bet['bet_amount']),
            payout_amount=payout_amount,
            result=bet_result
        )

        self.logger.info(
            f"[{bet['expert_id']}] Bet settled: {bet_result.upper()} - "
            f"${bet['bet_amount']:.2f} -> ${payout_amount:.2f} "
            f"(balance: ${bankroll_before:.2f} -> ${bankroll_after:.2f})"
        )

        return {
            'bet_id': bet['id'],
            'expert_id': bet['expert_id'],
            'result': bet_result,
            'bet_amount': float(bet['bet_amount']),
            'payout_amount': payout_amount,
            'bankroll_before': bankroll_before,
            'bankroll_after': bankroll_after,
            'expert_eliminated': bankroll_update['was_eliminated']
        }

    def _determine_bet_result(
        self,
        prediction_category: str,
        game_result: Dict
    ) -> str:
        """
        Determine if bet won, lost, or pushed based on game outcome.

        Args:
            prediction_category: Type of bet (e.g., 'spread', 'total', 'moneyline')
            game_result: Actual game outcome

        Returns:
            Bet result: 'won', 'lost', or 'push'
        """
        category = prediction_category.lower()

        if 'spread' in category or 'ats' in category:
            spread_result = game_result.get('spread_result', '').lower()
            if spread_result == 'push':
                return 'push'

            # Check if prediction matches outcome
            if 'home' in category and 'home_covered' in spread_result:
                return 'won'
            elif 'away' in category and 'away_covered' in spread_result:
                return 'won'
            else:
                return 'lost'

        elif 'total' in category or 'over' in category or 'under' in category:
            total_result = game_result.get('total_result', '').lower()
            if total_result == 'push':
                return 'push'

            if 'over' in category and total_result == 'over':
                return 'won'
            elif 'under' in category and total_result == 'under':
                return 'won'
            else:
                return 'lost'

        elif 'moneyline' in category or 'winner' in category:
            winner = game_result.get('winner', '').lower()
            if winner == 'tie':
                return 'push'

            if 'home' in category and winner == 'home':
                return 'won'
            elif 'away' in category and winner == 'away':
                return 'won'
            else:
                return 'lost'

        else:
            self.logger.warning(f"Unknown prediction category: {prediction_category}")
            return 'lost'  # Default to lost if category is unclear

    def _calculate_payout(
        self,
        bet_amount: float,
        vegas_odds: str,
        result: str
    ) -> float:
        """
        Calculate payout from Vegas odds.

        This uses the PostgreSQL function calculate_payout() defined in the migration.

        Args:
            bet_amount: Amount wagered
            vegas_odds: American odds format ('+150', '-110', 'EVEN')
            result: Bet result ('won', 'lost', 'push')

        Returns:
            Payout amount (0 if lost)
        """
        if result == 'lost':
            return 0.0
        elif result == 'push':
            return bet_amount  # Return original bet on push

        # Parse American odds
        odds_str = vegas_odds.strip().upper()

        if odds_str == 'EVEN':
            return bet_amount * 2.0  # Even odds = 1:1

        # Remove '+' or '-' and convert to integer
        try:
            odds_value = abs(int(odds_str))
            is_positive = odds_str.startswith('+')

            if is_positive:
                # Positive odds: profit = (bet_amount * odds / 100)
                profit = bet_amount * (odds_value / 100.0)
            else:
                # Negative odds: profit = (bet_amount * 100 / odds)
                profit = bet_amount * (100.0 / odds_value)

            # Payout = original bet + profit
            payout = bet_amount + profit
            return round(payout, 2)

        except (ValueError, ZeroDivisionError) as e:
            self.logger.error(f"Error parsing odds '{vegas_odds}': {str(e)}")
            return bet_amount  # Return original bet on error

    def get_settled_bets(
        self,
        game_id: Optional[str] = None,
        expert_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get settled bets with optional filters.

        Args:
            game_id: Optional filter by game
            expert_id: Optional filter by expert
            limit: Maximum records to return

        Returns:
            List of settled bet records
        """
        query = self.db.table('expert_virtual_bets')\
            .select('*')\
            .neq('result', 'pending')\
            .order('updated_at', desc=True)\
            .limit(limit)

        if game_id:
            query = query.eq('game_id', game_id)

        if expert_id:
            query = query.eq('expert_id', expert_id)

        response = query.execute()
        return response.data or []

    def recalculate_elimination_status(self) -> Dict:
        """
        Recalculate elimination status for all experts.

        Useful for fixing any inconsistencies in the data.

        Returns:
            Dict with summary of updates
        """
        summary = {
            'total_experts': 0,
            'eliminated': 0,
            'at_risk': 0,
            'updated': 0
        }

        all_bankrolls = self.bankroll_manager.get_all_bankrolls()
        summary['total_experts'] = len(all_bankrolls)

        for bankroll in all_bankrolls:
            expert_id = bankroll['expert_id']
            current_balance = float(bankroll['current_balance'])

            # Check for elimination
            should_be_eliminated = current_balance <= 0
            is_eliminated = bankroll['season_status'] == 'eliminated'

            if should_be_eliminated and not is_eliminated:
                # Expert should be eliminated but isn't
                self.db.table('expert_virtual_bankrolls')\
                    .update({
                        'season_status': 'eliminated',
                        'elimination_risk_level': 'critical',
                        'elimination_date': datetime.utcnow().isoformat(),
                        'updated_at': datetime.utcnow().isoformat()
                    })\
                    .eq('expert_id', expert_id)\
                    .execute()

                summary['updated'] += 1
                summary['eliminated'] += 1

                self.logger.warning(f"[{expert_id}] Status corrected to ELIMINATED")

            elif is_eliminated:
                summary['eliminated'] += 1

            # Count at-risk experts
            risk_level = bankroll.get('elimination_risk_level', 'safe')
            if risk_level in ['danger', 'critical']:
                summary['at_risk'] += 1

        self.logger.info(
            f"Elimination status recalculation complete: "
            f"{summary['total_experts']} experts, "
            f"{summary['eliminated']} eliminated, "
            f"{summary['at_risk']} at risk, "
            f"{summary['updated']} updated"
        )

        return summary