"""
Simplified database models compatible with SQLite and PostgreSQL
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, DECIMAL, 
    ForeignKey, Index, UniqueConstraint, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class User(Base):
    """Core user model for authentication and profile management"""
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True)  # UUID as string
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    email_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

class UserSession(Base):
    """User session management for JWT tokens"""
    __tablename__ = 'user_sessions'
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token_hash = Column(String(255), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")

class SubscriptionTier(Base):
    """Subscription tier definitions"""
    __tablename__ = 'subscription_tiers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    price_cents = Column(Integer, nullable=False)
    duration_days = Column(Integer)
    features = Column(JSON, nullable=False, default=list)
    is_active = Column(Boolean, default=True)
    is_admin_granted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="tier")

class Subscription(Base):
    """User subscriptions"""
    __tablename__ = 'subscriptions'
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    tier_id = Column(Integer, ForeignKey('subscription_tiers.id'), nullable=False)
    status = Column(String(20), nullable=False, default='active')
    starts_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime)
    stripe_subscription_id = Column(String(255), index=True)
    stripe_customer_id = Column(String(255), index=True)
    auto_renew = Column(Boolean, default=True)
    amount_paid_cents = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    tier = relationship("SubscriptionTier", back_populates="subscriptions")

class AdminUser(Base):
    """Admin users with role-based permissions"""
    __tablename__ = 'admin_users'
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    role = Column(String(50), nullable=False, default='admin')
    permissions = Column(JSON, nullable=False, default=list)
    created_by = Column(String(36), ForeignKey('admin_users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_admin_login = Column(DateTime)
    is_active = Column(Boolean, default=True)

class Affiliate(Base):
    """Affiliate program participants"""
    __tablename__ = 'affiliates'
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    referral_code = Column(String(20), unique=True, nullable=False, index=True)
    commission_rate = Column(DECIMAL(5, 4), default=0.30)
    tier = Column(String(20), default='bronze')
    total_referrals = Column(Integer, default=0)
    total_earnings_cents = Column(Integer, default=0)
    pending_earnings_cents = Column(Integer, default=0)
    paid_earnings_cents = Column(Integer, default=0)
    payout_method = Column(String(50))
    payout_details = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Prediction(Base):
    """Prediction tracking for accuracy metrics"""
    __tablename__ = 'predictions'
    
    id = Column(String(36), primary_key=True)
    week = Column(Integer, nullable=False)
    season = Column(Integer, nullable=False)
    prediction_type = Column(String(20), nullable=False)
    home_team = Column(String(10))
    away_team = Column(String(10))
    matchup = Column(String(100))
    prediction_data = Column(JSON, nullable=False)
    confidence = Column(DECIMAL(5, 4))
    actual_result = Column(JSON)
    is_correct = Column(Boolean)
    created_at = Column(DateTime, default=datetime.utcnow)
    result_updated_at = Column(DateTime)