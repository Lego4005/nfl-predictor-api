#!/usr/bin/env python3
"""
Run Tonight's NFL Predictions with Reasoning Chain Logging

This script runs predictions for tonight's NFL games using all 15 personality-driven experts,
capturing their detailed reasoning chains, and storing everything in the database.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import sys
import os
from dataclasses import dataclass
from collections import defaultdict

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the new services
from src.ml.reasoning_chain_logger import ReasoningChainLogger
from src.ml.belief_revision_service import BeliefRevisionService
from src.ml.episodic_memory_manager import EpisodicMemoryManager

# Import existing system components
from src.ml.personality_driven_experts import (
    UniversalGameData,
    TheAnalyst,
    TheGambler,
    TheHistorian,
    TheContrarian,
    TheOptimist,
    ThePessimist,
    TheMomentumRider,
    TheUnderdogLover,
    TheFavoriteFollower,
    TheWeatherWatcher,
    ThePrimetimeSpecialist,
    TheDivisionExpert,
    TheRookie,
    TheVeteran,
    TheBalancedMind
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TonightGame:
    """Tonight's game data"""
    game_id: str
    home_team: str
    away_team: str
    start_time: str
    spread: float  # Negative means home team favored
    total: float
    home_moneyline: int
    away_moneyline: int

