"""
Base transformer class for normalizing API responses to standard format.
Provides common functionality for all data source transformers.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class StandardGamePrediction:
    """Standard format for game predictions"""
    home: str
    away: str
    matchup: str
    su_pick: str
    su_confidence: float
    source: str
    timestamp: str


@dataclass
class StandardATSPrediction:
    """Standard format for ATS predictions"""
    matchup: str
    ats_pick: str
    spread: float
    ats_confidence: float
    source: str
    timestamp: str


@dataclass
class StandardTotalsPrediction:
    """Standard format for totals predictions"""
    matchup: str
    tot_pick: str
    total_line: float
    tot_confidence: float
    source: str
    timestamp: str


@dataclass
class StandardPropBet:
    """Standard format for prop bets"""
    player: str
    prop_type: str
    units: str
    line: float
    pick: str
    confidence: float
    bookmaker: str
    team: str
    opponent: str
    source: str
    timestamp: str


@dataclass
class StandardFantasyPick:
    """Standard format for fantasy picks"""
    player: str
    position: str
    salary: int
    projected_points: float
    value_score: float
    source: str
    timestamp: str


class BaseTransformer(ABC):
    """
    Abstract base class for data transformers.
    Provides common functionality and interface for all transformers.
    """
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.timestamp = datetime.utcnow().isoformat()
    
    def _generate_confidence(self, base_confidence: float = 0.55, **factors) -> float:
        """
        Generate confidence score based on various factors.
        This is a simplified model - in production, use ML models.
        """
        confidence = base_confidence
        
        # Apply various factors to adjust confidence
        for factor_name, factor_value in factors.items():
            if factor_name == "line_movement" and factor_value:
                confidence += min(abs(factor_value) * 0.01, 0.1)
            elif factor_name == "volume" and factor_value:
                confidence += min(factor_value * 0.001, 0.05)
            elif factor_name == "consensus" and factor_value:
                confidence += min(factor_value * 0.1, 0.15)
        
        # Ensure confidence stays within reasonable bounds
        return min(max(confidence, 0.5), 0.95)
    
    def _parse_team_abbreviation(self, team: str) -> str:
        """Standardize team abbreviations across all sources"""
        if not team:
            return ""
        
        # Handle common variations
        team_mapping = {
            # Handle full names to abbreviations
            "Buffalo Bills": "BUF",
            "Miami Dolphins": "MIA",
            "New England Patriots": "NE", 
            "New York Jets": "NYJ",
            "Baltimore Ravens": "BAL",
            "Cincinnati Bengals": "CIN",
            "Cleveland Browns": "CLE",
            "Pittsburgh Steelers": "PIT",
            "Houston Texans": "HOU",
            "Indianapolis Colts": "IND",
            "Jacksonville Jaguars": "JAX",
            "Tennessee Titans": "TEN",
            "Denver Broncos": "DEN",
            "Kansas City Chiefs": "KC",
            "Las Vegas Raiders": "LV",
            "Los Angeles Chargers": "LAC",
            "Dallas Cowboys": "DAL",
            "New York Giants": "NYG",
            "Philadelphia Eagles": "PHI",
            "Washington Commanders": "WAS",
            "Chicago Bears": "CHI",
            "Detroit Lions": "DET",
            "Green Bay Packers": "GB",
            "Minnesota Vikings": "MIN",
            "Atlanta Falcons": "ATL",
            "Carolina Panthers": "CAR",
            "New Orleans Saints": "NO",
            "Tampa Bay Buccaneers": "TB",
            "Arizona Cardinals": "ARI",
            "Los Angeles Rams": "LAR",
            "San Francisco 49ers": "SF",
            "Seattle Seahawks": "SEA",
            
            # Handle common abbreviation variations
            "NWE": "NE",
            "GNB": "GB",
            "KAN": "KC",
            "LVR": "LV",
            "LAR": "LAR",
            "SFO": "SF",
            "TAM": "TB",
            "NOR": "NO"
        }
        
        return team_mapping.get(team, team.upper())
    
    def _create_matchup_string(self, away_team: str, home_team: str) -> str:
        """Create standardized matchup string"""
        away = self._parse_team_abbreviation(away_team)
        home = self._parse_team_abbreviation(home_team)
        return f"{away} @ {home}"
    
    def _validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Validate that required fields are present in data"""
        for field in required_fields:
            if field not in data or data[field] is None:
                logger.warning(f"Missing required field '{field}' in {self.source_name} data")
                return False
        return True
    
    def _safe_float_conversion(self, value: Any, default: float = 0.0) -> float:
        """Safely convert value to float with fallback"""
        try:
            if value is None:
                return default
            return float(value)
        except (ValueError, TypeError):
            logger.warning(f"Failed to convert '{value}' to float, using default {default}")
            return default
    
    def _safe_int_conversion(self, value: Any, default: int = 0) -> int:
        """Safely convert value to int with fallback"""
        try:
            if value is None:
                return default
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"Failed to convert '{value}' to int, using default {default}")
            return default
    
    @abstractmethod
    def transform_game_predictions(self, raw_data: List[Dict[str, Any]]) -> List[StandardGamePrediction]:
        """Transform raw game data to standard game predictions format"""
        pass
    
    @abstractmethod
    def transform_ats_predictions(self, raw_data: List[Dict[str, Any]]) -> List[StandardATSPrediction]:
        """Transform raw odds data to standard ATS predictions format"""
        pass
    
    @abstractmethod
    def transform_totals_predictions(self, raw_data: List[Dict[str, Any]]) -> List[StandardTotalsPrediction]:
        """Transform raw odds data to standard totals predictions format"""
        pass
    
    @abstractmethod
    def transform_prop_bets(self, raw_data: List[Dict[str, Any]]) -> List[StandardPropBet]:
        """Transform raw prop data to standard prop bets format"""
        pass
    
    @abstractmethod
    def transform_fantasy_picks(self, raw_data: List[Dict[str, Any]]) -> List[StandardFantasyPick]:
        """Transform raw fantasy data to standard fantasy picks format"""
        pass
    
    def get_transformer_info(self) -> Dict[str, Any]:
        """Get information about this transformer"""
        return {
            "source": self.source_name,
            "timestamp": self.timestamp,
            "supported_formats": [
                "game_predictions",
                "ats_predictions", 
                "totals_predictions",
                "prop_bets",
                "fantasy_picks"
            ]
        }