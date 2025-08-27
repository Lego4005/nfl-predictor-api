"""
RapidAPI NFL Data Client
Integrates with RapidAPI NFL data endpoints for live game data
"""

import aiohttp
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class RapidAPINFLClient:
    """Client for RapidAPI NFL data endpoints"""
    
    def __init__(self):
        self.api_key = os.getenv("RAPID_API_KEY")
        self.base_url = "https://nfl-api-data.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "nfl-api-data.p.rapidapi.com"
        }
        
    async def get_games_for_week(self, week: int, season: int = 2025) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch NFL games for a specific week
        """
        if not self.api_key:
            logger.warning("RapidAPI key not configured")
            return None
            
        try:
            url = f"{self.base_url}/nfl-games"
            params = {
                "week": week,
                "season": season,
                "type": "regular"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, 
                    headers=self.headers, 
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ RapidAPI NFL: Retrieved {len(data.get('games', []))} games for week {week}")
                        return data.get('games', [])
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ RapidAPI NFL API error {response.status}: {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ RapidAPI NFL client error: {e}")
            return None
    
    async def get_team_stats(self, team_id: str, season: int = 2025) -> Optional[Dict[str, Any]]:
        """
        Fetch team statistics
        """
        if not self.api_key:
            return None
            
        try:
            url = f"{self.base_url}/nfl-team-stats"
            params = {
                "team": team_id,
                "season": season
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, 
                    headers=self.headers, 
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ RapidAPI NFL: Retrieved stats for team {team_id}")
                        return data
                    else:
                        logger.error(f"❌ RapidAPI NFL team stats error {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ RapidAPI NFL team stats error: {e}")
            return None
    
    async def get_player_stats(self, player_id: str, season: int = 2025) -> Optional[Dict[str, Any]]:
        """
        Fetch player statistics for props
        """
        if not self.api_key:
            return None
            
        try:
            url = f"{self.base_url}/nfl-player-stats"
            params = {
                "player": player_id,
                "season": season
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, 
                    headers=self.headers, 
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ RapidAPI NFL: Retrieved stats for player {player_id}")
                        return data
                    else:
                        logger.error(f"❌ RapidAPI NFL player stats error {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ RapidAPI NFL player stats error: {e}")
            return None

    async def health_check(self) -> bool:
        """
        Check if RapidAPI NFL service is available
        """
        if not self.api_key:
            return False
            
        try:
            # Use a simple endpoint to check connectivity
            url = f"{self.base_url}/nfl-games"
            params = {"week": 1, "season": 2025, "type": "regular"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, 
                    headers=self.headers, 
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"RapidAPI NFL health check failed: {e}")
            return False