class PredictionOrchestrator:
    """Orchestrates predictions with reasoning chain logging"""

    def __init__(self, supabase_client=None):
        # Initialize services
        self.reasoning_logger = ReasoningChainLogger(supabase_client)
        self.belief_service = BeliefRevisionService(supabase_client)
        self.memory_manager = EpisodicMemoryManager(supabase_client)
        self.supabase = supabase_client

        # Initialize all 15 experts
        self.experts = self._initialize_experts()

        logger.info(f"✅ Initialized {len(self.experts)} personality-driven experts")

    def _initialize_experts(self) -> Dict[str, Any]:
        """Initialize all 15 personality experts"""
        experts = {
            "the_analyst": TheAnalyst(),
            "the_gambler": TheGambler(),
            "the_historian": TheHistorian(),
            "the_contrarian": TheContrarian(),
            "the_optimist": TheOptimist(),
            "the_pessimist": ThePessimist(),
            "the_momentum_rider": TheMomentumRider(),
            "the_underdog_lover": TheUnderdogLover(),
            "the_favorite_follower": TheFavoriteFollower(),
            "the_weather_watcher": TheWeatherWatcher(),
            "the_primetime_specialist": ThePrimetimeSpecialist(),
            "the_division_expert": TheDivisionExpert(),
            "the_rookie": TheRookie(),
            "the_veteran": TheVeteran(),
            "the_balanced_mind": TheBalancedMind()
        }

        # Map experts to their personality types for monologue generation
        self.expert_personalities = {
            "the_analyst": "analytical",
            "the_gambler": "intuitive",
            "the_historian": "conservative",
            "the_contrarian": "contrarian",
            "the_optimist": "intuitive",
            "the_pessimist": "conservative",
            "the_momentum_rider": "momentum",
            "the_underdog_lover": "contrarian",
            "the_favorite_follower": "conservative",
            "the_weather_watcher": "analytical",
            "the_primetime_specialist": "analytical",
            "the_division_expert": "analytical",
            "the_rookie": "intuitive",
            "the_veteran": "conservative",
            "the_balanced_mind": "analytical"
        }

        return experts

    async def fetch_tonight_games(self) -> List[TonightGame]:
        """Fetch tonight's NFL games"""
        # For testing, we'll use a hardcoded Monday Night Football game
        # In production, this would fetch from ESPN API or similar

        tonight = datetime.now().strftime("%Y-%m-%d")

        games = [
            TonightGame(
                game_id=f"BUF_NYJ_{tonight}",
                home_team="New York Jets",
                away_team="Buffalo Bills",
                start_time="8:15 PM ET",
                spread=2.5,  # Jets +2.5
                total=41.5,
                home_moneyline=125,
                away_moneyline=-145
            )
        ]

        logger.info(f"📅 Found {len(games)} game(s) for tonight")
        return games

    def _create_universal_game_data(self, game: TonightGame) -> UniversalGameData:
        """Create UniversalGameData object for a game"""
        return UniversalGameData(
            home_team=game.home_team,
            away_team=game.away_team,
            game_time=game.start_time,
            location="MetLife Stadium",

            # Weather (NYC area tonight - example data)
            weather={
                "temperature": 48,
                "wind_speed": 8,
                "condition": "Clear",
                "humidity": 65,
                "outdoor": True
            },

            # Injuries (example data - would fetch from injury report API)
            injuries={
                game.home_team: [
                    {"player": "Garrett Wilson", "position": "WR", "status": "Questionable"},
                    {"player": "C.J. Mosley", "position": "LB", "status": "Doubtful"}
                ],
                game.away_team: [
                    {"player": "Matt Milano", "position": "LB", "status": "Out"},
                    {"player": "DaQuan Jones", "position": "DT", "status": "Questionable"}
                ]
            },

            # Team statistics (season averages - example data)
            team_stats={
                game.home_team: {
                    "points_per_game": 18.5,
                    "points_allowed": 24.2,
                    "yards_per_game": 289.3,
                    "yards_allowed": 356.7,
                    "turnover_differential": -3,
                    "record": "2-3"
                },
                game.away_team: {
                    "points_per_game": 28.4,
                    "points_allowed": 19.8,
                    "yards_per_game": 371.2,
                    "yards_allowed": 298.5,
                    "turnover_differential": 5,
                    "record": "4-1"
                }
            },

            # Market data
            line_movement={
                "opening_spread": 3.0,
                "current_spread": game.spread,
                "opening_total": 42.5,
                "current_total": game.total,
                "line_direction": "toward_home"
            },

            public_betting={
                "spread_percentage_home": 35,
                "spread_percentage_away": 65,
                "moneyline_percentage_home": 28,
                "moneyline_percentage_away": 72,
                "total_over_percentage": 58
            },

            # Recent news
            recent_news=[
                {"headline": "Bills offense clicking after slow start", "impact": "positive_away"},
                {"headline": "Jets defense shows improvement in red zone", "impact": "positive_home"},
                {"headline": "Division rivalry adds extra intensity", "impact": "neutral"}
            ],

            # Historical matchups
            head_to_head={
                "last_5_meetings": "Bills 4-1",
                "last_home_game": "Jets won 20-17",
                "avg_total_points": 38.4,
                "avg_margin": 7.2
            },

            # Coaching info
            coaching_info={
                game.home_team: {"coach": "Robert Saleh", "record_vs_opponent": "1-4"},
                game.away_team: {"coach": "Sean McDermott", "record_vs_opponent": "8-3"}
            }
        )

    async def run_expert_prediction(
        self,
        expert_id: str,
        expert: Any,
        game: TonightGame,
        universal_data: UniversalGameData
    ) -> Dict:
        """Run prediction for a single expert with reasoning logging"""

        logger.info(f"🤔 {expert_id} analyzing {game.away_team} @ {game.home_team}...")

        # Get expert's personality-driven prediction
        prediction = expert.make_personality_driven_prediction(universal_data)

        # Extract reasoning factors from the expert's process
        factors = self._extract_reasoning_factors(expert, universal_data, prediction)

        # Generate confidence scores
        confidence = {
            "overall": prediction.get("confidence", 0.65),
            "winner": prediction.get("winner_confidence", 0.7),
            "spread": prediction.get("spread_confidence", 0.6),
            "total": prediction.get("total_confidence", 0.6)
        }

        # Log the reasoning chain
        chain_id = await self.reasoning_logger.log_reasoning_chain(
            expert_id=expert_id,
            game_id=game.game_id,
            prediction={
                "winner": prediction.get("predicted_winner"),
                "spread": prediction.get("predicted_spread"),
                "total": prediction.get("predicted_total")
            },
            factors=factors,
            monologue=None,  # Will be auto-generated based on personality
            confidence=confidence,
            expert_personality=self.expert_personalities[expert_id]
        )

        # Store the full prediction result
        full_prediction = {
            "expert_id": expert_id,
            "game_id": game.game_id,
            "prediction": prediction,
            "reasoning_chain_id": chain_id,
            "confidence": confidence,
            "factors": factors,
            "timestamp": datetime.utcnow().isoformat()
        }

        return full_prediction

    def _extract_reasoning_factors(
        self,
        expert: Any,
        data: UniversalGameData,
        prediction: Dict
    ) -> List[Dict]:
        """Extract reasoning factors from expert's decision process"""

        factors = []

        # Home/Away performance factor
        home_stats = data.team_stats[data.home_team]
        away_stats = data.team_stats[data.away_team]

        factors.append({
            "factor": "team_performance",
            "value": f"{data.away_team} averaging {away_stats['points_per_game']:.1f} PPG vs {data.home_team} {home_stats['points_per_game']:.1f} PPG",
            "weight": 0.7,
            "confidence": 0.8,
            "source": "season_stats"
        })

        # Injuries factor
        home_injuries = len([i for i in data.injuries.get(data.home_team, []) if i['status'] in ['Out', 'Doubtful']])
        away_injuries = len([i for i in data.injuries.get(data.away_team, []) if i['status'] in ['Out', 'Doubtful']])

        factors.append({
            "factor": "injury_impact",
            "value": f"{data.home_team} has {home_injuries} key injuries, {data.away_team} has {away_injuries}",
            "weight": 0.5,
            "confidence": 0.7,
            "source": "injury_report"
        })

        # Market movement factor
        line_move = data.line_movement['current_spread'] - data.line_movement['opening_spread']
        factors.append({
            "factor": "line_movement",
            "value": f"Line moved {abs(line_move)} points {'toward home' if line_move > 0 else 'toward away'}",
            "weight": 0.4,
            "confidence": 0.6,
            "source": "market_data"
        })

        # Public betting factor
        factors.append({
            "factor": "public_betting",
            "value": f"{data.public_betting['spread_percentage_away']}% on {data.away_team}",
            "weight": 0.3,
            "confidence": 0.65,
            "source": "betting_percentages"
        })

        # Weather factor (if outdoor)
        if data.weather.get('outdoor', False):
            factors.append({
                "factor": "weather_conditions",
                "value": f"{data.weather['temperature']}°F, {data.weather['wind_speed']} mph wind",
                "weight": 0.35,
                "confidence": 0.75,
                "source": "weather_data"
            })

        # Historical matchup factor
        factors.append({
            "factor": "head_to_head",
            "value": f"{data.away_team} {data.head_to_head['last_5_meetings']} in last 5",
            "weight": 0.45,
            "confidence": 0.7,
            "source": "historical_pattern"
        })

        # Primetime factor (for Monday Night Football)
        factors.append({
            "factor": "primetime_game",
            "value": "Monday Night Football divisional matchup",
            "weight": 0.25,
            "confidence": 0.6,
            "source": "situational"
        })

        return factors

    async def run_all_predictions(self, game: TonightGame) -> Dict:
        """Run predictions for all experts on a game"""

        logger.info(f"\n{'='*60}")
        logger.info(f"🏈 Running predictions for: {game.away_team} @ {game.home_team}")
        logger.info(f"   Spread: {game.home_team} {'+' if game.spread > 0 else ''}{game.spread}")
        logger.info(f"   Total: {game.total}")
        logger.info(f"{'='*60}\n")

        # Create universal game data
        universal_data = self._create_universal_game_data(game)

        # Run predictions for all experts
        all_predictions = {}
        prediction_tasks = []

        for expert_id, expert in self.experts.items():
            task = self.run_expert_prediction(expert_id, expert, game, universal_data)
            prediction_tasks.append(task)

        # Run all predictions concurrently
        predictions = await asyncio.gather(*prediction_tasks)

        # Organize predictions by expert
        for pred in predictions:
            all_predictions[pred['expert_id']] = pred

        return all_predictions

    def generate_predictions_report(self, game: TonightGame, predictions: Dict) -> str:
        """Generate human-readable predictions report"""

        report = []
        report.append(f"\n{'='*80}")
        report.append(f"🏈 PREDICTIONS REPORT: {game.away_team} @ {game.home_team}")
        report.append(f"{'='*80}\n")
        report.append(f"Game Time: {game.start_time}")
        report.append(f"Current Line: {game.home_team} {'+' if game.spread > 0 else ''}{game.spread}")
        report.append(f"Total: {game.total} | ML: {game.home_team} {game.home_moneyline:+d} / {game.away_team} {game.away_moneyline:+d}\n")
        report.append(f"{'-'*80}\n")

        # Tally predictions
        winner_picks = defaultdict(int)
        spread_picks = {"home": 0, "away": 0}
        total_picks = {"over": 0, "under": 0}

        # Individual expert predictions
        report.append("EXPERT PREDICTIONS:\n")

        for expert_id, pred_data in predictions.items():
            pred = pred_data['prediction']
            conf = pred_data['confidence']

            # Count picks
            winner = pred.get('predicted_winner', 'Unknown')
            winner_picks[winner] += 1

            if pred.get('predicted_spread', 0) > game.spread:
                spread_picks['away'] += 1
            else:
                spread_picks['home'] += 1

            if pred.get('predicted_total', 0) > game.total:
                total_picks['over'] += 1
            else:
                total_picks['under'] += 1

            # Format expert name
            expert_name = expert_id.replace('_', ' ').title()

            # Get top reasoning factor
            top_factor = pred_data['factors'][0] if pred_data['factors'] else {"value": "No factors"}

            report.append(f"📊 {expert_name}")
            report.append(f"   Pick: {winner} | Spread: {pred.get('predicted_spread', 'N/A')} | Total: {pred.get('predicted_total', 'N/A')}")
            report.append(f"   Confidence: {conf['overall']:.0%} (W: {conf['winner']:.0%}, S: {conf['spread']:.0%}, T: {conf['total']:.0%})")
            report.append(f"   Key Factor: {top_factor['value']}")
            report.append("")

        # Summary
        report.append(f"{'-'*80}\n")
        report.append("CONSENSUS SUMMARY:\n")

        # Winner consensus
        total_experts = len(predictions)
        for team, count in winner_picks.items():
            pct = (count / total_experts) * 100
            report.append(f"  {team}: {count}/{total_experts} experts ({pct:.0f}%)")

        report.append("")

        # Spread consensus
        home_spread_pct = (spread_picks['home'] / total_experts) * 100
        away_spread_pct = (spread_picks['away'] / total_experts) * 100
        report.append(f"  {game.home_team} {'+' if game.spread > 0 else ''}{game.spread}: {spread_picks['home']}/{total_experts} ({home_spread_pct:.0f}%)")
        report.append(f"  {game.away_team} {'+' if game.spread < 0 else ''}{-game.spread}: {spread_picks['away']}/{total_experts} ({away_spread_pct:.0f}%)")

        report.append("")

        # Total consensus
        over_pct = (total_picks['over'] / total_experts) * 100
        under_pct = (total_picks['under'] / total_experts) * 100
        report.append(f"  Over {game.total}: {total_picks['over']}/{total_experts} ({over_pct:.0f}%)")
        report.append(f"  Under {game.total}: {total_picks['under']}/{total_experts} ({under_pct:.0f}%)")

        report.append(f"\n{'='*80}\n")

        return '\n'.join(report)

    async def run_tonight_predictions(self):
        """Main execution method"""

        logger.info("🚀 Starting NFL prediction run with reasoning chain logging...")

        # Fetch tonight's games
        games = await self.fetch_tonight_games()

        if not games:
            logger.warning("No games found for tonight")
            return

        # Run predictions for each game
        all_game_predictions = {}

        for game in games:
            predictions = await self.run_all_predictions(game)
            all_game_predictions[game.game_id] = predictions

            # Generate and print report
            report = self.generate_predictions_report(game, predictions)
            print(report)

            # Save report to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"predictions_report_{game.game_id}_{timestamp}.txt"
            with open(report_file, 'w') as f:
                f.write(report)
            logger.info(f"📝 Report saved to {report_file}")

        logger.info("✅ Prediction run complete!")

        # Store predictions summary in database if available
        if self.supabase:
            try:
                summary = {
                    "run_timestamp": datetime.utcnow().isoformat(),
                    "games_predicted": len(games),
                    "experts_used": len(self.experts),
                    "game_ids": [g.game_id for g in games]
                }

                self.supabase.table('prediction_runs').insert(summary).execute()
                logger.info("💾 Prediction run summary stored in database")
            except Exception as e:
                logger.warning(f"Could not store summary in database: {e}")

        return all_game_predictions


async def main():
    """Main entry point"""

    # Initialize Supabase client if credentials are available
    supabase_client = None

    # Try to load Supabase credentials from environment
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

    if supabase_url and supabase_key:
        try:
            from supabase import create_client
            supabase_client = create_client(supabase_url, supabase_key)
            logger.info("✅ Connected to Supabase")
        except Exception as e:
            logger.warning(f"Could not connect to Supabase: {e}")
            logger.info("Running in local mode without database persistence")
    else:
        logger.info("Running in local mode (no Supabase credentials found)")

    # Create orchestrator and run predictions
    orchestrator = PredictionOrchestrator(supabase_client)
    await orchestrator.run_tonight_predictions()


if __name__ == "__main__":
    asyncio.run(main())