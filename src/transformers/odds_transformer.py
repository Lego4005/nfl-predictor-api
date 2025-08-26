"""
Transformer for The Odds API responses.
Converts Odds API data to standard format for game predictions, ATS, and totals.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_transformer import (
    BaseTransformer,
    StandardGamePrediction,
    StandardATSPrediction, 
    StandardTotalsPrediction,
    StandardPropBet,
    StandardFantasyPick
)

logger = logging.getLogger(__name__)


class OddsTransformer(BaseTransformer):
    """
    Transformer for The Odds API data.
    Handles game odds, spreads, totals, and moneylines.
    """
    
    def __init__(self):
        super().__init__("odds_api")
    
    def _extract_best_spread(self, bookmakers: List[Dict[str, Any]], team: str) -> Optional[float]:
        """Extract the best spread for a team from bookmakers"""
        spreads = []
        
        for bookmaker in bookmakers:
            markets = bookmaker.get("markets", [])
            for market in markets:
                if market.get("key") == "spreads":
                    outcomes = market.get("outcomes", [])
                    for outcome in outcomes:
                        if self._parse_team_abbreviation(outcome.get("name", "")) == team:
                            point = outcome.get("point")
                            if point is not None:
                                spreads.append(float(point))
        
        return spreads[0] if spreads else None
    
    def _extract_best_total(self, bookmakers: List[Dict[str, Any]]) -> Optional[float]:
        """Extract the best total line from bookmakers"""
        totals = []
        
        for bookmaker in bookmakers:
            markets = bookmaker.get("markets", [])
            for market in markets:
                if market.get("key") == "totals":
                    outcomes = market.get("outcomes", [])
                    for outcome in outcomes:
                        if outcome.get("name") == "Over":
                            point = outcome.get("point")
                            if point is not None:
                                totals.append(float(point))
        
        return totals[0] if totals else None
    
    def _extract_moneylines(self, bookmakers: List[Dict[str, Any]]) -> Dict[str, int]:
        """Extract moneyline odds for both teams"""
        moneylines = {}
        
        for bookmaker in bookmakers:
            markets = bookmaker.get("markets", [])
            for market in markets:
                if market.get("key") == "h2h":
                    outcomes = market.get("outcomes", [])
                    for outcome in outcomes:
                        team = self._parse_team_abbreviation(outcome.get("name", ""))
                        price = outcome.get("price")
                        if team and price is not None:
                            moneylines[team] = int(price)
        
        return moneylines
    
    def _predict_winner_from_moneyline(self, moneylines: Dict[str, int], home: str, away: str) -> str:
        """Predict winner based on moneyline odds"""
        home_ml = moneylines.get(home, 0)
        away_ml = moneylines.get(away, 0)
        
        # Lower (more negative) moneyline = favorite
        if home_ml < away_ml:
            return home
        elif away_ml < home_ml:
            return away
        else:
            return home  # Default to home team if equal
    
    def _calculate_spread_confidence(self, spread: float, moneylines: Dict[str, int]) -> float:
        """Calculate confidence for spread pick based on line and moneylines"""
        base_confidence = 0.55
        
        # Larger spreads generally have higher confidence
        spread_factor = min(abs(spread) * 0.01, 0.1)
        
        # Moneyline differential indicates market confidence
        ml_values = list(moneylines.values())
        if len(ml_values) >= 2:
            ml_diff = abs(ml_values[0] - ml_values[1])
            ml_factor = min(ml_diff * 0.0001, 0.05)
        else:
            ml_factor = 0
        
        return min(base_confidence + spread_factor + ml_factor, 0.85)
    
    def _calculate_total_confidence(self, total: float) -> float:
        """Calculate confidence for totals pick"""
        base_confidence = 0.52
        
        # Higher totals might have slightly more confidence in model
        total_factor = min(total * 0.001, 0.08)
        
        return min(base_confidence + total_factor, 0.75)
    
    def transform_game_predictions(self, raw_data: List[Dict[str, Any]]) -> List[StandardGamePrediction]:
        """Transform Odds API game data to standard game predictions"""
        predictions = []
        
        for game_data in raw_data:
            try:
                if not self._validate_required_fields(game_data, ["home_team", "away_team", "bookmakers"]):
                    continue
                
                home_team = self._parse_team_abbreviation(game_data["home_team"])
                away_team = self._parse_team_abbreviation(game_data["away_team"])
                matchup = self._create_matchup_string(away_team, home_team)
                
                bookmakers = game_data.get("bookmakers", [])
                if not bookmakers:
                    continue
                
                # Extract moneylines to determine favorite
                moneylines = self._extract_moneylines(bookmakers)
                su_pick = self._predict_winner_from_moneyline(moneylines, home_team, away_team)
                
                # Calculate confidence based on moneyline differential
                su_confidence = self._generate_confidence(
                    base_confidence=0.58,
                    moneyline_diff=abs(moneylines.get(home_team, 0) - moneylines.get(away_team, 0))
                )
                
                prediction = StandardGamePrediction(
                    home=home_team,
                    away=away_team,
                    matchup=matchup,
                    su_pick=su_pick,
                    su_confidence=su_confidence,
                    source=self.source_name,
                    timestamp=self.timestamp
                )
                
                predictions.append(prediction)
                
            except Exception as e:
                logger.warning(f"Failed to transform game prediction: {str(e)}")
                continue
        
        logger.info(f"Transformed {len(predictions)} game predictions from {self.source_name}")
        return predictions
    
    def transform_ats_predictions(self, raw_data: List[Dict[str, Any]]) -> List[StandardATSPrediction]:
        """Transform Odds API odds data to standard ATS predictions"""
        predictions = []
        
        for game_data in raw_data:
            try:
                if not self._validate_required_fields(game_data, ["home_team", "away_team", "bookmakers"]):
                    continue
                
                home_team = self._parse_team_abbreviation(game_data["home_team"])
                away_team = self._parse_team_abbreviation(game_data["away_team"])
                matchup = self._create_matchup_string(away_team, home_team)
                
                bookmakers = game_data.get("bookmakers", [])
                if not bookmakers:
                    continue
                
                # Extract spread data
                home_spread = self._extract_best_spread(bookmakers, home_team)
                if home_spread is None:
                    continue
                
                # Determine ATS pick (pick the team getting points or smaller spread)
                if home_spread < 0:  # Home team favored
                    ats_pick = f"{home_team} {home_spread}"
                    spread = home_spread
                else:  # Away team favored or pick'em
                    away_spread = -home_spread if home_spread != 0 else 0
                    ats_pick = f"{away_team} {away_spread}" if away_spread != 0 else f"{away_team} PK"
                    spread = away_spread
                
                # Calculate confidence
                moneylines = self._extract_moneylines(bookmakers)
                ats_confidence = self._calculate_spread_confidence(spread, moneylines)
                
                prediction = StandardATSPrediction(
                    matchup=matchup,
                    ats_pick=ats_pick,
                    spread=spread,
                    ats_confidence=ats_confidence,
                    source=self.source_name,
                    timestamp=self.timestamp
                )
                
                predictions.append(prediction)
                
            except Exception as e:
                logger.warning(f"Failed to transform ATS prediction: {str(e)}")
                continue
        
        logger.info(f"Transformed {len(predictions)} ATS predictions from {self.source_name}")
        return predictions
    
    def transform_totals_predictions(self, raw_data: List[Dict[str, Any]]) -> List[StandardTotalsPrediction]:
        """Transform Odds API odds data to standard totals predictions"""
        predictions = []
        
        for game_data in raw_data:
            try:
                if not self._validate_required_fields(game_data, ["home_team", "away_team", "bookmakers"]):
                    continue
                
                home_team = self._parse_team_abbreviation(game_data["home_team"])
                away_team = self._parse_team_abbreviation(game_data["away_team"])
                matchup = self._create_matchup_string(away_team, home_team)
                
                bookmakers = game_data.get("bookmakers", [])
                if not bookmakers:
                    continue
                
                # Extract total line
                total_line = self._extract_best_total(bookmakers)
                if total_line is None:
                    continue
                
                # Simple prediction logic (in production, use ML models)
                # For now, slightly favor Over for higher scoring games
                if total_line > 47:
                    tot_pick = f"Over {total_line}"
                else:
                    tot_pick = f"Under {total_line}"
                
                tot_confidence = self._calculate_total_confidence(total_line)
                
                prediction = StandardTotalsPrediction(
                    matchup=matchup,
                    tot_pick=tot_pick,
                    total_line=total_line,
                    tot_confidence=tot_confidence,
                    source=self.source_name,
                    timestamp=self.timestamp
                )
                
                predictions.append(prediction)
                
            except Exception as e:
                logger.warning(f"Failed to transform totals prediction: {str(e)}")
                continue
        
        logger.info(f"Transformed {len(predictions)} totals predictions from {self.source_name}")
        return predictions
    
    def transform_prop_bets(self, raw_data: List[Dict[str, Any]]) -> List[StandardPropBet]:
        """
        Transform Odds API data to prop bets.
        Note: The Odds API doesn't typically provide player props,
        so this returns empty list. Use SportsDataIO for props.
        """
        logger.info("The Odds API doesn't provide player props - use SportsDataIO instead")
        return []
    
    def transform_fantasy_picks(self, raw_data: List[Dict[str, Any]]) -> List[StandardFantasyPick]:
        """
        Transform Odds API data to fantasy picks.
        Note: The Odds API doesn't provide fantasy data,
        so this returns empty list. Use SportsDataIO for fantasy.
        """
        logger.info("The Odds API doesn't provide fantasy data - use SportsDataIO instead")
        return []