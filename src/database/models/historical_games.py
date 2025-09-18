"""
SQLAlchemy models for historical NFL game data storage.
Optimized for ML model training with proper indexing and relationships.
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, JSON,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Any

Base = declarative_base()

class HistoricalGame(Base):
    """
    Main games table storing core game information.
    One record per NFL game with scores, dates, teams, and weather.
    """
    __tablename__ = 'historical_games'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    game_key = Column(String(50), unique=True, nullable=False, index=True)

    # Basic game info
    season = Column(Integer, nullable=False, index=True)
    season_type = Column(String(20), nullable=False)  # Regular, Postseason
    week = Column(Integer, nullable=True, index=True)
    game_date = Column(DateTime, nullable=False, index=True)

    # Teams
    home_team = Column(String(10), nullable=False, index=True)
    away_team = Column(String(10), nullable=False, index=True)

    # Scores
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    home_score_quarter1 = Column(Integer, nullable=True)
    home_score_quarter2 = Column(Integer, nullable=True)
    home_score_quarter3 = Column(Integer, nullable=True)
    home_score_quarter4 = Column(Integer, nullable=True)
    home_score_overtime = Column(Integer, nullable=True)
    away_score_quarter1 = Column(Integer, nullable=True)
    away_score_quarter2 = Column(Integer, nullable=True)
    away_score_quarter3 = Column(Integer, nullable=True)
    away_score_quarter4 = Column(Integer, nullable=True)
    away_score_overtime = Column(Integer, nullable=True)

    # Game status
    is_final = Column(Boolean, default=False)
    is_overtime = Column(Boolean, default=False)

    # Stadium and conditions
    stadium_name = Column(String(100), nullable=True)
    stadium_city = Column(String(50), nullable=True)
    stadium_state = Column(String(5), nullable=True)
    playing_surface = Column(String(20), nullable=True)  # Grass, Turf, etc.
    is_dome = Column(Boolean, default=False)

    # Weather data
    temperature = Column(Float, nullable=True)  # Fahrenheit
    humidity = Column(Float, nullable=True)  # Percentage
    wind_speed = Column(Float, nullable=True)  # MPH
    wind_direction = Column(String(10), nullable=True)  # N, S, E, W, etc.
    weather_conditions = Column(String(50), nullable=True)  # Clear, Rain, Snow, etc.

    # Betting data (if available)
    point_spread = Column(Float, nullable=True)  # Negative = home favorite
    over_under = Column(Float, nullable=True)
    home_moneyline = Column(Integer, nullable=True)
    away_moneyline = Column(Integer, nullable=True)

    # Derived metrics for ML
    total_points = Column(Integer, nullable=True)
    point_differential = Column(Integer, nullable=True)  # home_score - away_score
    is_upset = Column(Boolean, nullable=True)  # underdog won
    game_pace = Column(Float, nullable=True)  # Total plays per minute
    is_high_scoring = Column(Boolean, nullable=True)  # Above average total points

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    team_stats = relationship("TeamStats", back_populates="game", cascade="all, delete-orphan")
    player_stats = relationship("PlayerStats", back_populates="game", cascade="all, delete-orphan")
    betting_data = relationship("BettingData", back_populates="game", cascade="all, delete-orphan")
    injuries = relationship("Injury", back_populates="game", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        Index('idx_season_week', 'season', 'week'),
        Index('idx_game_date', 'game_date'),
        Index('idx_teams', 'home_team', 'away_team'),
        CheckConstraint('home_score >= 0', name='check_home_score_positive'),
        CheckConstraint('away_score >= 0', name='check_away_score_positive'),
        CheckConstraint('season >= 2000', name='check_season_realistic'),
    )

    def __repr__(self):
        return f"<Game({self.game_key}: {self.away_team} @ {self.home_team}, {self.game_date})>"

class TeamStats(Base):
    """
    Team statistics per game for offensive/defensive metrics.
    Two records per game (home and away team stats).
    """
    __tablename__ = 'team_stats'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    game_id = Column(Integer, ForeignKey('historical_games.id'), nullable=False, index=True)
    game_key = Column(String(50), nullable=False, index=True)

    # Team info
    team = Column(String(10), nullable=False, index=True)
    is_home = Column(Boolean, nullable=False)
    opponent = Column(String(10), nullable=False)

    # Basic offensive stats
    points = Column(Integer, nullable=True)
    first_downs = Column(Integer, nullable=True)
    total_yards = Column(Integer, nullable=True)
    passing_yards = Column(Integer, nullable=True)
    rushing_yards = Column(Integer, nullable=True)
    penalties = Column(Integer, nullable=True)
    penalty_yards = Column(Integer, nullable=True)
    turnovers = Column(Integer, nullable=True)
    fumbles_lost = Column(Integer, nullable=True)
    interceptions_thrown = Column(Integer, nullable=True)

    # Passing stats
    completions = Column(Integer, nullable=True)
    passing_attempts = Column(Integer, nullable=True)
    passing_touchdowns = Column(Integer, nullable=True)
    qb_rating = Column(Float, nullable=True)
    sacks_allowed = Column(Integer, nullable=True)
    sack_yards_lost = Column(Integer, nullable=True)

    # Rushing stats
    rushing_attempts = Column(Integer, nullable=True)
    rushing_touchdowns = Column(Integer, nullable=True)
    rushing_yards_per_attempt = Column(Float, nullable=True)

    # Red zone efficiency
    red_zone_attempts = Column(Integer, nullable=True)
    red_zone_scores = Column(Integer, nullable=True)
    red_zone_efficiency = Column(Float, nullable=True)  # Calculated percentage

    # Third down efficiency
    third_down_attempts = Column(Integer, nullable=True)
    third_down_conversions = Column(Integer, nullable=True)
    third_down_efficiency = Column(Float, nullable=True)  # Calculated percentage

    # Time of possession
    time_of_possession_seconds = Column(Integer, nullable=True)
    time_of_possession_percentage = Column(Float, nullable=True)

    # Advanced metrics for ML
    yards_per_play = Column(Float, nullable=True)
    plays_per_drive = Column(Float, nullable=True)
    points_per_drive = Column(Float, nullable=True)
    turnover_margin = Column(Integer, nullable=True)  # Turnovers forced - turnovers committed
    explosive_plays = Column(Integer, nullable=True)  # Plays >= 20 yards
    three_and_outs = Column(Integer, nullable=True)

    # Expected Points Added (EPA) - calculated
    total_epa = Column(Float, nullable=True)
    passing_epa = Column(Float, nullable=True)
    rushing_epa = Column(Float, nullable=True)
    epa_per_play = Column(Float, nullable=True)

    # Success rate - calculated
    success_rate = Column(Float, nullable=True)  # Percentage of successful plays
    passing_success_rate = Column(Float, nullable=True)
    rushing_success_rate = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now())

    # Relationships
    game = relationship("HistoricalGame", back_populates="team_stats")

    # Constraints
    __table_args__ = (
        Index('idx_team_stats_game_team', 'game_id', 'team'),
        Index('idx_team_stats_season', 'game_key', 'team'),
        UniqueConstraint('game_id', 'team', name='unique_game_team_stats'),
        CheckConstraint('points >= 0', name='check_points_positive'),
        CheckConstraint('total_yards >= 0', name='check_total_yards_positive'),
    )

    def __repr__(self):
        return f"<TeamStats({self.team} in {self.game_key}: {self.points} pts, {self.total_yards} yds)>"

class PlayerStats(Base):
    """
    Individual player performance statistics per game.
    Multiple records per game for key players.
    """
    __tablename__ = 'player_stats'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    game_id = Column(Integer, ForeignKey('historical_games.id'), nullable=False, index=True)
    game_key = Column(String(50), nullable=False, index=True)

    # Player info
    player_id = Column(String(20), nullable=False, index=True)
    player_name = Column(String(100), nullable=False)
    team = Column(String(10), nullable=False, index=True)
    position = Column(String(10), nullable=False, index=True)
    jersey_number = Column(Integer, nullable=True)

    # Passing stats
    passing_attempts = Column(Integer, nullable=True)
    passing_completions = Column(Integer, nullable=True)
    passing_yards = Column(Integer, nullable=True)
    passing_touchdowns = Column(Integer, nullable=True)
    interceptions = Column(Integer, nullable=True)
    qb_rating = Column(Float, nullable=True)
    longest_pass = Column(Integer, nullable=True)
    times_sacked = Column(Integer, nullable=True)
    sack_yards = Column(Integer, nullable=True)

    # Rushing stats
    rushing_attempts = Column(Integer, nullable=True)
    rushing_yards = Column(Integer, nullable=True)
    rushing_touchdowns = Column(Integer, nullable=True)
    longest_rush = Column(Integer, nullable=True)
    fumbles = Column(Integer, nullable=True)
    fumbles_lost = Column(Integer, nullable=True)

    # Receiving stats
    receptions = Column(Integer, nullable=True)
    receiving_yards = Column(Integer, nullable=True)
    receiving_touchdowns = Column(Integer, nullable=True)
    targets = Column(Integer, nullable=True)
    longest_reception = Column(Integer, nullable=True)

    # Kicking stats
    field_goals_made = Column(Integer, nullable=True)
    field_goals_attempted = Column(Integer, nullable=True)
    field_goal_percentage = Column(Float, nullable=True)
    longest_field_goal = Column(Integer, nullable=True)
    extra_points_made = Column(Integer, nullable=True)
    extra_points_attempted = Column(Integer, nullable=True)

    # Defensive stats
    tackles = Column(Integer, nullable=True)
    solo_tackles = Column(Integer, nullable=True)
    assisted_tackles = Column(Integer, nullable=True)
    sacks = Column(Float, nullable=True)  # Can be fractional
    quarterback_hits = Column(Integer, nullable=True)
    tackles_for_loss = Column(Integer, nullable=True)
    interceptions_defense = Column(Integer, nullable=True)
    passes_defended = Column(Integer, nullable=True)
    fumbles_forced = Column(Integer, nullable=True)
    fumbles_recovered = Column(Integer, nullable=True)
    defensive_touchdowns = Column(Integer, nullable=True)

    # Special teams
    punt_returns = Column(Integer, nullable=True)
    punt_return_yards = Column(Integer, nullable=True)
    punt_return_touchdowns = Column(Integer, nullable=True)
    kick_returns = Column(Integer, nullable=True)
    kick_return_yards = Column(Integer, nullable=True)
    kick_return_touchdowns = Column(Integer, nullable=True)

    # Fantasy points (useful for some ML models)
    fantasy_points = Column(Float, nullable=True)
    fantasy_points_ppr = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now())

    # Relationships
    game = relationship("HistoricalGame", back_populates="player_stats")

    # Constraints
    __table_args__ = (
        Index('idx_player_stats_game_player', 'game_id', 'player_id'),
        Index('idx_player_stats_position', 'position', 'game_key'),
        Index('idx_player_stats_team', 'team', 'game_key'),
    )

    def __repr__(self):
        return f"<PlayerStats({self.player_name} ({self.position}) in {self.game_key})>"

class BettingData(Base):
    """
    Historical betting lines, spreads, totals, and outcomes.
    Multiple records per game for different sportsbooks and line movements.
    """
    __tablename__ = 'betting_data'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    game_id = Column(Integer, ForeignKey('historical_games.id'), nullable=False, index=True)
    game_key = Column(String(50), nullable=False, index=True)

    # Sportsbook info
    sportsbook = Column(String(50), nullable=True)  # DraftKings, FanDuel, etc.
    line_type = Column(String(20), nullable=False)  # Opening, Closing, Live

    # Point spread
    point_spread_home = Column(Float, nullable=True)  # Negative if home favorite
    point_spread_away = Column(Float, nullable=True)  # Positive if home favorite
    spread_juice_home = Column(Integer, nullable=True)  # -110, etc.
    spread_juice_away = Column(Integer, nullable=True)

    # Over/Under (Total)
    over_under = Column(Float, nullable=True)
    over_juice = Column(Integer, nullable=True)
    under_juice = Column(Integer, nullable=True)

    # Moneyline
    moneyline_home = Column(Integer, nullable=True)
    moneyline_away = Column(Integer, nullable=True)

    # Line movement tracking
    line_timestamp = Column(DateTime, nullable=True)
    minutes_before_kickoff = Column(Integer, nullable=True)

    # Outcome tracking
    spread_result = Column(String(10), nullable=True)  # Home_Cover, Away_Cover, Push
    total_result = Column(String(10), nullable=True)  # Over, Under, Push
    moneyline_result = Column(String(10), nullable=True)  # Home_Win, Away_Win

    # Market efficiency metrics
    closing_line_value = Column(Float, nullable=True)  # Difference from opening
    reverse_line_movement = Column(Boolean, nullable=True)  # Line moved opposite to public betting
    sharp_money_indicator = Column(Boolean, nullable=True)  # Professional betting detected

    # Timestamps
    created_at = Column(DateTime, default=func.now())

    # Relationships
    game = relationship("HistoricalGame", back_populates="betting_data")

    # Constraints
    __table_args__ = (
        Index('idx_betting_game_sportsbook', 'game_id', 'sportsbook'),
        Index('idx_betting_line_type', 'line_type', 'game_key'),
    )

    def __repr__(self):
        return f"<BettingData({self.game_key}: Spread {self.point_spread_home}, O/U {self.over_under})>"

class Injury(Base):
    """
    Historical injury reports affecting game outcomes.
    Multiple records per game for different players and injury statuses.
    """
    __tablename__ = 'injuries'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    game_id = Column(Integer, ForeignKey('historical_games.id'), nullable=False, index=True)
    game_key = Column(String(50), nullable=False, index=True)

    # Player info
    player_id = Column(String(20), nullable=False, index=True)
    player_name = Column(String(100), nullable=False)
    team = Column(String(10), nullable=False, index=True)
    position = Column(String(10), nullable=False, index=True)
    jersey_number = Column(Integer, nullable=True)

    # Injury details
    injury_status = Column(String(20), nullable=False)  # Out, Doubtful, Questionable, Probable
    injury_type = Column(String(50), nullable=True)  # Knee, Ankle, Concussion, etc.
    injury_body_part = Column(String(30), nullable=True)  # More specific location
    injury_description = Column(Text, nullable=True)  # Full description

    # Timeline
    injury_date = Column(DateTime, nullable=True)  # When injury occurred
    days_since_injury = Column(Integer, nullable=True)  # Days between injury and game
    report_date = Column(DateTime, nullable=False)  # When status was reported
    final_game_status = Column(String(20), nullable=True)  # Did Not Play, Limited, Full

    # Impact metrics
    is_key_player = Column(Boolean, default=False)  # Starter or significant contributor
    games_missed = Column(Integer, nullable=True)  # Total games missed due to injury
    player_importance_score = Column(Float, nullable=True)  # 0-1 scale of player importance
    replacement_player = Column(String(100), nullable=True)  # Who replaced them

    # Fantasy/betting impact
    pre_injury_snap_percentage = Column(Float, nullable=True)  # % of snaps before injury
    projected_snap_percentage = Column(Float, nullable=True)  # Expected % with injury
    line_movement_impact = Column(Float, nullable=True)  # How much betting lines moved

    # Timestamps
    created_at = Column(DateTime, default=func.now())

    # Relationships
    game = relationship("HistoricalGame", back_populates="injuries")

    # Constraints
    __table_args__ = (
        Index('idx_injury_game_player', 'game_id', 'player_id'),
        Index('idx_injury_status_position', 'injury_status', 'position'),
        Index('idx_injury_team_game', 'team', 'game_key'),
    )

    def __repr__(self):
        return f"<Injury({self.player_name} ({self.position}) - {self.injury_status} for {self.game_key})>"

# Database utility functions
def create_all_tables(engine):
    """Create all tables in the database"""
    Base.metadata.create_all(engine)

def drop_all_tables(engine):
    """Drop all tables in the database (use with caution!)"""
    Base.metadata.drop_all(engine)

def get_performance_indexes():
    """Get list of additional indexes for performance optimization"""
    return [
        # Game queries
        "CREATE INDEX IF NOT EXISTS idx_games_season_week_teams ON historical_games(season, week, home_team, away_team);",
        "CREATE INDEX IF NOT EXISTS idx_games_date_range ON historical_games(game_date) WHERE is_final = true;",

        # Team stats queries
        "CREATE INDEX IF NOT EXISTS idx_team_stats_advanced ON team_stats(team, total_epa, success_rate);",
        "CREATE INDEX IF NOT EXISTS idx_team_stats_efficiency ON team_stats(red_zone_efficiency, third_down_efficiency);",

        # Player stats queries
        "CREATE INDEX IF NOT EXISTS idx_player_stats_qb ON player_stats(position, qb_rating, passing_yards) WHERE position = 'QB';",
        "CREATE INDEX IF NOT EXISTS idx_player_stats_skill ON player_stats(position, fantasy_points) WHERE position IN ('RB', 'WR', 'TE');",

        # Betting queries
        "CREATE INDEX IF NOT EXISTS idx_betting_closing_lines ON betting_data(line_type, point_spread_home, over_under) WHERE line_type = 'Closing';",

        # Injury impact queries
        "CREATE INDEX IF NOT EXISTS idx_injuries_key_players ON injuries(is_key_player, injury_status, position) WHERE is_key_player = true;",
    ]