"""
Bet Placement Service

Automatically places bets for expert predictions with sufficient confidence.

Author: Financial Systems Engineer
Created: 2025-09-29
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import uuid

from .bet_sizer import get_bet_sizer
from .bankroll_manager import BankrollManager

logger = logging.getLogger(__name__)


class BetPlacer:
    """Automatically place bets for expert predictions."""

    def __init__(self, db_connection):
        """
        Initialize bet placer with database connection.

        Args:
            db_connection: Database connection (supabase client or similar)
        """
        self.db = db_connection
        self.bet_sizer = get_bet_sizer()
        self.bankroll_manager = BankrollManager(db_connection)
        self.logger = logging.getLogger(self.__class__.__name__)

    def process_prediction(
        self,
        expert_id: str,
        prediction_data: Dict
    ) -> Dict:
        """
        Process a prediction and place bet if conditions are met.

        Args:
            expert_id: Expert identifier
            prediction_data: Dict with prediction details:
                {
                    'game_id': str,
                    'prediction_category': str,
                    'confidence': float,
                    'vegas_odds': str,
                    'reasoning': str (optional)
                }

        Returns:
            Dict with placement result:
            {
                'bet_placed': bool,
                'bet_id': str (if placed),
                'bet_amount': float,
                'reason': str
            }
        """
        result = {
            'bet_placed': False,
            'bet_id': None,
            'bet_amount': 0.0,
            'reason': ''
        }

        try:
            # Validate required fields
            required_fields = ['game_id', 'prediction_category', 'confidence', 'vegas_odds']
            missing_fields = [f for f in required_fields if f not in prediction_data]
            if missing_fields:
                result['reason'] = f"Missing required fields: {', '.join(missing_fields)}"
                self.logger.error(f"[{expert_id}] {result['reason']}")
                return result

            # Get expert details
            expert = self._get_expert_details(expert_id)
            if not expert:
                result['reason'] = f"Expert {expert_id} not found"
                self.logger.error(result['reason'])
                return result

            # Get current bankroll
            bankroll_data = self.bankroll_manager.get_bankroll(expert_id)
            current_balance = float(bankroll_data['current_balance'])

            # Check if expert is eliminated
            if bankroll_data['season_status'] == 'eliminated':
                result['reason'] = "Expert is eliminated"
                self.logger.warning(f"[{expert_id}] {result['reason']}")
                return result

            # Calculate bet size
            bet_sizing = self.bet_sizer.get_bet_size(
                expert_id=expert_id,
                expert_personality=expert['archetype'],
                confidence=prediction_data['confidence'],
                odds=prediction_data['vegas_odds'],
                bankroll=current_balance
            )

            # Check if bet should be placed
            if not bet_sizing['should_bet']:
                result['reason'] = bet_sizing['reasoning']
                self.logger.info(f"[{expert_id}] Bet not placed: {result['reason']}")
                return result

            # Place the bet
            bet_id = self._place_bet(
                expert_id=expert_id,
                prediction_data=prediction_data,
                bet_sizing=bet_sizing,
                current_balance=current_balance
            )

            result['bet_placed'] = True
            result['bet_id'] = bet_id
            result['bet_amount'] = bet_sizing['bet_amount']
            result['reason'] = f"Bet placed successfully: ${bet_sizing['bet_amount']:.2f}"

            self.logger.info(
                f"[{expert_id}] ✅ Bet placed: ${bet_sizing['bet_amount']:.2f} on "
                f"{prediction_data['game_id']} ({prediction_data['prediction_category']})"
            )

            return result

        except Exception as e:
            result['reason'] = f"Error placing bet: {str(e)}"
            self.logger.error(f"[{expert_id}] {result['reason']}", exc_info=True)
            return result

    def process_multiple_predictions(
        self,
        predictions: List[Dict]
    ) -> List[Dict]:
        """
        Process multiple predictions in batch.

        Args:
            predictions: List of prediction dicts with 'expert_id' field

        Returns:
            List of placement results
        """
        results = []

        for prediction in predictions:
            expert_id = prediction.get('expert_id')
            if not expert_id:
                self.logger.error("Prediction missing expert_id field")
                continue

            result = self.process_prediction(expert_id, prediction)
            results.append({
                'expert_id': expert_id,
                'game_id': prediction.get('game_id'),
                **result
            })

        # Log summary
        placed_count = sum(1 for r in results if r['bet_placed'])
        total_amount = sum(r['bet_amount'] for r in results if r['bet_placed'])

        self.logger.info(
            f"Batch processing complete: {placed_count}/{len(results)} bets placed, "
            f"total amount: ${total_amount:.2f}"
        )

        return results

    def get_pending_bets(self, expert_id: Optional[str] = None) -> List[Dict]:
        """
        Get all pending (unsettled) bets.

        Args:
            expert_id: Optional filter by expert

        Returns:
            List of pending bet records
        """
        query = self.db.table('expert_virtual_bets')\
            .select('*')\
            .eq('result', 'pending')\
            .order('bet_placed_at', desc=True)

        if expert_id:
            query = query.eq('expert_id', expert_id)

        response = query.execute()
        return response.data or []

    def get_bet_history(
        self,
        expert_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get bet history for an expert.

        Args:
            expert_id: Expert identifier
            limit: Maximum number of records to return

        Returns:
            List of bet records
        """
        response = self.db.table('expert_virtual_bets')\
            .select('*')\
            .eq('expert_id', expert_id)\
            .order('bet_placed_at', desc=True)\
            .limit(limit)\
            .execute()

        return response.data or []

    def _place_bet(
        self,
        expert_id: str,
        prediction_data: Dict,
        bet_sizing: Dict,
        current_balance: float
    ) -> str:
        """
        Insert bet record into database.

        Args:
            expert_id: Expert identifier
            prediction_data: Prediction details
            bet_sizing: Bet sizing calculation result
            current_balance: Current bankroll balance

        Returns:
            Bet ID (UUID)
        """
        bet_id = str(uuid.uuid4())

        bet_record = {
            'id': bet_id,
            'expert_id': expert_id,
            'game_id': prediction_data['game_id'],
            'prediction_category': prediction_data['prediction_category'],
            'bet_amount': bet_sizing['bet_amount'],
            'vegas_odds': prediction_data['vegas_odds'],
            'prediction_confidence': prediction_data['confidence'],
            'bet_placed_at': datetime.utcnow().isoformat(),
            'result': 'pending',
            'bankroll_before': current_balance,
            'reasoning': prediction_data.get('reasoning', bet_sizing['reasoning']),
            'kelly_criterion_suggested': bet_sizing['kelly_suggested'],
            'personality_adjustment': bet_sizing['personality_adjustment'],
            'edge_calculation': bet_sizing['edge'],
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        self.db.table('expert_virtual_bets')\
            .insert(bet_record)\
            .execute()

        return bet_id

    def _get_expert_details(self, expert_id: str) -> Optional[Dict]:
        """
        Get expert details from database.

        Args:
            expert_id: Expert identifier

        Returns:
            Expert record or None if not found
        """
        response = self.db.table('expert_models')\
            .select('*')\
            .eq('expert_id', expert_id)\
            .single()\
            .execute()

        return response.data if response.data else None