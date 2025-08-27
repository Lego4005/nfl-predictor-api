"""
Enhanced prediction tracking and accuracy models
Extends the base models with comprehensive accuracy tracking
"""

import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, DECIMAL, 
    ForeignKey, Index, UniqueConstraint, Text, JSONB
)
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..database.models import Base

class PredictionResult(Base):
    """Stores actual game results for accuracy calculation"""
    __tablename__ = 'prediction_results'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id = Column(String(50), nullable=False, unique=True)
    week = Column(Integer, nullable=False)
    season = Column(Integer, nullable=False)
    home_team = Column(String(10), nullable=False)
    away_team = Column(String(10), nullable=False)
    
    # Game results
    home_score = Column(Integer)
    away_score = Column(Integer)
    game_status = Column(String(20), default='scheduled')  # 'scheduled', 'in_progress', 'final', 'postponed'
    
    # Betting lines (for ATS and totals accuracy)
    spread_line = Column(DECIMAL(4, 1))  # Home team spread
    total_line = Column(DECIMAL(5, 1))   # Over/under total
    
    # Calculated results
    winner = Column(String(10))  # 'home', 'away', 'tie'
    ats_winner = Column(String(10))  # 'home', 'away', 'push'
    total_result = Column(String(10))  # 'over', 'under', 'push'
    
    # Metadata
    game_date = Column(DateTime(timezone=True))
    result_source = Column(String(50))  # 'espn', 'nfl_api', 'manual'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    prediction_matches = relationship("PredictionMatch", back_populates="result")
    
    # Indexes
    __table_args__ = (
        Index('idx_prediction_results_week_season', 'week', 'season'),
        Index('idx_prediction_results_game_date', 'game_date'),
        Index('idx_prediction_results_status', 'game_status'),
    )c
lass PredictionMatch(Base):
    """Links predictions to actual results for accuracy calculation"""
    __tablename__ = 'prediction_matches'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey('predictions.id', ondelete='CASCADE'), nullable=False)
    result_id = Column(UUID(as_uuid=True), ForeignKey('prediction_results.id', ondelete='CASCADE'), nullable=False)
    
    # Accuracy calculation
    is_correct = Column(Boolean)
    confidence_score = Column(DECIMAL(5, 4))
    prediction_value = Column(String(50))  # The actual prediction made
    actual_value = Column(String(50))      # The actual result
    
    # ROI calculation (theoretical betting returns)
    theoretical_bet_amount = Column(DECIMAL(10, 2), default=100.00)  # $100 standard bet
    theoretical_payout = Column(DECIMAL(10, 2))
    roi_percentage = Column(DECIMAL(6, 3))
    
    # Metadata
    matched_at = Column(DateTime(timezone=True), server_default=func.now())
    accuracy_calculated_at = Column(DateTime(timezone=True))
    
    # Relationships
    result = relationship("PredictionResult", back_populates="prediction_matches")
    
    # Indexes
    __table_args__ = (
        Index('idx_prediction_matches_prediction_id', 'prediction_id'),
        Index('idx_prediction_matches_result_id', 'result_id'),
        UniqueConstraint('prediction_id', 'result_id', name='uq_prediction_result_match'),
    )

class PerformanceHistory(Base):
    """Historical performance tracking with trend analysis"""
    __tablename__ = 'performance_history'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Time period
    period_type = Column(String(20), nullable=False)  # 'daily', 'weekly', 'monthly', 'season'
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    week = Column(Integer)
    season = Column(Integer, nullable=False)
    
    # Prediction type breakdown
    prediction_type = Column(String(20), nullable=False)  # 'game', 'ats', 'total', 'prop'
    
    # Performance metrics
    total_predictions = Column(Integer, nullable=False, default=0)
    correct_predictions = Column(Integer, nullable=False, default=0)
    accuracy_percentage = Column(DECIMAL(5, 2), nullable=False)
    confidence_weighted_accuracy = Column(DECIMAL(5, 2))
    
    # Advanced metrics
    high_confidence_accuracy = Column(DECIMAL(5, 2))  # Accuracy for predictions > 70% confidence
    medium_confidence_accuracy = Column(DECIMAL(5, 2))  # Accuracy for 50-70% confidence
    low_confidence_accuracy = Column(DECIMAL(5, 2))   # Accuracy for < 50% confidence
    
    # ROI metrics
    total_theoretical_bets = Column(DECIMAL(12, 2), default=0.00)
    total_theoretical_returns = Column(DECIMAL(12, 2), default=0.00)
    roi_percentage = Column(DECIMAL(6, 3), default=0.000)
    best_bet_roi = Column(DECIMAL(6, 3))  # ROI of highest confidence bets
    
    # Streak tracking
    current_streak = Column(Integer, default=0)  # Positive for wins, negative for losses
    longest_win_streak = Column(Integer, default=0)
    longest_loss_streak = Column(Integer, default=0)
    
    # Trend analysis
    trend_direction = Column(String(20))  # 'improving', 'declining', 'stable'
    momentum_score = Column(DECIMAL(5, 2))  # -100 to +100 momentum indicator
    
    # Metadata
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_performance_history_period', 'period_type', 'period_start', 'period_end'),
        Index('idx_performance_history_season_week', 'season', 'week'),
        Index('idx_performance_history_type', 'prediction_type'),
        UniqueConstraint('period_type', 'period_start', 'prediction_type', name='uq_performance_period'),
    )class 
