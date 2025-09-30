"""
Supabase Database Service
"""
from supabase import create_client, Client
from typing import Optional, List, Dict, Any
from src.api.config import settings
import logging

logger = logging.getLogger(__name__)


class DatabaseService:
    """Supabase database client wrapper"""

    def __init__(self):
        self.client: Optional[Client] = None

    async def initialize(self):
        """Initialize Supabase client"""
        try:
            if settings.supabase_url and settings.supabase_key:
                self.client = create_client(
                    settings.supabase_url,
                    settings.supabase_key
                )
                logger.info("Supabase client initialized successfully")
            else:
                logger.warning("Supabase credentials not configured")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise

    async def get_experts(self) -> List[Dict[str, Any]]:
        """Get all experts with current stats"""
        if not self.client:
            raise RuntimeError("Database not initialized")

        try:
            response = self.client.table("experts").select("*").execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching experts: {e}")
            raise

    async def get_expert_by_id(self, expert_id: str) -> Optional[Dict[str, Any]]:
        """Get expert by ID"""
        if not self.client:
            raise RuntimeError("Database not initialized")

        try:
            response = self.client.table("experts").select("*").eq("expert_id", expert_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching expert {expert_id}: {e}")
            raise

    async def get_expert_bankroll_history(
        self,
        expert_id: str,
        timeframe: str = "week"
    ) -> Dict[str, Any]:
        """Get expert bankroll history"""
        if not self.client:
            raise RuntimeError("Database not initialized")

        try:
            response = self.client.table("bankroll_history").select("*").eq(
                "expert_id", expert_id
            ).execute()
            return {"history": response.data}
        except Exception as e:
            logger.error(f"Error fetching bankroll history for {expert_id}: {e}")
            raise

    async def get_expert_predictions(
        self,
        expert_id: str,
        week: Optional[int] = None,
        status: Optional[str] = None,
        min_confidence: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Get expert predictions"""
        if not self.client:
            raise RuntimeError("Database not initialized")

        try:
            query = self.client.table("predictions").select("*").eq("expert_id", expert_id)

            if week:
                query = query.eq("week", week)
            if status:
                query = query.eq("status", status)
            if min_confidence:
                query = query.gte("confidence", min_confidence)

            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching predictions for {expert_id}: {e}")
            raise

    async def get_expert_memories(
        self,
        expert_id: str,
        limit: int = 20,
        offset: int = 0,
        importance_min: Optional[float] = None
    ) -> Dict[str, Any]:
        """Get expert memories"""
        if not self.client:
            raise RuntimeError("Database not initialized")

        try:
            query = self.client.table("memories").select("*").eq("expert_id", expert_id)

            if importance_min:
                query = query.gte("importance_score", importance_min)

            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

            response = query.execute()

            # Get total count
            count_response = self.client.table("memories").select(
                "count", count="exact"
            ).eq("expert_id", expert_id).execute()

            return {
                "memories": response.data,
                "total_count": count_response.count if hasattr(count_response, 'count') else len(response.data)
            }
        except Exception as e:
            logger.error(f"Error fetching memories for {expert_id}: {e}")
            raise

    async def get_council_current(self, week: Optional[int] = None) -> Dict[str, Any]:
        """Get current council members"""
        if not self.client:
            raise RuntimeError("Database not initialized")

        try:
            query = self.client.table("council_members").select("*")

            if week:
                query = query.eq("week", week)

            query = query.order("rank", desc=False).limit(5)

            response = query.execute()
            return {"members": response.data}
        except Exception as e:
            logger.error(f"Error fetching council: {e}")
            raise

    async def get_consensus_for_game(self, game_id: str) -> Dict[str, Any]:
        """Get council consensus for specific game"""
        if not self.client:
            raise RuntimeError("Database not initialized")

        try:
            response = self.client.table("consensus_predictions").select("*").eq(
                "game_id", game_id
            ).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error fetching consensus for game {game_id}: {e}")
            raise

    async def get_live_bets(
        self,
        game_id: Optional[str] = None,
        expert_id: Optional[str] = None,
        limit: int = 50,
        status: str = "pending"
    ) -> List[Dict[str, Any]]:
        """Get live betting feed"""
        if not self.client:
            raise RuntimeError("Database not initialized")

        try:
            query = self.client.table("bets").select("*").eq("status", status)

            if game_id:
                query = query.eq("game_id", game_id)
            if expert_id:
                query = query.eq("expert_id", expert_id)

            query = query.order("placed_at", desc=True).limit(limit)

            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching live bets: {e}")
            raise

    async def get_bet_history(
        self,
        expert_id: str,
        limit: int = 50,
        offset: int = 0,
        result: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get bet history for expert"""
        if not self.client:
            raise RuntimeError("Database not initialized")

        try:
            query = self.client.table("bets").select("*").eq("expert_id", expert_id)

            if result and result != "all":
                query = query.eq("status", result)

            query = query.order("settled_at", desc=True).range(offset, offset + limit - 1)

            response = query.execute()
            return {"bets": response.data}
        except Exception as e:
            logger.error(f"Error fetching bet history for {expert_id}: {e}")
            raise

    async def get_week_games(
        self,
        week_number: int,
        include_predictions: bool = True,
        include_odds: bool = True
    ) -> List[Dict[str, Any]]:
        """Get games for specific week"""
        if not self.client:
            raise RuntimeError("Database not initialized")

        try:
            response = self.client.table("games").select("*").eq("week", week_number).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching games for week {week_number}: {e}")
            raise

    async def get_active_battles(
        self,
        week: Optional[int] = None,
        min_difference: float = 3.0
    ) -> List[Dict[str, Any]]:
        """Get active prediction battles"""
        if not self.client:
            raise RuntimeError("Database not initialized")

        try:
            query = self.client.table("prediction_battles").select("*")

            if week:
                query = query.eq("week", week)

            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching battles: {e}")
            raise


# Singleton instance
db_service = DatabaseService()