AccuracySnapshot(Base):
    """Real-time accuracy snapshots for dashboard display"""
    __tablename__ = 'accuracy_snapshots'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Snapshot metadata
    snapshot_type = Column(String(20), nullable=False)  # 'live', 'weekly', 'monthly', 'season'
    snapshot_date = Column(DateTime(timezone=True), nullable=False)
    
    # Overall metrics
    overall_accuracy = Column(DECIMAL(5, 2), nullable=False)
    total_predictions = Column(Integer, nullable=False)
    correct_predictions = Column(Integer, nullable=False)
    
    # Breakdown by prediction type
    game_accuracy = Column(DECIMAL(5, 2))
    ats_accuracy = Column(DECIMAL(5, 2))
    total_accuracy = Column(DECIMAL(5, 2))
    prop_accuracy = Column(DECIMAL(5, 2))
    
    # Confidence-weighted metrics
    confidence_weighted_overall = Column(DECIMAL(5, 2))
    high_confidence_count = Column(Integer, default=0)
    high_confidence_accuracy = Column(DECIMAL(5, 2))
    
    # ROI metrics
    theoretical_roi = Column(DECIMAL(6, 3))
    total_units_bet = Column(DECIMAL(10, 2))
    total_units_won = Column(DECIMAL(10, 2))
    
    # Recent performance (last 10 predictions)
    recent_accuracy = Column(DECIMAL(5, 2))
    recent_streak = Column(Integer)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_accuracy_snapshots_type_date', 'snapshot_type', 'snapshot_date'),
        Index('idx_accuracy_snapshots_date', 'snapshot_date'),
    )

class PredictionFeedback(Base):
    """User feedback on prediction accuracy and quality"""
    __tablename__ = 'prediction_feedback'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey('predictions.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # Feedback metrics
    usefulness_rating = Column(Integer)  # 1-5 scale
    confidence_rating = Column(Integer)  # 1-5 scale (how confident user felt about prediction)
    outcome_satisfaction = Column(Integer)  # 1-5 scale (satisfaction with result)
    
    # Feedback text
    comments = Column(Text)
    feedback_type = Column(String(20))  # 'positive', 'negative', 'neutral', 'suggestion'
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_prediction_feedback_prediction_id', 'prediction_id'),
        Index('idx_prediction_feedback_user_id', 'user_id'),
        Index('idx_prediction_feedback_type', 'feedback_type'),
    )

class AccuracyAlert(Base):
    """Alerts for significant accuracy changes or milestones"""
    __tablename__ = 'accuracy_alerts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Alert details
    alert_type = Column(String(30), nullable=False)  # 'accuracy_drop', 'accuracy_milestone', 'streak_broken', 'roi_threshold'
    severity = Column(String(20), nullable=False)    # 'info', 'warning', 'critical'
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Trigger data
    trigger_value = Column(DECIMAL(10, 3))
    threshold_value = Column(DECIMAL(10, 3))
    prediction_type = Column(String(20))
    
    # Status
    is_active = Column(Boolean, default=True)
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_accuracy_alerts_type', 'alert_type'),
        Index('idx_accuracy_alerts_severity', 'severity'),
        Index('idx_accuracy_alerts_active', 'is_active'),
    )